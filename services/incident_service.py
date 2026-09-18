import json
import os
from services.complaint_service import get_all_complaints

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "incidents.json")

_incidents = []


def _load_incidents():
    global _incidents
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                _incidents = json.load(f)
        except Exception:
            _incidents = []
    else:
        _incidents = []


def get_all_incidents(severity=None, category=None):
    """Retrieve list of merged incident cluster + intelligence objects.
    
    Swap hook: When Members 2 & 3 deliver clustering.py, anomaly.py, and pressure.py,
    this function will assemble real cluster + intelligence outputs.
    """
    if not _incidents:
        _load_incidents()

    results = _incidents
    if severity:
        results = [inc for inc in results if inc.get("severity", "").lower() == severity.lower()]
    if category:
        results = [inc for inc in results if inc.get("category", "").lower() == category.lower()]

    return results


def get_incident_by_id(incident_id):
    """Retrieve single incident along with full member complaint objects for evidence panel."""
    if not _incidents:
        _load_incidents()

    incident = next((inc for inc in _incidents if inc.get("incident_id") == incident_id), None)
    if not incident:
        return None

    # Attach actual complaint details for evidence panel
    all_complaints = get_all_complaints()
    complaint_map = {c.get("complaint_id"): c for c in all_complaints}
    member_complaints = [complaint_map[cid] for cid in incident.get("complaint_ids", []) if cid in complaint_map]

    incident_copy = dict(incident)
    incident_copy["complaints"] = member_complaints
    return incident_copy


def get_hotspots():
    """Reduces incidents to map-friendly points for Leaflet.js.
    
    Returns: incident_id, centroid_lat, centroid_lng, cluster_radius_km, severity,
    plus category, representative_area, pressure_score, complaint_count.
    """
    incidents = get_all_incidents()
    hotspots = []
    for inc in incidents:
        hotspots.append({
            "incident_id": inc.get("incident_id"),
            "centroid_lat": inc.get("centroid_lat"),
            "centroid_lng": inc.get("centroid_lng"),
            "cluster_radius_km": inc.get("cluster_radius_km", 1.0),
            "severity": inc.get("severity", "Normal"),
            "category": inc.get("category"),
            "representative_area": inc.get("representative_area"),
            "pressure_score": inc.get("pressure_score", 0),
            "complaint_count": inc.get("complaint_count", 0),
            "auto_escalated": inc.get("auto_escalated", False)
        })
    return hotspots


def get_kpi_metrics():
    """Compute KPI summary for authority dashboard."""
    complaints = get_all_complaints()
    incidents = get_all_incidents()

    total_complaints = len(complaints)
    active_incidents = len(incidents)
    emerging_incidents = sum(1 for inc in incidents if inc.get("severity") == "Emerging")
    auto_escalated_incidents = sum(1 for inc in incidents if inc.get("auto_escalated") is True)

    return {
        "total_complaints": total_complaints,
        "active_incidents": active_incidents,
        "emerging_incidents": emerging_incidents,
        "auto_escalated_incidents": auto_escalated_incidents
    }
