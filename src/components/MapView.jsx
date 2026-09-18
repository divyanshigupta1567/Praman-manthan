import React, { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import SectionState from "./SectionState";

// severity_band is read directly off each hotspot — never recomputed from
// pressure_score. This keeps band cutoffs owned entirely by the backend.
const SEVERITY_COLOR = {
  Normal: "#3FCB6B",
  Emerging: "#E8B93F",
  "High Pressure": "#E5484D",
};
const DEFAULT_COLOR = "#8A97A3";

function severityColor(band) {
  return SEVERITY_COLOR[band] || DEFAULT_COLOR;
}

// Mathura, UP is a reasonable default center for this deployment; swap for
// your city's coordinates or compute a bounds-fit from the first response.
const DEFAULT_CENTER = [27.4924, 77.6737];
const DEFAULT_ZOOM = 13;

// Build a Leaflet marker for a hotspot.
// High-pressure incidents get a CSS-animated divIcon (so the pulse animation
// works — SVG paths on circleMarker can't be targeted by CSS keyframes).
// Normal/emerging stay as circleMarkers and are never pulsed.
function createMarker(h, map, onSelectIncident) {
  const color = severityColor(h.severity_band);

  if (h.severity_band === "High Pressure") {
    const icon = L.divIcon({
      className: "",          // clear Leaflet's default white-box class
      html: `<div class="hp-pulse-marker" style="background:${color};" data-incident="${h.incident_id}"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
      tooltipAnchor: [0, -12],
    });
    const marker = L.marker([h.centroid_lat, h.centroid_lng], { icon }).addTo(map);
    marker.bindTooltip(`${h.locality} · ${h.category}`, { direction: "top" });
    marker.on("click", () => onSelectIncident(h.incident_id));
    return marker;
  }

  // Normal / Emerging — static circleMarker
  const marker = L.circleMarker([h.centroid_lat, h.centroid_lng], {
    radius: 10,
    color,
    fillColor: color,
    fillOpacity: 0.85,
    weight: 2,
  }).addTo(map);
  marker.bindTooltip(`${h.locality} · ${h.category}`, { direction: "top" });
  marker.on("click", () => onSelectIncident(h.incident_id));
  return marker;
}

// Apply or remove selected styling. circleMarker uses setStyle;
// divIcon markers get a CSS class toggled on their inner element.
function applySelectedStyle(marker, isSelected) {
  if (marker.setStyle) {
    // circleMarker path — weight is the only meaningful toggle here
    marker.setStyle({ weight: isSelected ? 4 : 2 });
  } else {
    // divIcon marker — toggle helper class on the inner div
    const el = marker.getElement();
    const dot = el?.querySelector(".hp-pulse-marker");
    if (dot) {
      dot.classList.toggle("hp-pulse-marker--selected", isSelected);
    }
  }
}

export default function MapView({ hotspots, loading, error, onRetry, onSelectIncident, selectedIncidentId }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef(new Map());

  // Initialize the map once.
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;
    mapRef.current = L.map(mapContainerRef.current, {
      zoomControl: true,
    }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(mapRef.current);

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Sync markers whenever hotspots change.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !hotspots) return;

    // Clear previous markers.
    markersRef.current.forEach((marker) => map.removeLayer(marker));
    markersRef.current.clear();

    hotspots.forEach((h) => {
      const marker = createMarker(h, map, onSelectIncident);
      markersRef.current.set(h.incident_id, marker);
    });
  }, [hotspots, onSelectIncident]);

  // Highlight the selected marker.
  useEffect(() => {
    markersRef.current.forEach((marker, incidentId) => {
      applySelectedStyle(marker, incidentId === selectedIncidentId);
    });
  }, [selectedIncidentId]);

  // Smooth fly-to when an incident is selected (from list or map click).
  useEffect(() => {
    if (!selectedIncidentId || !mapRef.current) return;
    const marker = markersRef.current.get(selectedIncidentId);
    if (!marker) return;
    const latlng = marker.getLatLng();
    mapRef.current.flyTo(latlng, Math.max(mapRef.current.getZoom(), 14), {
      duration: 0.75,
      easeLinearity: 0.25,
    });
  }, [selectedIncidentId]);

  const isEmpty = !loading && !error && (!hotspots || hotspots.length === 0);

  // The map container stays mounted at all times (Leaflet needs a stable
  // DOM node to initialize into) — loading/error/empty render as an
  // overlay on top of it instead of replacing it, so the ref is never lost.
  return (
    <section className="map-panel" aria-label="Incident map">
      <div className="map-legend">
        <span><i className="legend-dot" style={{ background: SEVERITY_COLOR.Normal }} /> Normal</span>
        <span><i className="legend-dot" style={{ background: SEVERITY_COLOR.Emerging }} /> Emerging</span>
        <span><i className="legend-dot" style={{ background: SEVERITY_COLOR["High Pressure"] }} /> High Pressure</span>
      </div>
      <div className="map-container-wrap">
        <div ref={mapContainerRef} className="map-container" role="img" aria-label="Map of incident hotspots" />
        {(loading || error || isEmpty) && (
          <div className="map-overlay">
            <SectionState
              loading={loading}
              error={error}
              isEmpty={isEmpty}
              emptyMessage="No hotspots detected yet."
              onRetry={onRetry}
              skeletonHeight={480}
            >
              <></>
            </SectionState>
          </div>
        )}
      </div>
    </section>
  );
}
