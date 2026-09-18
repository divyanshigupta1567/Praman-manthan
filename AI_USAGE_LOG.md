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
