import React from "react";
import SectionState from "./SectionState";
import { SEVERITY_COLOR } from "../severityColors";

// Shows incidents worth a judge's attention right now: anything not
// "Normal", ranked by pressure_score. severity_band drives the color dot —
// never recomputed here.
export default function IncidentList({
  incidents,
  loading,
  error,
  onRetry,
  onSelectIncident,
  selectedIncidentId,
  isFiltered = false,
  comparingIds = [],
  onToggleCompare,
  onOpenComparison,
}) {
  const list = incidents || [];
  // When filters are active, show matching incidents directly; otherwise prioritize non-normal incidents
  const ranked = (isFiltered ? list : list.filter((i) => i.severity_band !== "Normal"))
    .sort((a, b) => (b.pressure_score ?? 0) - (a.pressure_score ?? 0))
    .slice(0, 8);

  const isEmpty = !loading && !error && ranked.length === 0;
  const isMaxReached = comparingIds.length >= 3;

  return (
    <section className="incident-list-panel" aria-label="Top emerging incidents" data-reveal data-reveal-delay="1">
      <div className="incident-list-header">
        <h2 className="panel-title">Top Emerging Incidents</h2>
        {comparingIds.length > 0 && (
          <div className="compare-summary-pill">
            <span>{comparingIds.length}/3 to compare</span>
            {comparingIds.length >= 2 && onOpenComparison && (
              <button
                type="button"
                className="btn-compare-view"
                onClick={onOpenComparison}
              >
                Compare
              </button>
            )}
          </div>
        )}
      </div>

      <SectionState
        loading={loading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage={isFiltered ? "No incidents match the active filters." : "No emerging or high-pressure incidents right now."}
        onRetry={onRetry}
        skeletonHeight={320}
        skeletonType="list"
      >
        <ul className="incident-list">
          {ranked.map((i) => {
            const isComparing = comparingIds.includes(i.incident_id);
            const disableAdd = !isComparing && isMaxReached;

            return (
              <li key={i.incident_id} className="incident-list-item-wrap">
                <button
                  type="button"
                  className={
                    "incident-row" +
                    (i.incident_id === selectedIncidentId ? " incident-row-selected" : "") +
                    (isComparing ? " incident-row-comparing" : "")
                  }
                  onClick={() => onSelectIncident(i.incident_id)}
                >
                  <span
                    className="incident-dot"
                    style={{ background: SEVERITY_COLOR[i.severity_band] || "#6F7C8E" }}
                    aria-hidden="true"
                  />
                  <span className="incident-row-main">
                    <span className="incident-row-title">{i.locality}</span>
                    <span className="incident-row-sub">{i.category}</span>
                    <span className="incident-row-count">{i.complaint_count} reports</span>
                  </span>
                  <span className="incident-row-score">
                    {Math.round((i.pressure_score ?? 0) * 100)}
                  </span>
                  {onToggleCompare && (
                    <span
                      className={`btn-compare-toggle ${
                        isComparing ? "btn-compare-toggle--active" : ""
                      } ${disableAdd ? "btn-compare-toggle--disabled" : ""}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!disableAdd || isComparing) {
                          onToggleCompare(i.incident_id);
                        }
                      }}
                      role="checkbox"
                      aria-checked={isComparing}
                      tabIndex={0}
                      title={
                        isComparing
                          ? "Remove from comparison"
                          : disableAdd
                          ? "Max 3 incidents selected"
                          : "Select to compare"
                      }
                    >
                      {isComparing ? "✓ Compared" : "+ Compare"}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </SectionState>
    </section>
  );
}
