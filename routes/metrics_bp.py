from flask import Blueprint, jsonify
from services.incident_service import get_kpi_metrics
from services.model_service import get_model_metrics

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """GET /api/metrics - KPI summary for the dashboard:
    total_complaints, active_incidents, emerging_incidents, auto_escalated_incidents.
    """
    kpis = get_kpi_metrics()
    return jsonify(kpis), 200


@metrics_bp.route("/model-metrics", methods=["GET"])
def get_evaluation_metrics():
    """GET /api/model-metrics - Classifier evaluation metrics (accuracy, precision, recall, F1)
    for baseline (TF-IDF + Logistic Regression) and comparison model (Linear SVM).
    """
    model_data = get_model_metrics()
    return jsonify(model_data), 200
