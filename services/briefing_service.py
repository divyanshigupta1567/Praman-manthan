from datetime import datetime, timezone
from services.incident_service import get_all_incidents, get_kpi_metrics


def generate_operations_briefing():
    """Generates a deterministic daily operations briefing.
    
    Guaranteed to reflect ONLY computed incident data — never invented numbers.
    """
    metrics = get_kpi_metrics()
    incidents = get_all_incidents()

    high_pressure = [inc for inc in incidents if inc.get("severity") == "High Pressure" or inc.get("auto_escalated")]
    emerging = [inc for inc in incidents if inc.get("severity") == "Emerging"]
    normal = [inc for inc in incidents if inc.get("severity") == "Normal"]

    high_pressure.sort(key=lambda x: x.get("pressure_score", 0), reverse=True)
    emerging.sort(key=lambda x: x.get("pressure_score", 0), reverse=True)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Construct deterministic summary narrative
    bullet_points = []
    
    if high_pressure:
        for inc in high_pressure[:3]:
            bullet_points.append(
                f"[CRITICAL ESCALATION] Incident {inc.get('incident_id')} ({inc.get('category')} in {inc.get('representative_area')}): "
                f"Pressure score reached {inc.get('pressure_score')}/100 with {inc.get('complaint_count')} reports "
                f"({inc.get('unresolved_count')} unresolved). Spike detected at {inc.get('spike_pct')}% above baseline "
                f"(z-score: {inc.get('z_score')}). Immediate dispatch recommended."
            )
        if len(high_pressure) > 3:
            bullet_points.append(f"...and {len(high_pressure) - 3} other high-pressure incidents auto-escalated.")
    else:
        bullet_points.append("No incidents currently meeting high-pressure auto-escalation criteria.")

    if emerging:
        for inc in emerging[:3]:
            bullet_points.append(
                f"[MONITORING] Emerging incident {inc.get('incident_id')} ({inc.get('category')} in {inc.get('representative_area')}): "
                f"Pressure score {inc.get('pressure_score')}/100, volume {inc.get('current')} reports vs baseline {inc.get('baseline')} "
                f"({inc.get('spike_pct')}% increase)."
            )
        if len(emerging) > 3:
            bullet_points.append(f"...and {len(emerging) - 3} other emerging incidents under active monitoring.")

    bullet_points.append(
        f"[SYSTEM TOTALS] {metrics['total_complaints']} total complaints logged across {metrics['active_incidents']} active incidents "
        f"({metrics['emerging_incidents']} emerging, {metrics['auto_escalated_incidents']} auto-escalated)."
    )

    overview = (
        f"Praman Daily Civic Intelligence Briefing for {today_str}. "
        f"System monitors {metrics['total_complaints']} complaints aggregated into {metrics['active_incidents']} geographic incident clusters. "
        f"{metrics['auto_escalated_incidents']} incident(s) flagged for priority escalation."
    )

    return {
        "briefing_date": today_str,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "overview": overview,
        "key_metrics": metrics,
        "action_items": bullet_points,
        "high_pressure_incidents": high_pressure,
        "emerging_incidents": emerging,
        "normal_incidents_count": len(normal)
    }
