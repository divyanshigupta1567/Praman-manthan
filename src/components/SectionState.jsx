import React from "react";

// Wraps one dashboard section (KPI row, map, incident list, trend chart,
// briefing) and renders exactly one of: shaped skeleton, error+retry, empty
// message, or the real content — scoped to that section only.
export default function SectionState({
  loading,
  error,
  isEmpty,
  emptyMessage = "Nothing here yet.",
  onRetry,
  skeletonHeight = 120,
  skeletonType = "default", // "kpi" | "list" | "briefing" | "default"
  children,
}) {
  if (loading) {
    if (skeletonType === "kpi") {
      return (
        <div className="skeleton-kpi-grid" aria-busy="true" aria-label="Loading metrics">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="skeleton-kpi-card">
              <div className="skeleton-line skeleton-line--kpi-label" />
              <div className="skeleton-line skeleton-line--kpi-number" />
            </div>
          ))}
        </div>
      );
    }

    if (skeletonType === "list") {
      return (
        <div className="skeleton-list" aria-busy="true" aria-label="Loading incidents">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton-list-item">
              <div className="skeleton-dot" />
              <div className="skeleton-list-main">
                <div
                  className="skeleton-line"
                  style={{ width: i % 2 === 0 ? "58%" : "44%", height: "14px" }}
                />
                <div
                  className="skeleton-line skeleton-line--sm"
                  style={{ width: "32%", height: "11px", marginTop: "4px" }}
                />
              </div>
              <div
                className="skeleton-line skeleton-line--score"
                style={{ width: "24px", height: "16px" }}
              />
            </div>
          ))}
        </div>
      );
    }

    if (skeletonType === "briefing") {
      return (
        <div className="skeleton-briefing" aria-busy="true" aria-label="Loading briefing">
          <div className="skeleton-line" style={{ width: "95%", height: "14px", marginBottom: "8px" }} />
          <div className="skeleton-line" style={{ width: "88%", height: "14px", marginBottom: "8px" }} />
          <div className="skeleton-line" style={{ width: "62%", height: "14px", marginBottom: "16px" }} />
          <div className="skeleton-line skeleton-line--sm" style={{ width: "130px", height: "11px", marginBottom: "12px" }} />
          <div style={{ display: "flex", gap: "8px" }}>
            <div className="skeleton-line" style={{ width: "68px", height: "24px", borderRadius: "4px" }} />
            <div className="skeleton-line" style={{ width: "68px", height: "24px", borderRadius: "4px" }} />
          </div>
        </div>
      );
    }

    return (
      <div
        className="section-skeleton"
        style={{ height: skeletonHeight }}
        aria-busy="true"
        aria-label="Loading"
      />
    );
  }

  if (error) {
    return (
      <div className="section-error" role="alert">
        <p>Couldn't load this section.</p>
        <p className="section-error-detail">{error}</p>
        {onRetry && (
          <button type="button" className="btn-retry" onClick={onRetry}>
            Retry
          </button>
        )}
      </div>
    );
  }

  if (isEmpty) {
    return <p className="section-empty">{emptyMessage}</p>;
  }

  return children;
}
