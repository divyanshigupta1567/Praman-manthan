import React from "react";

// incidents: the full live incidents array. This filters on the
// auto_escalated boolean the backend already computed — never
// recomputed from pressure_score here.
export default function AutoEscalationBanner({ incidents, onSelectIncident }) {
  const escalated = (incidents || []).filter((i) => i.auto_escalated === true);

  if (escalated.length === 0) return null;

  return (
    <div className="escalation-banner" role="alert">
      <span className="escalation-banner-headline">
        {escalated.length === 1
          ? "1 incident auto-escalated"
          : `${escalated.length} incidents auto-escalated`}
      </span>
      <div className="escalation-banner-list">
        {escalated.map((i) => (
          <button
            key={i.incident_id}
            type="button"
            className="escalation-chip"
            onClick={() => onSelectIncident(i.incident_id)}
          >
            <span className="chip-locality">{i.locality}</span>
            <span className="chip-category">{i.category}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
