import React, { useEffect, useState } from "react";
import { getIncidentById, ApiError } from "../api";
import { SEVERITY_COLOR } from "../severityColors";

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

// spike_pct is a number OR the literal string 'N/A (new activity)' —
// this is the one place that has to type-check it before formatting.
function formatSpike(spikePct) {
  if (typeof spikePct === "number") return `+${spikePct.toFixed(1)}%`;
  return spikePct ?? "—";
}

// pressure_score comes off the backend as a 0–1 fraction (e.g. 0.91) but is
// displayed as a 0–100 score everywhere else in the app (IncidentList,
// ComparisonView). This panel was rendering the raw fraction — bug fix.
function formatPressureScore(score) {
  if (typeof score !== "number") return "—";
  return Math.round(score * 100);
}

// incidentId: the currently selected incident_id (opaque string — never
// parsed or sorted). complaintsById: a Map for looking up sample
// complaints already loaded in Dashboard state, used only as a fallback
// if the incident detail response doesn't already embed full complaint
// objects for sample_complaint_ids.
//
// isOpen: boolean — drives the CSS slide-in transition. The panel stays
// mounted at all times so the exit animation can play before React removes it.
export default function EvidencePanel({ incidentId, complaintsById, onClose, isOpen }) {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!incidentId) {
      setIncident(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getIncidentById(incidentId)
      .then((data) => {
        if (!cancelled) setIncident(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Couldn't load this incident.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [incidentId]);

  const sampleIds = incident?.sample_complaint_ids || [];
  const sampleComplaints = sampleIds
    .map((id) => incident?.sample_complaints?.find?.((c) => c.complaint_id === id) || complaintsById?.get(id))
    .filter(Boolean);

  return (
    <>
      {/* Backdrop fades in behind the panel */}
      <div
        className={`evidence-backdrop${isOpen ? " evidence-backdrop--visible" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel slides in from the right; transform driven by CSS class */}
      <aside
        className={`evidence-panel${isOpen ? " evidence-panel--open" : ""}`}
        role="dialog"
        aria-label="Incident evidence"
        aria-hidden={!isOpen}
      >
        <div className="evidence-panel-header">
          <h2>Evidence Panel</h2>
          <button type="button" className="btn-close" onClick={onClose} aria-label="Close evidence panel">
            ×
          </button>
        </div>

        {loading && <div className="section-skeleton" style={{ height: 320 }} aria-busy="true" />}

        {error && (
          <div className="section-error" role="alert">
            <p>Couldn't load this incident.</p>
            <p className="section-error-detail">{error}</p>
            <button
              type="button"
              className="btn-retry"
              onClick={() => {
                setLoading(true);
                setError(null);
                getIncidentById(incidentId)
                  .then(setIncident)
                  .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load this incident."))
                  .finally(() => setLoading(false));
              }}
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && incident && (
          <dl className="evidence-fields">
            <div><dt>Incident ID</dt><dd>{incident.incident_id}</dd></div>
            <div><dt>Category</dt><dd>{incident.category}</dd></div>
            <div><dt>Area</dt><dd>{incident.locality}</dd></div>
            <div><dt>Reports</dt><dd>{incident.complaint_count}</dd></div>
            <div><dt>Baseline</dt><dd>{incident.baseline}</dd></div>
            <div><dt>Spike %</dt><dd>{formatSpike(incident.spike_pct)}</dd></div>
            <div>
              <dt>Time Window</dt>
              <dd>{formatDate(incident.first_seen)} → {formatDate(incident.last_seen)}</dd>
            </div>
            <div><dt>Potentially Related Reports</dt><dd>{incident.similar_complaint_count}</dd></div>
            <div><dt>Unresolved Reports</dt><dd>{incident.unresolved_count}</dd></div>
            <div><dt>Cluster Radius</dt><dd>{incident.cluster_radius_km} km</dd></div>
            <div><dt>Pressure Score</dt><dd>{formatPressureScore(incident.pressure_score)}</dd></div>
            <div>
              <dt>Status</dt>
              <dd>
                <span
                  className="severity-pill"
                  style={{ background: SEVERITY_COLOR[incident.severity_band] || "#6F7C8E" }}
                >
                  {incident.severity_band}
                </span>
                {incident.auto_escalated && <span className="auto-escalated-tag">Auto-escalated</span>}
              </dd>
            </div>

            <div className="evidence-samples">
              <dt>Sample complaints</dt>
              <dd>
                {sampleComplaints.length > 0 ? (
                  <ul>
                    {sampleComplaints.map((c) => (
                      <li key={c.complaint_id}>
                        <span className="sample-id">{c.complaint_id}</span> — {c.complaint_text}
                        <span className="sample-status"> ({c.status})</span>
                      </li>
                    ))}
                  </ul>
                ) : sampleIds.length > 0 ? (
                  <ul>
                    {sampleIds.map((id) => (
                      <li key={id}><span className="sample-id">{id}</span> — details not loaded</li>
                    ))}
                  </ul>
                ) : (
                  <p className="section-empty">No sample complaints attached.</p>
                )}
              </dd>
            </div>
          </dl>
        )}
      </aside>
    </>
  );
}
