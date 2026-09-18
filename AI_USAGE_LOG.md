# AI Usage Log — Praman Backend

**Project**: Praman — Civic Incident Intelligence Platform  
**Event**: GLAML Manthan 4.0 · Track 4: Public Services & Civic Tech · PS #19  
**Role**: Member 4 (Backend API)  
**Branch**: `feature/backend-api`  

This document logs all AI assistance throughout the hackathon in compliance with transparency and evaluation guidelines.

---

## Log Entries

### Entry 1: Project Kickoff & Schema Contract Alignment
- **Timestamp**: 2026-09-18 (Phase 0 / Phase 1)
- **Prompt / Request**: "Read the files and let's start step by step on a new branch." + PRD & Addendum schema specifications.
- **AI Tool**: Antigravity IDE (Gemini 3.8 Flash)
- **Actions Taken**:
  - Analyzed `for_antigravity.txt`, `pramandetails.txt`, and `help.txt`.
  - Created git branch `feature/backend-api` from `main`.
  - Defined strict schema requirements for Complaint, Incident Cluster, Incident Intelligence, Hotspots, Trends, and Briefing objects.
- **Output Generated**:
  - Initial implementation plan: `implementation_plan.md`.
- **Modifications / Human Review**: Verified that no field names deviate from the contract-locked schema agreed upon by teammates.

### Entry 2: Backend Scaffolding & Service Layer Design
- **Timestamp**: 2026-09-18 (Phase 1)
- **Prompt / Request**: Implementation of modular Flask backend with separation of concerns.
- **AI Tool**: Antigravity IDE
- **Actions Taken**:
  - Configured Python virtual environment and `requirements.txt` (`flask`, `flask-cors`, `pandas`, `numpy`, `python-dateutil`).
  - Implemented `app.py` with CORS support for React frontend clients on different ports.
  - Built Blueprints:
    - `routes/complaints_bp.py`
    - `routes/incidents_bp.py`
    - `routes/metrics_bp.py`
    - `routes/trends_bp.py`
    - `routes/briefing_bp.py`
  - Created service abstraction layer in `services/` to cleanly decouple route endpoints from data generation/ML modules.
  - Implemented sample datasets in `data/` adhering to schemas.
  - Authored automated test suite in `test_backend.py` (24 test assertions passing 100%).
- **Modifications / Human Review**:
  - Ensured briefing service uses deterministic calculations strictly derived from computed incident numbers (guardrail against LLM hallucination).
  - Verified complaint ID generation conforms to sequential format (`C0001`, `C0002`...).

### Entry 3: Real Dataset Migration (9,200 Rows), Spatial-Temporal Window & Latency Optimization
- **Timestamp**: 2026-09-18 (Phase 2 & Defense Preparation)
- **Prompt / Request**: Migrate to 3.5-year real civic dataset (`praman_train.csv`, `praman_test.csv`), resolve temporal staleness, optimize complaint ingestion latency, and author defense documentation.
- **AI Tool**: Antigravity IDE (Gemini 3.8 Flash)
- **Actions Taken**:
  - Implemented in-memory multi-source dataset loader in `services/complaint_service.py` to ingest 9,200+ historical rows.
  - Formulated `ANCHOR_DATE = max(timestamp)` pattern across all services (`complaint_service`, `incident_service`, `briefing_service`) to avoid time-decay distortion on historical datasets.
  - Resolved `TypeError` on offset-naive vs offset-aware datetime subtraction by establishing a unified UTC normalization boundary (`_parse_dt`) across services.
  - Implemented 72-hour temporal sliding window on spatial clustering to prevent grouping incidents across years.
  - Decoupled `severity` from temporal resolution status in `incident_service.py` to ensure valid anomaly escalation (High Pressure / Emerging) triggers correctly on historical data.
  - Designed append-only `data/new_submissions.json` architecture to avoid rewriting 9,200 rows to disk on POST requests.
  - Benchmarked live POST latency in Windows PowerShell (`Measure-Command` / `Invoke-RestMethod` vs `127.0.0.1:5000`): confirmed **~31 ms** backend processing time and **~112 ms** client roundtrip.
  - Authored comprehensive `HACKATHON_DEFENSE_GUIDE.md` covering architecture rationales, formula breakdowns, judge defense Q&A, and live demo steps.
  - Verified 100% test pass rate across 25 assertions (`test_backend.py`).
- **Modifications / Human Review**:
  - Confirmed human review on disabling full-dataset disk serialization to guarantee sub-second live demonstration capability.
  - Validated adherence to strict "no unapproved git commits" constraint.
