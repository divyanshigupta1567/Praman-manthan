from flask import Blueprint, jsonify
from services.briefing_service import generate_operations_briefing

briefing_bp = Blueprint("briefing", __name__)


@briefing_bp.route("/briefing", methods=["GET"])
def get_daily_briefing():
    """GET /api/briefing - Daily operations briefing built ONLY from computed incident data."""
    briefing = generate_operations_briefing()
    return jsonify(briefing), 200
