from flask import Blueprint, jsonify, request
from services.complaint_service import get_all_complaints, create_complaint

complaints_bp = Blueprint("complaints", __name__)


@complaints_bp.route("/complaints", methods=["GET"])
def list_complaints():
    """GET /api/complaints - Returns list of COMPLAINT objects."""
    category = request.args.get("category")
    locality = request.args.get("locality")
    status = request.args.get("status")

    complaints = get_all_complaints(category=category, locality=locality, status=status)
    return jsonify(complaints), 200


@complaints_bp.route("/complaints", methods=["POST"])
def submit_complaint():
    """POST /api/complaints - Submits a citizen complaint.
    
    Accepts: {complaint_text, latitude, longitude, locality (optional)}
    Generates complaint_id, assigns predicted_category + confidence,
    and returns newly created COMPLAINT object.
    """
    data = request.get_json(silent=True) or {}

    complaint_text = data.get("complaint_text", "").strip()
    if not complaint_text:
        return jsonify({"error": "complaint_text is required"}), 400

    new_complaint = create_complaint(data)
    return jsonify(new_complaint), 201
