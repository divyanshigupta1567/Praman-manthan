import React, { useEffect, useRef, useState } from "react";
import SectionState from "./SectionState";

const KPI_DEFS = [
  { key: "total_complaints", label: "Total Complaints" },
  { key: "active_incidents", label: "Active Incidents" },
  { key: "emerging_incidents", label: "Emerging Incidents" },
  { key: "auto_escalated_incidents", label: "Auto-Escalated Incidents" },
];

// Animates a number from its previous value to the new target using
// requestAnimationFrame + ease-out-cubic. Cancels cleanly on unmount / change.
function useCountUp(target, duration = 700) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(null);
  const fromRef = useRef(0);

  useEffect(() => {
    if (target == null) return;
    const from = fromRef.current;
    const diff = target - from;
    if (diff === 0) {
      setDisplay(target);
      return;
    }

    startRef.current = null;

    const step = (timestamp) => {
      if (!startRef.current) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(from + diff * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        fromRef.current = target;
      }
    };

    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(step);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return display;
}

// Isolated card so useCountUp can be called at the top level of a component
// (hooks must not be called inside loops).
function KpiCard({ label, value }) {
  const count = useCountUp(value ?? 0);
  return (
    <div className="kpi-card">
      <span className="kpi-label">{label}</span>
      <span className="kpi-number">{count}</span>
    </div>
  );
}

// metrics: the raw object from GET /api/metrics — nothing here is computed
// or hardcoded; every number is read straight off that response.
export default function KPIRow({ metrics, loading, error, onRetry }) {
  const isEmpty = !loading && !error && !metrics;

  return (
    <section className="kpi-row" aria-label="Key metrics">
      <SectionState
        loading={loading}
        error={error}
        isEmpty={isEmpty}
        emptyMessage="No metrics reported yet."
        onRetry={onRetry}
        skeletonHeight={96}
        skeletonType="kpi"
      >
        <div className="kpi-grid">
          {KPI_DEFS.map(({ key, label }) => (
            <KpiCard key={key} label={label} value={metrics?.[key] ?? 0} />
          ))}
        </div>
      </SectionState>
    </section>
  );
}
