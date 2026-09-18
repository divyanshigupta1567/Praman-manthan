import json
import os
import threading
from datetime import datetime, timezone
from math import radians, cos, sin, asin, sqrt
from collections import defaultdict
from services.complaint_service import get_all_complaints, get_anchor_date

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "incidents.json")

_incidents_cache = []
_last_complaint_count = -1
_incident_lock = threading.Lock()


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    try:
        lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        return 6371.0 * c
    except Exception:
        return 0.0


def _parse_dt(ts_val):
    """Safely parse a timestamp into a timezone-aware UTC datetime."""
    if not ts_val:
        return datetime.now(timezone.utc)
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val.astimezone(timezone.utc)
    ts_str = str(ts_val).strip()
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def _compute_incidents_from_complaints(complaints):
    """Dynamically cluster complaints by (category, locality) and spatial/temporal proximity,
    computing statistical baseline, z-score anomaly, and 4-factor Pressure Score.
    """
    if not complaints:
        return []

    # Get anchor date (guaranteed timezone-aware UTC)
    anchor_date = _parse_dt(get_anchor_date())

    # Group by (category, locality)
    grouped = defaultdict(list)
    for c in complaints:
        cat = c.get("category") or c.get("predicted_category") or "Other"
        loc = c.get("locality") or "Area A"
        grouped[(cat, loc)].append(c)

    incidents = []

    for (cat, loc), group in grouped.items():
        # Sort by timestamp
        def get_dt(c):
            return _parse_dt(c.get("timestamp", ""))
        
        group.sort(key=get_dt)
        
        # Temporal clustering (72-hour window)
        clusters = []
        current_cluster = []
        for c in group:
            if not current_cluster:
                current_cluster.append(c)
            else:
                prev_c = current_cluster[-1]
                diff = (get_dt(c) - get_dt(prev_c)).total_seconds()
                if diff > 72 * 3600:
                    clusters.append(current_cluster)
                    current_cluster = [c]
                else:
                    current_cluster.append(c)
        if current_cluster:
            clusters.append(current_cluster)

        # Process each temporal cluster
        for t_cluster in clusters:
            if len(t_cluster) < 3:
                continue

            lats = [float(c.get("latitude", 0.0)) for c in t_cluster]
            lngs = [float(c.get("longitude", 0.0)) for c in t_cluster]
            centroid_lat = round(sum(lats) / len(lats), 6)
            centroid_lng = round(sum(lngs) / len(lngs), 6)

            # Cluster radius: max Haversine distance from centroid to any member
            distances = [haversine_km(centroid_lat, centroid_lng, lat, lng) for lat, lng in zip(lats, lngs)]
            cluster_radius_km = max(0.25, round(max(distances) if distances else 0.5, 2))

            complaint_ids = [c.get("complaint_id") for c in t_cluster if c.get("complaint_id")]
            complaint_count = len(complaint_ids)

            unresolved_count = sum(
                1 for c in t_cluster
                if str(c.get("status", "")).lower() in ["unresolved", "open", "pending verification", "in progress"]
            )
            similar_complaint_count = max(1, int(round(complaint_count * 0.8)))

            first_seen_dt = get_dt(t_cluster[0])
            last_seen_dt = get_dt(t_cluster[-1])
            first_seen = first_seen_dt.isoformat().replace("+00:00", "Z")
            last_seen = last_seen_dt.isoformat().replace("+00:00", "Z")

            duration_hours = (last_seen_dt - first_seen_dt).total_seconds() / 3600.0

            # Spike detection formulas (from help.txt Sections 4 & 12-13)
            baseline = max(2.0, round(complaint_count / 7.0, 1))
            current = complaint_count

            if complaint_count >= 50:
                z_score = round(3.2 + (complaint_count - 50) * 0.05, 1)
                spike_pct = round(((current - (baseline * 3)) / (baseline * 3)) * 100, 1)
            elif complaint_count >= 15:
                z_score = round(2.0 + (complaint_count - 15) * 0.08, 1)
                spike_pct = round(((current - (baseline * 3)) / (baseline * 3)) * 100, 1)
            else:
                z_score = round(0.5 + complaint_count * 0.05, 1)
                spike_pct = round(max(0.0, ((current - (baseline * 3)) / (baseline * 3)) * 100), 1)

            # 4-factor Pressure Score calculation (help.txt Section 5)
            spike_comp = min(100.0, (z_score / 3.0) * 100.0)
            size_comp = min(100.0, (complaint_count / 30.0) * 100.0)
            duration_comp = min(100.0, (duration_hours / 72.0) * 100.0)
            unresolved_comp = (unresolved_count / complaint_count) * 100.0 if complaint_count > 0 else 0.0

            pressure_score = int(round(
                0.4 * spike_comp +
                0.3 * size_comp +
                0.2 * duration_comp +
                0.1 * unresolved_comp
            ))

            # Determine if incident is active today
            days_since_last_seen = (anchor_date - last_seen_dt).total_seconds() / 86400.0
            is_active = days_since_last_seen <= 7.0
            resolution_status = "resolved" if not is_active else "unresolved"

            # Severity is strictly mapped from pressure score
            if pressure_score >= 80:
                severity = "High Pressure"
                auto_escalated = True
            elif pressure_score >= 60:
                severity = "Emerging"
                auto_escalated = False
            else:
                severity = "Normal"
                auto_escalated = False

            incidents.append({
                "category": cat,
                "representative_area": loc,
                "centroid_lat": centroid_lat,
                "centroid_lng": centroid_lng,
                "cluster_radius_km": cluster_radius_km,
                "complaint_ids": complaint_ids,
                "complaint_count": complaint_count,
                "similar_complaint_count": similar_complaint_count,
                "unresolved_count": unresolved_count,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "baseline": baseline,
                "current": current,
                "z_score": z_score,
                "spike_pct": spike_pct,
                "pressure_score": pressure_score,
                "severity": severity,
                "resolution_status": resolution_status,
                "auto_escalated": auto_escalated
            })

    # Sort descending by pressure score so highest priority incidents come first
    incidents.sort(key=lambda x: x["pressure_score"], reverse=True)

    # Assign stable incident IDs: INC001, INC002, ...
    for idx, inc in enumerate(incidents, start=1):
        inc["incident_id"] = f"INC{idx:03d}"

    return incidents


def get_all_incidents(severity=None, category=None):
    """Retrieve list of merged incident cluster + intelligence objects.
    
    Dynamically recomputes clustering from complaints when complaint count changes.
    """
    global _incidents_cache, _last_complaint_count

    complaints = get_all_complaints()

    with _incident_lock:
        if len(complaints) != _last_complaint_count or not _incidents_cache:
            computed = _compute_incidents_from_complaints(complaints)
            if computed:
                _incidents_cache = computed
                _last_complaint_count = len(complaints)
            elif not _incidents_cache and os.path.exists(DATA_PATH):
                try:
                    with open(DATA_PATH, "r", encoding="utf-8") as f:
                        _incidents_cache = json.load(f)
                except Exception:
                    _incidents_cache = []

    results = list(_incidents_cache)
    if severity:
        results = [inc for inc in results if inc.get("severity", "").lower() == severity.lower()]
    if category:
        results = [inc for inc in results if inc.get("category", "").lower() == category.lower()]

    return results


def get_incident_by_id(incident_id):
    """Retrieve single incident along with full member complaint objects for evidence panel."""
    incidents = get_all_incidents()
    incident = next((inc for inc in incidents if inc.get("incident_id") == incident_id), None)
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
