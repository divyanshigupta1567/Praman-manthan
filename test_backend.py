"""Verification script for Praman Backend API endpoints and schema conformance."""

import json
from app import create_app


def run_tests():
    app = create_app()
    client = app.test_client()
    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}: {details}")

    print("\n--- Running Praman API Verification Tests ---")

    # 1. Health check
    res = client.get("/api/health")
    assert_test("GET /api/health returns 200", res.status_code == 200)

    # 2. GET /api/complaints
    res = client.get("/api/complaints")
    assert_test("GET /api/complaints returns 200", res.status_code == 200)
    complaints = res.get_json()
    assert_test("Complaints is non-empty list", isinstance(complaints, list) and len(complaints) > 0)
    
    first_c = complaints[0] if complaints else {}
    expected_c_keys = {"complaint_id", "complaint_text", "category", "predicted_category",
                       "confidence", "latitude", "longitude", "locality", "timestamp", "status"}
    assert_test("Complaint schema conforms to spec", expected_c_keys.issubset(set(first_c.keys())),
                f"Missing keys: {expected_c_keys - set(first_c.keys())}")

    # 3. GET /api/incidents
    res = client.get("/api/incidents")
    assert_test("GET /api/incidents returns 200", res.status_code == 200)
    incidents = res.get_json()
    assert_test("Incidents is non-empty list", isinstance(incidents, list) and len(incidents) > 0)

    first_inc = incidents[0] if incidents else {}
    expected_inc_keys = {"incident_id", "category", "representative_area", "centroid_lat",
                         "centroid_lng", "cluster_radius_km", "complaint_ids", "complaint_count",
                         "similar_complaint_count", "unresolved_count", "first_seen", "last_seen",
                         "baseline", "current", "z_score", "spike_pct", "pressure_score",
                         "severity", "auto_escalated"}
    assert_test("Incident schema conforms to merged cluster+intelligence spec",
                expected_inc_keys.issubset(set(first_inc.keys())),
                f"Missing keys: {expected_inc_keys - set(first_inc.keys())}")

    # 4. GET /api/incidents/<id>
    inc_id = first_inc.get("incident_id", "INC001")
    res = client.get(f"/api/incidents/{inc_id}")
    assert_test(f"GET /api/incidents/{inc_id} returns 200", res.status_code == 200)
    inc_detail = res.get_json()
    assert_test("Incident details contains complaints list", "complaints" in inc_detail)

    # 5. GET /api/metrics
    res = client.get("/api/metrics")
    assert_test("GET /api/metrics returns 200", res.status_code == 200)
    metrics = res.get_json()
    expected_metric_keys = {"total_complaints", "active_incidents", "emerging_incidents", "auto_escalated_incidents"}
    assert_test("Metrics schema conforms to spec", expected_metric_keys.issubset(set(metrics.keys())),
                f"Missing keys: {expected_metric_keys - set(metrics.keys())}")

    # 6. GET /api/hotspots
    res = client.get("/api/hotspots")
    assert_test("GET /api/hotspots returns 200", res.status_code == 200)
    hotspots = res.get_json()
    assert_test("Hotspots is non-empty list", isinstance(hotspots, list) and len(hotspots) > 0)
    first_hs = hotspots[0] if hotspots else {}
    expected_hs_keys = {"incident_id", "centroid_lat", "centroid_lng", "cluster_radius_km", "severity"}
    assert_test("Hotspots schema conforms to spec", expected_hs_keys.issubset(set(first_hs.keys())),
                f"Missing keys: {expected_hs_keys - set(first_hs.keys())}")

    # 7. GET /api/trends
    res = client.get("/api/trends")
    assert_test("GET /api/trends returns 200", res.status_code == 200)
    trends = res.get_json()
    assert_test("Trends contains daily_totals, by_category, by_locality",
                all(k in trends for k in ["daily_totals", "by_category", "by_locality"]))

    # 8. GET /api/briefing
    res = client.get("/api/briefing")
    assert_test("GET /api/briefing returns 200", res.status_code == 200)
    briefing = res.get_json()
    assert_test("Briefing contains overview and action_items", "overview" in briefing and "action_items" in briefing)

    # 9. GET /api/model-metrics
    res = client.get("/api/model-metrics")
    assert_test("GET /api/model-metrics returns 200", res.status_code == 200)
    model_m = res.get_json()
    assert_test("Model metrics contains baseline_model and comparison_model",
                "baseline_model" in model_m and "comparison_model" in model_m)

    # 10. POST /api/complaints
    post_payload = {
        "complaint_text": "Massive overflow of garbage at market street causing bad odor",
        "latitude": 12.9730,
        "longitude": 77.5960,
        "locality": "Area A"
    }
    res = client.post("/api/complaints", data=json.dumps(post_payload), content_type="application/json")
    assert_test("POST /api/complaints returns 201 Created", res.status_code == 201)
    new_c = res.get_json()
    assert_test("POST generates valid complaint_id", "complaint_id" in new_c and new_c["complaint_id"].startswith("C"))
    assert_test("POST returns predicted_category and confidence",
                "predicted_category" in new_c and "confidence" in new_c)
    assert_test("POST assigns unresolved status", new_c.get("status") == "unresolved")

    print(f"\n--- Summary: {passed}/{total} tests passed ---")
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
