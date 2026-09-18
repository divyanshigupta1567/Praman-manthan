// api.js
// Single source of truth for talking to the Praman backend.
// Field names in every response are used as-is (snake_case) — never renamed
// or remapped on the way into React state. See SCHEMA_NOTES.md for the
// locked contract these responses are expected to match.

// Set VITE_API_BASE_URL in your .env if the API isn't same-origin.
// Falls back to '' so paths like '/api/incidents' hit the current origin.
const BASE_URL =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_BASE_URL) ||
  "";

class ApiError extends Error {
  constructor(message, status, endpoint) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.endpoint = endpoint;
  }
}

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  let res;
  try {
    res = await fetch(url, {
      headers: { Accept: "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch (networkErr) {
    throw new ApiError(
      `Couldn't reach ${path}. Check your connection or the API server.`,
      0,
      path
    );
  }

  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body?.message || body?.error || "";
    } catch {
      /* body wasn't JSON — ignore */
    }
    throw new ApiError(
      detail || `Request to ${path} failed (${res.status})`,
      res.status,
      path
    );
  }

  // Some endpoints (e.g. a successful DELETE) may return no body.
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// ---------------------------------------------------------------------------
// Mock mode — set to false when a real backend is available.
// ---------------------------------------------------------------------------
const USE_MOCK = true;

import {
  mockComplaints,
  mockIncidents,
  mockHotspots,
  mockMetrics,
  mockTrends,
  mockBriefing,
  mockModelMetrics,
} from "./mockData";

// Simulate a short network round-trip so loading states are visible.
function mockDelay(data) {
  return new Promise((resolve) => setTimeout(() => resolve(data), 400));
}

// ---------------------------------------------------------------------------
// Live-mode drift simulator (mock mode only).
// A real backend naturally changes between polls; static mock data doesn't,
// so real-time polling would have nothing to visibly animate. This keeps one
// mutable working copy of incidents and nudges it slightly on every poll
// after the first, deriving severity_band/auto_escalated the same way the
// backend contract describes (0–59 Normal / 60–79 Emerging / 80–100 High
// Pressure). Hotspots and metrics are re-derived from the same copy so all
// three endpoints stay in lockstep, exactly like a real backend would.
// ---------------------------------------------------------------------------
let liveIncidents = mockIncidents.map((i) => ({ ...i }));
let liveCallCount = 0;
let liveTotalComplaints = mockMetrics.total_complaints;

function bandForScore(score) {
  if (score >= 0.8) return "High Pressure";
  if (score >= 0.6) return "Emerging";
  return "Normal";
}

function driftIncidents() {
  liveCallCount += 1;
  if (liveCallCount === 1) return liveIncidents; // first load stays deterministic

  liveIncidents = liveIncidents.map((incident) => {
    // Small random walk on pressure_score, clamped to [0.05, 0.99].
    const delta = (Math.random() - 0.45) * 0.05;
    const nextScore = Math.min(0.99, Math.max(0.05, incident.pressure_score + delta));
    const nextBand = bandForScore(nextScore);

    // complaint_count nudges in the same direction as the score.
    const countDelta = delta > 0 ? Math.round(Math.random() * 2) : -Math.round(Math.random());
    const nextCount = Math.max(0, incident.complaint_count + countDelta);

    const nextSpike =
      typeof incident.spike_pct === "number" && incident.baseline > 0
        ? +(((nextCount - incident.baseline) / incident.baseline) * 100).toFixed(1)
        : incident.spike_pct;

    return {
      ...incident,
      pressure_score: +nextScore.toFixed(2),
      severity_band: nextBand,
      complaint_count: nextCount,
      unresolved_count: Math.min(nextCount, Math.max(0, incident.unresolved_count + countDelta)),
      spike_pct: nextSpike,
      auto_escalated: nextBand === "High Pressure" && nextScore >= 0.8,
      last_seen: new Date().toISOString(),
    };
  });

  return liveIncidents;
}

// --- Section 1: Complaint Object -------------------------------------------
export function getComplaints() {
  if (USE_MOCK) return mockDelay([...mockComplaints]);
  return request("/api/complaints");
}

// body: { complaint_text, latitude, longitude, locality?, image_url? }
// Returns the created Complaint Object (includes predicted_category,
// confidence, and the backend-assigned complaint_id — never assume its
// format, never sort/parse it).
export function postComplaint(payload) {
  if (USE_MOCK) {
    const id = `PRM-${1000 + Math.floor(Math.random() * 9000)}`;
    const cats = ["Sanitation", "Roads", "Streetlight", "Water", "Noise"];
    return mockDelay({
      complaint_id: id,
      predicted_category: cats[Math.floor(Math.random() * cats.length)],
      confidence: +(0.75 + Math.random() * 0.2).toFixed(2),
      status: "Open",
      ...payload,
    });
  }
  return request("/api/complaints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// --- Section 3 / drill-down: Incident Cluster Object ------------------------
export function getIncidents() {
  if (USE_MOCK) return mockDelay(driftIncidents().map((i) => ({ ...i })));
  return request("/api/incidents");
}

// Always prefer this over filtering the already-loaded incidents array —
// guarantees fresh member-complaint detail for the Evidence Panel.
export function getIncidentById(incidentId) {
  if (USE_MOCK) {
    const incident = liveIncidents.find((i) => i.incident_id === incidentId);
    if (!incident)
      return Promise.reject(
        new ApiError(`Incident ${incidentId} not found`, 404, incidentId)
      );
    return mockDelay({ ...incident });
  }
  return request(`/api/incidents/${encodeURIComponent(incidentId)}`);
}

// --- Section 6: Hotspot Object (map) ----------------------------------------
export function getHotspots() {
  if (USE_MOCK) {
    const hotspots = liveIncidents.map((i) => ({
      incident_id: i.incident_id,
      centroid_lat: i.centroid_lat,
      centroid_lng: i.centroid_lng,
      severity_band: i.severity_band,
      category: i.category,
      locality: i.locality,
    }));
    return mockDelay(hotspots);
  }
  return request("/api/hotspots");
}

// --- Section 5: Dashboard KPI Aggregates ------------------------------------
export function getMetrics() {
  if (USE_MOCK) {
    const activeIncidents = liveIncidents.filter((i) => i.severity_band !== "Normal").length;
    const emergingIncidents = liveIncidents.filter((i) => i.severity_band === "Emerging").length;
    const autoEscalated = liveIncidents.filter((i) => i.auto_escalated).length;
    if (liveCallCount > 1) liveTotalComplaints += Math.round(Math.random() * 3);
    return mockDelay({
      ...mockMetrics,
      total_complaints: liveTotalComplaints,
      active_incidents: activeIncidents,
      emerging_incidents: emergingIncidents,
      auto_escalated_incidents: autoEscalated,
    });
  }
  return request("/api/metrics");
}

// --- Section 7: Trend Data Point --------------------------------------------
export function getTrends() {
  if (USE_MOCK) return mockDelay([...mockTrends]);
  return request("/api/trends");
}

// --- Section 8: Daily Briefing -----------------------------------------------
export function getBriefing() {
  if (USE_MOCK) return mockDelay({ ...mockBriefing });
  return request("/api/briefing");
}

// --- Section 9: Model Metrics -------------------------------------------------
export function getModelMetrics() {
  if (USE_MOCK) return mockDelay({ ...mockModelMetrics });
  return request("/api/model-metrics");
}

export { ApiError };
