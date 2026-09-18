// severityColors.js
// Single source of truth for severity_band → color. Previously this map was
// copy-pasted into MapView.jsx, IncidentList.jsx, EvidencePanel.jsx, and
// ComparisonView.jsx — a drift risk the README flagged. Import from here
// instead of redefining it locally.
export const SEVERITY_COLOR = {
  Normal: "#2E9E5B",
  Emerging: "#C4870F",
  "High Pressure": "#D23B40",
};

export const DEFAULT_SEVERITY_COLOR = "#6F7C8E";

export function severityColor(band) {
  return SEVERITY_COLOR[band] || DEFAULT_SEVERITY_COLOR;
}
