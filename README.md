# Praman — Civic Incident Intelligence Platform

> **GLAML Manthan 4.0 · Track 4: Public Services & Civic Tech · Problem Statement #19**  
> Role: Backend API (Member 4 of 5)  
> Active Branch: `feature/backend-api`

---

## 1. Overview
Praman transforms individual citizen complaints into an early-warning civic intelligence picture. The backend exposes clean REST endpoints connecting machine learning modules (text classification, similarity, spatial-temporal clustering, and pressure scoring) to the frontend authority dashboard and citizen reporting form.

All endpoints adhere strictly to the project's contract-locked shared schema, allowing Frontend and ML teammates to integrate seamlessly.

---

## 2. Tech Stack & Architecture

- **Framework**: Flask (Python 3.14) with `Flask-CORS` for cross-origin frontend requests.
- **Data Layer**: Modular service-based architecture (`services/`) backed by in-memory & JSON persistence (`data/`), designed for drop-in replacement with real ML module outputs.
- **Dependencies**: `flask`, `flask-cors`, `pandas`, `numpy`, `python-dateutil`.

### Project Structure
```text
Praman-manthan/
├── app.py                     # Flask app entrypoint, CORS, blueprint registration
├── requirements.txt           # Python dependency specifications
├── test_backend.py            # Automated test suite verifying all 8 endpoints & schemas
├── README.md                  # Backend documentation & API contracts
├── AI_USAGE_LOG.md            # AI usage & engineering log
├── data/
│   ├── complaints.json        # Seeded complaints conforming to COMPLAINT schema
│   ├── incidents.json         # Merged incident cluster + intelligence objects
│   └── model_metrics.json     # Classifier evaluation metrics (baseline vs comparison)
├── routes/
│   ├── complaints_bp.py       # Endpoints: GET /api/complaints, POST /api/complaints
│   ├── incidents_bp.py        # Endpoints: GET /api/incidents, /api/incidents/<id>, /api/hotspots
│   ├── metrics_bp.py          # Endpoints: GET /api/metrics, GET /api/model-metrics
│   ├── trends_bp.py           # Endpoint: GET /api/trends
│   └── briefing_bp.py         # Endpoint: GET /api/briefing
└── services/
    ├── complaint_service.py   # Complaint CRUD & classifier inference hook
    ├── incident_service.py    # Merged cluster & intelligence aggregation, hotspots & KPIs
    ├── trend_service.py       # Dynamic time-series aggregation by category & locality
    ├── briefing_service.py    # Deterministic operations briefing from computed numbers
    └── model_service.py       # Model performance statistics
```

---

## 3. Quickstart & Setup

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Backend Server
```bash
python app.py
```
The server will start at `http://localhost:5000`.

### 4. Run Automated Tests
```bash
python test_backend.py
```

---

## 4. API Endpoints & Schemas

### 1. Citizen Complaints

#### `GET /api/complaints`
Retrieve list of complaints with optional query params (`category`, `locality`, `status`).

**Response Schema (`COMPLAINT` object)**:
```json
[
  {
    "complaint_id": "C0001",
    "complaint_text": "Massive deep pothole near Main Market crossroad...",
    "category": "Pothole",
    "predicted_category": "Pothole",
    "confidence": 0.96,
    "latitude": 12.9721,
    "longitude": 77.5950,
    "locality": "Area A",
    "timestamp": "2026-09-16T08:30:00Z",
    "status": "unresolved"
  }
]
```

#### `POST /api/complaints`
Submits a new citizen complaint.

**Request Body**:
```json
{
  "complaint_text": "Water pipeline burst causing street flooding",
  "latitude": 12.9650,
  "longitude": 77.5850,
  "locality": "Area C"
}
```

**Response (`201 Created`)**:
```json
{
  "complaint_id": "C0018",
  "complaint_text": "Water pipeline burst causing street flooding",
  "category": "Water Leakage",
  "predicted_category": "Water Leakage",
  "confidence": 0.94,
  "latitude": 12.9650,
  "longitude": 77.5850,
  "locality": "Area C",
  "timestamp": "2026-09-18T03:37:00Z",
  "status": "unresolved"
}
```

---

### 2. Incidents & Hotspots

#### `GET /api/incidents`
Returns list of merged **Incident Cluster + Incident Intelligence** objects.

**Response Schema**:
```json
[
  {
    "incident_id": "INC001",
    "category": "Pothole",
    "representative_area": "Area A",
    "centroid_lat": 12.9722,
    "centroid_lng": 77.5951,
    "cluster_radius_km": 0.45,
    "complaint_ids": ["C0001", "C0002", "C0003", "C0004", "C0005"],
    "complaint_count": 24,
    "similar_complaint_count": 19,
    "unresolved_count": 22,
    "first_seen": "2026-09-15T08:00:00Z",
    "last_seen": "2026-09-17T10:05:00Z",
    "baseline": 5.0,
    "current": 24,
    "z_score": 3.4,
    "spike_pct": 380.0,
    "pressure_score": 86,
    "severity": "High Pressure",
    "auto_escalated": true
  }
]
```

#### `GET /api/incidents/<incident_id>`
Returns specific incident along with full member complaint objects for the evidence drill-down panel.

#### `GET /api/hotspots`
Reduces incidents to map-friendly points for Leaflet.js rendering.
```json
[
  {
    "incident_id": "INC001",
    "centroid_lat": 12.9722,
    "centroid_lng": 77.5951,
    "cluster_radius_km": 0.45,
    "severity": "High Pressure",
    "category": "Pothole",
    "representative_area": "Area A",
    "pressure_score": 86,
    "complaint_count": 24,
    "auto_escalated": true
  }
]
```

---

### 3. Dashboard Analytics & Operations

#### `GET /api/metrics`
Authority dashboard KPI header summary:
```json
{
  "total_complaints": 18,
  "active_incidents": 5,
  "emerging_incidents": 2,
  "auto_escalated_incidents": 1
}
```

#### `GET /api/trends`
Time series complaint volume aggregated daily, by category, and by locality for Recharts/Plotly.

#### `GET /api/briefing`
Deterministic daily operations briefing constructed strictly from computed incident and spike statistics (zero invented numbers).

#### `GET /api/model-metrics`
Classifier evaluation metrics comparing baseline (TF-IDF + Logistic Regression) against comparison model (Linear SVM).
```json
{
  "baseline_model": {
    "model_name": "TF-IDF + Logistic Regression",
    "accuracy": 0.892,
    "precision": 0.887,
    "recall": 0.890,
    "f1": 0.888
  },
  "comparison_model": {
    "model_name": "Linear SVM",
    "accuracy": 0.915,
    "precision": 0.912,
    "recall": 0.914,
    "f1": 0.913
  }
}
```

---

## 5. ML Integration Hooks (Phases 3 & 4)
The service layer (`services/`) is explicitly isolated from route handlers (`routes/`):
- **Classifier**: Hooked into `services/complaint_service.py` -> `predict_category()` and `services/model_service.py`.
- **Clustering**: Hooked into `services/incident_service.py` -> `get_all_incidents()`.
- **Spike & Pressure**: Hooked into `services/incident_service.py` calculation pipeline.
