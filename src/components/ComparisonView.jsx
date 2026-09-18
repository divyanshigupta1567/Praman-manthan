import React, { useEffect, useState } from "react";
import { getIncidentById, ApiError } from "../api";
import { SEVERITY_COLOR } from "../severityColors";

function formatSpike(spikePct) {
  if (typeof spikePct === "number") return `+${spikePct.toFixed(1)}%`;
  return spikePct ?? "—";
}

function TrendMiniChart({ baseline = 0, currentVolume = 0, severityBand = "Normal" }) {
  const pointsCount = 5;
  // Build a synthetic 5-day progression leading up to currentVolume vs baseline
  const dataPoints = [];
  const base = Math.max(0.5, Number(baseline) || 1);
  const target = Number(currentVolume) || base;

  for (let i = 0; i < pointsCount; i++) {
    const ratio = i / (pointsCount - 1);
    const value = Math.max(0, +(base + (target - base) * Math.pow(ratio, 1.4)).toFixed(1));
    dataPoints.push(value);
  }

  const maxVal = Math.max(...dataPoints, base * 1.2, 5);
  const height = 60;
  const width = 180;
  const padding = 10;

  const getX = (idx) => padding + (idx / (pointsCount - 1)) * (width - 2 * padding);
  const getY = (val) => height - padding - (val / maxVal) * (height - 2 * padding);

  const baselineY = getY(base);
  const pathD = dataPoints
    .map((val, idx) => `${idx === 0 ? "M" : "L"} ${getX(idx)} ${getY(val)}`)
    .join(" ");

  const color = SEVERITY_COLOR[severityBand] || "#2C8391";

  return (
    <div className="comparison-trend-wrap">
      <div className="comparison-trend-labels">
        <span>Trend vs Baseline</span>
        <span className="comparison-trend-vals">
          <span style={{ color }}>{target}</span> / <span className="text-muted">{base}</span>
        </span>
      </div>
      <svg
        className="comparison-trend-svg"
        viewBox={`0 0 ${width} ${height}`}
        aria-hidden="true"
      >
        {/* Baseline dashed reference line */}
        <line
          x1={padding}
          y1={baselineY}
          x2={width - padding}
          y2={baselineY}
          stroke="#B6C0CE"
          strokeWidth="1.2"
          strokeDasharray="3 3"
        />
        {/* Volume trajectory line */}
        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Current volume endpoint dot */}
        <circle
          cx={getX(pointsCount - 1)}
          cy={getY(dataPoints[pointsCount - 1])}
          r="4"
          fill={color}
        />
      </svg>
    </div>
  );
}

export default function ComparisonView({
  incidentIds = [],
  isOpen = false,
  onClose,
  onRemoveIncident,
}) {
  const [incidentsMap, setIncidentsMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Reuse EvidencePanel data fetching pattern: get fresh details per incident
  useEffect(() => {
    if (!incidentIds || incidentIds.length === 0) {
      setIncidentsMap({});
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.allSettled(incidentIds.map((id) => getIncidentById(id)))
      .then((results) => {
        if (cancelled) return;
        const nextMap = {};
        results.forEach((res, idx) => {
          const id = incidentIds[idx];
          if (res.status === "fulfilled") {
            nextMap[id] = { data: res.value, error: null };
          } else {
            nextMap[id] = {
              data: null,
              error:
                res.reason instanceof ApiError
                  ? res.reason.message
                  : "Couldn't load incident details.",
            };
          }
        });
        setIncidentsMap(nextMap);
      })
      .catch((err) => {
        if (!cancelled) setError("Failed to fetch comparison data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [incidentIds]);

  if (!isOpen || incidentIds.length === 0) return null;

  // Identify highest pressure score among compared
  const items = incidentIds.map((id) => incidentsMap[id]?.data).filter(Boolean);
  const highestScore = Math.max(...items.map((i) => i.pressure_score ?? 0), 0);

  return (
    <div className="comparison-overlay" role="dialog" aria-label="Incident comparison">
      <div className="comparison-backdrop" onClick={onClose} aria-hidden="true" />
      <div className="comparison-panel">
        <header className="comparison-header">
          <div className="comparison-header-left">
            <h2>Incident Comparison</h2>
            <span className="comparison-badge">{incidentIds.length} of 3 selected</span>
          </div>
          <div className="comparison-header-actions">
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={onClose}
              aria-label="Close comparison view"
            >
              Done Comparing
            </button>
            <button
              type="button"
              className="btn-close"
              onClick={onClose}
              aria-label="Close comparison modal"
            >
              ×
            </button>
          </div>
        </header>

        {loading && (
          <div className="comparison-loading">
            <div className="section-skeleton" style={{ height: 280 }} aria-busy="true" />
          </div>
        )}

        {error && (
          <div className="section-error" role="alert">
            <p>{error}</p>
          </div>
        )}

        <div className={`comparison-grid comparison-grid--${incidentIds.length}`}>
          {incidentIds.map((id) => {
            const entry = incidentsMap[id];
            const data = entry?.data;
            const err = entry?.error;

            if (err) {
              return (
                <div key={id} className="comparison-col comparison-col--error">
                  <div className="comparison-col-header">
                    <strong>{id}</strong>
                    <button
                      type="button"
                      className="btn-remove-compare"
                      onClick={() => onRemoveIncident(id)}
                      aria-label={`Remove ${id} from comparison`}
                    >
                      ×
                    </button>
                  </div>
                  <p className="comparison-error-text">{err}</p>
                </div>
              );
            }

            if (!data) {
              return (
                <div key={id} className="comparison-col">
                  <div className="section-skeleton" style={{ height: 260 }} />
                </div>
              );
            }

            const isHighest = (data.pressure_score ?? 0) === highestScore && items.length > 1;
            const sevColor = SEVERITY_COLOR[data.severity_band] || "#6F7C8E";

            return (
              <div
                key={id}
                className={`comparison-col ${isHighest ? "comparison-col--highest" : ""}`}
              >
                {isHighest && (
                  <div className="comparison-highest-tag">Highest Pressure</div>
                )}

                <div className="comparison-col-header">
                  <div>
                    <span className="comparison-id">{data.incident_id}</span>
                    <h3 className="comparison-locality">{data.locality}</h3>
                    <span className="comparison-category">{data.category}</span>
                  </div>
                  <button
                    type="button"
                    className="btn-remove-compare"
                    onClick={() => onRemoveIncident(id)}
                    title="Remove from comparison"
                    aria-label={`Remove ${id} from comparison`}
                  >
                    ×
                  </button>
                </div>

                <div className="comparison-status-row">
                  <span
                    className="severity-pill"
                    style={{ background: sevColor }}
                  >
                    {data.severity_band}
                  </span>
                  {data.auto_escalated && (
                    <span className="auto-escalated-tag">Auto-escalated</span>
                  )}
                </div>

                <div className="comparison-metrics-list">
                  {/* Pressure Score */}
                  <div className="comparison-metric">
                    <span className="metric-label">Pressure Score</span>
                    <div className="metric-score-wrap">
                      <span className="metric-score-num" style={{ color: sevColor }}>
                        {Math.round((data.pressure_score ?? 0) * 100)}
                      </span>
                      <span className="metric-score-denom">/ 100</span>
                    </div>
                  </div>

                  {/* Spike % */}
                  <div className="comparison-metric">
                    <span className="metric-label">Spike %</span>
                    <span className="metric-val metric-val--spike">
                      {formatSpike(data.spike_pct)}
                    </span>
                  </div>

                  {/* Report Count */}
                  <div className="comparison-metric">
                    <span className="metric-label">Report Count</span>
                    <span className="metric-val">
                      <strong>{data.complaint_count ?? 0}</strong> reports
                      {data.unresolved_count != null && (
                        <span className="metric-sub"> ({data.unresolved_count} unresolved)</span>
                      )}
                    </span>
                  </div>

                  {/* Baseline Volume */}
                  <div className="comparison-metric">
                    <span className="metric-label">Baseline Volume</span>
                    <span className="metric-val">
                      {data.baseline ?? 0} / day
                    </span>
                  </div>

                  {/* Cluster Radius */}
                  <div className="comparison-metric">
                    <span className="metric-label">Cluster Radius</span>
                    <span className="metric-val">
                      {data.cluster_radius_km ?? "—"} km
                    </span>
                  </div>
                </div>

                {/* Trend Mini Chart */}
                <TrendMiniChart
                  baseline={data.baseline}
                  currentVolume={data.current_volume || data.complaint_count}
                  severityBand={data.severity_band}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
