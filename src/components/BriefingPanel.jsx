import React from "react";
import SectionState from "./SectionState";

// briefing.summary_text is rendered verbatim — this is display text, not
// something to parse or recompute. highlighted_incident_ids link back into
// the same onSelectIncident flow the map and list use.
export default function BriefingPanel({ briefing, loading, error, onRetry, onSelectIncident }) {
  const isEmpty = !loading && !error && !briefing?.summary_text;

  return (
    <section className="briefing-panel" aria-label="Daily operations briefing" data-reveal data-reveal-delay="2">
      <h2 className="panel-title">Daily Briefing</h2>
      <SectionState
        loading={loading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="No briefing generated yet today."
        onRetry={onRetry}
        skeletonHeight={140}
        skeletonType="briefing"
      >
        <p className="briefing-text">{briefing?.summary_text}</p>
        {briefing?.generated_at && (
          <p className="briefing-timestamp">
            Generated {new Date(briefing.generated_at).toLocaleString()}
          </p>
        )}
        {briefing?.highlighted_incident_ids?.length > 0 && (
          <div className="briefing-links">
            {briefing.highlighted_incident_ids.map((id) => (
              <button key={id} type="button" className="briefing-chip" onClick={() => onSelectIncident(id)}>
                {id}
              </button>
            ))}
          </div>
        )}
      </SectionState>
    </section>
  );
}
