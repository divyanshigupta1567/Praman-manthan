"""Praman — Civic Incident Intelligence Platform
Backend API (Flask)
GLAML Manthan 4.0 · Track 4: Public Services & Civic Tech · PS #19
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

from routes.complaints_bp import complaints_bp
from routes.incidents_bp import incidents_bp
from routes.metrics_bp import metrics_bp
from routes.trends_bp import trends_bp
from routes.briefing_bp import briefing_bp


def create_app():
    """Application factory for Praman backend."""
    app = Flask(__name__)

    # Enable CORS for React frontend running on any port (Vite/CRA)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints under /api prefix
    app.register_blueprint(complaints_bp, url_prefix="/api")
    app.register_blueprint(incidents_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(trends_bp, url_prefix="/api")
    app.register_blueprint(briefing_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return jsonify({
            "project": "Praman — Civic Incident Intelligence Platform",
            "status": "online",
            "version": "1.0.0",
            "documentation": "/api/health",
            "endpoints": [
                {"method": "GET", "path": "/api/complaints", "description": "List of citizen complaints"},
                {"method": "POST", "path": "/api/complaints", "description": "Submit a citizen complaint"},
                {"method": "GET", "path": "/api/incidents", "description": "List of merged incident clusters and intelligence"},
                {"method": "GET", "path": "/api/incidents/<id>", "description": "Incident details with member complaints"},
                {"method": "GET", "path": "/api/hotspots", "description": "Map-friendly hotspot points for Leaflet"},
                {"method": "GET", "path": "/api/metrics", "description": "Dashboard KPI summary"},
                {"method": "GET", "path": "/api/trends", "description": "Time series volume by category and locality"},
                {"method": "GET", "path": "/api/briefing", "description": "Deterministic daily operations briefing"},
                {"method": "GET", "path": "/api/model-metrics", "description": "Classifier evaluation metrics"}
            ]
        })

    @app.route("/api/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "praman-backend-api"
        }), 200

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
