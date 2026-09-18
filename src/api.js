// api.js
// Single source of truth for talking to the Spandan backend.
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
  if (USE_MOCK) return mockDelay([...mockIncidents]);
  return request("/api/incidents");
}

// Always prefer this over filtering the already-loaded incidents array —
// guarantees fresh member-complaint detail for the Evidence Panel.
export function getIncidentById(incidentId) {
  if (USE_MOCK) {
    const incident = mockIncidents.find((i) => i.incident_id === incidentId);
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
  if (USE_MOCK) return mockDelay([...mockHotspots]);
  return request("/api/hotspots");
}

// --- Section 5: Dashboard KPI Aggregates ------------------------------------
export function getMetrics() {
  if (USE_MOCK) return mockDelay({ ...mockMetrics });
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
