from flask import Blueprint, jsonify
from services.trend_service import get_trends

trends_bp = Blueprint("trends", __name__)


@trends_bp.route("/trends", methods=["GET"])
def get_complaint_trends():
    """GET /api/trends - Time series of complaint volume per category/locality for charts."""
    trends = get_trends()
    return jsonify(trends), 200
