from flask import Blueprint, jsonify, request
from services.incident_service import get_all_incidents, get_incident_by_id, get_hotspots

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.route("/incidents", methods=["GET"])
def list_incidents():
    """GET /api/incidents - Returns list of merged INCIDENT CLUSTER + INTELLIGENCE objects."""
    severity = request.args.get("severity")
    category = request.args.get("category")

    incidents = get_all_incidents(severity=severity, category=category)
    return jsonify(incidents), 200


@incidents_bp.route("/incidents/<incident_id>", methods=["GET"])
def get_incident(incident_id):
    """GET /api/incidents/<incident_id> - Returns single incident with member complaints for evidence panel."""
    incident = get_incident_by_id(incident_id)
    if not incident:
        return jsonify({"error": f"Incident {incident_id} not found"}), 404
    return jsonify(incident), 200


@incidents_bp.route("/hotspots", methods=["GET"])
def list_hotspots():
    """GET /api/hotspots - Incidents reduced to map-friendly points for Leaflet.js."""
    hotspots = get_hotspots()
    return jsonify(hotspots), 200
