import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import SectionState from "./SectionState";
import { SEVERITY_COLOR, severityColor } from "../severityColors";

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

// Briefly flash a marker to draw the eye when a live poll changes its data —
// works for both circleMarker (SVG) and divIcon (HTML) paths.
function flashMarker(marker) {
  const target = marker.getElement ? marker.getElement() : marker._path;
  const el = target?.querySelector?.(".hp-pulse-marker") || target;
  if (!el || !el.classList) return;
  el.classList.remove("marker-flash");
  // Force reflow so the animation restarts if it's already mid-flash.
  // eslint-disable-next-line no-unused-expressions
  el.offsetWidth;
  el.classList.add("marker-flash");
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
  const markersRef = useRef(new Map()); // incident_id -> { marker, severity_band }
  const heatLayerRef = useRef(null);
  const [heatmapOn, setHeatmapOn] = useState(false);

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

  // Diff-sync markers whenever hotspots change, instead of clearing and
  // rebuilding everything — a full rebuild on every live-poll tick made
  // every marker (even unchanged ones) flicker/re-render, which fought the
  // pulse animation on high-pressure markers. Now: remove markers whose
  // incident dropped off, add markers for new incidents, and for existing
  // ones either update position/color in place (circleMarker) or swap the
  // icon only if the severity band actually changed (divIcon vs circleMarker
  // aren't interchangeable) — with a brief flash so a judge's eye catches it.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !hotspots) return;

    const incomingIds = new Set(hotspots.map((h) => h.incident_id));

    // Remove markers for incidents no longer present.
    markersRef.current.forEach((entry, id) => {
      if (!incomingIds.has(id)) {
        map.removeLayer(entry.marker);
        markersRef.current.delete(id);
      }
    });

    hotspots.forEach((h) => {
      const existing = markersRef.current.get(h.incident_id);

      if (!existing) {
        const marker = createMarker(h, map, onSelectIncident);
        markersRef.current.set(h.incident_id, { marker, severity_band: h.severity_band });
        return;
      }

      const bandChanged = existing.severity_band !== h.severity_band;
      if (bandChanged) {
        // Marker type may need to change (circleMarker <-> divIcon) — rebuild.
        map.removeLayer(existing.marker);
        const marker = createMarker(h, map, onSelectIncident);
        markersRef.current.set(h.incident_id, { marker, severity_band: h.severity_band });
        flashMarker(marker);
        return;
      }

      // Same band — update position/tooltip in place, no rebuild.
      const { marker } = existing;
      if (marker.setLatLng) marker.setLatLng([h.centroid_lat, h.centroid_lng]);
      if (marker.setTooltipContent) marker.setTooltipContent(`${h.locality} · ${h.category}`);
      flashMarker(marker);
    });
  }, [hotspots, onSelectIncident]);

  // Highlight the selected marker.
  useEffect(() => {
    markersRef.current.forEach(({ marker }, incidentId) => {
      applySelectedStyle(marker, incidentId === selectedIncidentId);
    });
  }, [selectedIncidentId]);

  // Smooth fly-to when an incident is selected (from list or map click).
  useEffect(() => {
    if (!selectedIncidentId || !mapRef.current) return;
    const entry = markersRef.current.get(selectedIncidentId);
    if (!entry) return;
    const latlng = entry.marker.getLatLng();
    mapRef.current.flyTo(latlng, Math.max(mapRef.current.getZoom(), 14), {
      duration: 0.75,
      easeLinearity: 0.25,
    });
  }, [selectedIncidentId]);

  // Heatmap overlay — density derives from complaint_count per hotspot (not
  // pressure_score), toggled independently of the pin markers. Pins stay
  // clickable/selectable while the heatmap is layered on top.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (!heatmapOn || !hotspots || hotspots.length === 0) {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
        heatLayerRef.current = null;
      }
      return;
    }

    const points = hotspots.map((h) => [
      h.centroid_lat,
      h.centroid_lng,
      Math.max(1, h.complaint_count || 1), // intensity weight
    ]);

    if (heatLayerRef.current) {
      heatLayerRef.current.setLatLngs(points);
    } else {
      heatLayerRef.current = L.heatLayer(points, {
        radius: 35,
        blur: 25,
        maxZoom: 17,
      }).addTo(map);
    }
  }, [heatmapOn, hotspots]);

  const isEmpty = !loading && !error && (!hotspots || hotspots.length === 0);

  // The map container stays mounted at all times (Leaflet needs a stable
  // DOM node to initialize into) — loading/error/empty render as an
  // overlay on top of it instead of replacing it, so the ref is never lost.
  return (
    <section className="map-panel" aria-label="Incident map" data-reveal>
      <div className="map-legend">
        <span><i className="legend-dot" style={{ background: SEVERITY_COLOR.Normal }} /> Normal</span>
        <span><i className="legend-dot" style={{ background: SEVERITY_COLOR.Emerging }} /> Emerging</span>
        <span><i className="legend-dot" style={{ background: SEVERITY_COLOR["High Pressure"] }} /> High Pressure</span>
        <button
          type="button"
          className={`btn-heatmap-toggle ${heatmapOn ? "btn-heatmap-toggle--active" : ""}`}
          onClick={() => setHeatmapOn((v) => !v)}
          aria-pressed={heatmapOn}
        >
          {heatmapOn ? "Heatmap: On" : "Heatmap: Off"}
        </button>
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
