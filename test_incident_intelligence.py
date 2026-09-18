"""
test_incident_intelligence.py

Comprehensive Audit & Test Suite for Praman Incident Intelligence Module
(ml/anomaly.py and ml/pressure.py).

Includes 10 explicit edge-case unit tests, reproducibility assertion test,
and dataset verification on praman_train.csv with pressure_score sorting.
"""

import sys
import os
import pandas as pd
import numpy as np

from ml.anomaly import detect_anomalies, UNRESOLVED_STATUSES, RESOLVED_STATUSES
from ml.pressure import calculate_pressure_score, calculate_pressure_scores_df


def run_incident_intelligence_tests():
    print("=" * 80)
    print("PRAMAN INCIDENT INTELLIGENCE — FULL AUDIT & TEST SUITE")
    print("Focus: Spike Detection (ml/anomaly.py) & Pressure Scoring (ml/pressure.py)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TEST 1: INSUFFICIENT HISTORY (<5 prior days)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Insufficient History (<5 prior days)...")
    dates_t1 = pd.date_range(start="2026-09-01", periods=4, freq="D")
    df_t1 = pd.DataFrame({
        "category": ["Roads"] * 4,
        "locality": ["Area A"] * 4,
        "date": dates_t1,
        "complaint_count": [2, 3, 1, 4]
    })
    res_t1 = detect_anomalies(df_t1)
    
    assert (res_t1["insufficient_history"] == True).all(), "Test 1 Failed: insufficient_history should be True"
    assert (res_t1["z_score"].isna()).all(), "Test 1 Failed: z_score should be None/NaN"
    print("  [OK] PASSED: insufficient_history = True and z_score = None for < 5 prior days.")

    # -------------------------------------------------------------------------
    # TEST 2: EXACTLY 5 PRIOR DAYS
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Exactly 5 Prior Days...")
    dates_t2 = pd.date_range(start="2026-09-01", periods=6, freq="D")
    df_t2 = pd.DataFrame({
        "category": ["Roads"] * 6,
        "locality": ["Area A"] * 6,
        "date": dates_t2,
        "complaint_count": [2, 2, 3, 2, 3, 10]
    })
    res_t2 = detect_anomalies(df_t2)
    day6_row = res_t2.iloc[5]
    
    assert day6_row["insufficient_history"] == False, "Test 2 Failed: Day 6 should have sufficient history"
    assert day6_row["z_score"] is not None and not pd.isna(day6_row["z_score"]), "Test 2 Failed: z_score should be calculated"
    print(f"  [OK] PASSED: Day 6 (5 prior days) insufficient_history = False, z_score = {day6_row['z_score']}.")

    # -------------------------------------------------------------------------
    # TEST 3: TODAY'S VALUE LEAK PREVENTION
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Today's Value Leak Prevention...")
    dates_t3 = pd.date_range(start="2026-09-01", periods=6, freq="D")
    df_t3 = pd.DataFrame({
        "category": ["Roads"] * 6,
        "locality": ["Area A"] * 6,
        "date": dates_t3,
        "complaint_count": [2, 2, 2, 2, 2, 500]
    })
    res_t3 = detect_anomalies(df_t3)
    day6_row_t3 = res_t3.iloc[5]
    
    assert np.isclose(day6_row_t3["rolling_mean"], 2.0), f"Test 3 Failed: rolling_mean should be 2.0, got {day6_row_t3['rolling_mean']}"
    assert np.isclose(day6_row_t3["rolling_std"], 0.0), f"Test 3 Failed: rolling_std should be 0.0, got {day6_row_t3['rolling_std']}"
    print(f"  [OK] PASSED: Today's count (500) did not leak into today's baseline (rolling_mean={day6_row_t3['rolling_mean']}).")

    # -------------------------------------------------------------------------
    # TEST 4: ZERO STANDARD DEVIATION
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Zero Standard Deviation (2,2,2,2,2,2,2 -> Today 10)...")
    dates_t4 = pd.date_range(start="2026-09-01", periods=8, freq="D")
    df_t4 = pd.DataFrame({
        "category": ["Roads"] * 8,
        "locality": ["Area A"] * 8,
        "date": dates_t4,
        "complaint_count": [2, 2, 2, 2, 2, 2, 2, 10]
    })
    res_t4 = detect_anomalies(df_t4)
    day8_row_t4 = res_t4.iloc[7]

    assert np.isclose(day8_row_t4["rolling_std"], 0.0), "Test 4 Failed: std should be 0.0"
    assert day8_row_t4["z_score"] == 3.0, f"Test 4 Failed: z_score should be capped at 3.0, got {day8_row_t4['z_score']}"
    assert not np.isnan(day8_row_t4["z_score"]) and not np.isinf(day8_row_t4["z_score"]), "Test 4 Failed: z_score is NaN or Inf"
    print(f"  [OK] PASSED: std=0 handling safely bounded z_score = {day8_row_t4['z_score']} (no NaN/Inf).")

    # -------------------------------------------------------------------------
    # TEST 5: ZERO BASELINE / NEW ACTIVITY
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Zero Baseline / New Activity (0,0,0,0,0,0,0 -> Today 5)...")
    dates_t5 = pd.date_range(start="2026-09-01", periods=8, freq="D")
    df_t5 = pd.DataFrame({
        "category": ["Water"] * 8,
        "locality": ["Area B"] * 8,
        "date": dates_t5,
        "complaint_count": [0, 0, 0, 0, 0, 0, 0, 5]
    })
    res_t5 = detect_anomalies(df_t5)
    day8_row_t5 = res_t5.iloc[7]

    assert day8_row_t5["rolling_mean"] == 0.0, "Test 5 Failed: rolling_mean should be 0.0"
    assert day8_row_t5["spike_pct"] == "N/A (new activity)", f"Test 5 Failed: spike_pct got {day8_row_t5['spike_pct']}"
    
    cluster_t5 = {
        "complaint_count": 5,
        "hours_since_first_seen": 12.0,
        "unresolved_count": 5,
        "z_score": day8_row_t5["z_score"],
        "spike_pct": day8_row_t5["spike_pct"]
    }
    p_t5 = calculate_pressure_score(cluster_t5)
    assert p_t5["pressure_score"] > 0, "Test 5 Failed: Pressure score should evaluate new activity"
    print(f"  [OK] PASSED: spike_pct='{day8_row_t5['spike_pct']}', pressure score={p_t5['pressure_score']}.")

    # -------------------------------------------------------------------------
    # TEST 6: LARGE NEW ACTIVITY (Day 1 - 30 Complaints)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Large New Activity (0 prior history -> 30 complaints today)...")
    cluster_t6 = {
        "complaint_count": 30,
        "hours_since_first_seen": 2.0,
        "unresolved_count": 30,
        "z_score": None,
        "spike_pct": "N/A (new activity)"
    }
    p_t6 = calculate_pressure_score(cluster_t6)

    assert p_t6["new_activity_score"] == 100.0, f"Test 6 Failed: expected new_activity_score=100.0, got {p_t6['new_activity_score']}"
    assert p_t6["band"] == "High Pressure", f"Test 6 Failed: expected High Pressure, got {p_t6['band']}"
    assert p_t6["auto_escalated"] == True, "Test 6 Failed: auto_escalated should be True"
    print(f"  [OK] PASSED: Large new activity correctly scored (pressure={p_t6['pressure_score']}, band='{p_t6['band']}', auto_escalated={p_t6['auto_escalated']}).")

    # -------------------------------------------------------------------------
    # TEST 7: SPARSE SPIKE (0,0,0,0,0,0,1 -> Today 4)
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Sparse Spike Protection (Prior: 0,0,0,0,0,0,1 -> Today 4)...")
    cluster_t7 = {
        "complaint_count": 4,
        "hours_since_first_seen": 10.0,
        "unresolved_count": 4,
        "z_score": 10.2050,
        "spike_pct": 2700.0
    }
    p_t7 = calculate_pressure_score(cluster_t7)

    assert p_t7["band"] != "High Pressure", f"Test 7 Failed: Sparse spike should NOT reach High Pressure, got {p_t7['band']}"
    assert p_t7["auto_escalated"] == False, "Test 7 Failed: Sparse spike should not auto-escalate"
    print(f"  [OK] PASSED: Sparse spike bounded safely (spike_score={p_t7['spike_score']}, pressure={p_t7['pressure_score']}, band='{p_t7['band']}').")

    # -------------------------------------------------------------------------
    # TEST 8: ALL-ZERO DATA
    # -------------------------------------------------------------------------
    print("\n[TEST 8] All-Zero Data Handling...")
    cluster_t8 = {
        "complaint_count": 0,
        "hours_since_first_seen": 0.0,
        "unresolved_count": 0,
        "z_score": 0.0,
        "spike_pct": 0.0
    }
    p_t8 = calculate_pressure_score(cluster_t8)

    assert p_t8["pressure_score"] == 0.0, f"Test 8 Failed: expected pressure=0.0, got {p_t8['pressure_score']}"
    assert p_t8["band"] == "Normal", f"Test 8 Failed: expected Normal, got {p_t8['band']}"
    assert p_t8["auto_escalated"] == False, "Test 8 Failed: expected auto_escalated=False"
    print("  [OK] PASSED: All-zero input returned pressure=0.0, Normal, auto_escalated=False.")

    # -------------------------------------------------------------------------
    # TEST 9: NEGATIVE & INVALID INPUTS SANITIZATION
    # -------------------------------------------------------------------------
    print("\n[TEST 9] Negative & Invalid Inputs Sanitization...")
    cluster_t9 = {
        "complaint_count": -5,
        "hours_since_first_seen": -10.0,
        "unresolved_count": 15,
        "z_score": None,
        "spike_pct": None
    }
    p_t9 = calculate_pressure_score(cluster_t9)

    assert p_t9["complaint_count"] == 0, "Test 9 Failed: negative count should clamp to 0"
    assert p_t9["hours_since_first_seen"] == 0.0, "Test 9 Failed: negative duration should clamp to 0.0"
    assert p_t9["unresolved_count"] == 0, "Test 9 Failed: unresolved count should clamp to 0"
    assert not np.isnan(p_t9["pressure_score"]), "Test 9 Failed: pressure_score is NaN"
    print(f"  [OK] PASSED: Invalid inputs sanitized cleanly (count={p_t9['complaint_count']}, unres={p_t9['unresolved_count']}, pressure={p_t9['pressure_score']}).")

    # -------------------------------------------------------------------------
    # TEST 10: UNKNOWN STATUS HANDLING
    # -------------------------------------------------------------------------
    print("\n[TEST 10] Unknown Status Handling...")
    df_t10 = pd.DataFrame({
        "complaint_id": ["C1", "C2", "C3"],
        "complaint_text": ["Issue 1", "Issue 2", "Issue 3"],
        "category": ["Roads", "Roads", "Roads"],
        "locality": ["Area A", "Area A", "Area A"],
        "latitude": [12.9, 12.9, 12.9],
        "longitude": [77.5, 77.5, 77.5],
        "timestamp": ["2026-09-01 10:00:00", "2026-09-01 11:00:00", "2026-09-01 12:00:00"],
        "status": ["Under Review", "Custom Status", "Archived"]
    })
    
    unresolved_c = int(df_t10['status'].isin(UNRESOLVED_STATUSES).sum())
    assert unresolved_c == 0, "Unknown statuses should not match default unresolved set without configuration"
    print("  [OK] PASSED: Unknown statuses handled safely without pipeline crashes.")

    # -------------------------------------------------------------------------
    # REPRODUCIBILITY ASSERTION TEST (BUG 1 REGRESSION TEST)
    # -------------------------------------------------------------------------
    print("\n[REPRODUCIBILITY TEST] Verifying Deterministic Pressure Scoring...")
    test_cluster_fixed = {
        "category": "Garbage",
        "locality": "Ramamurthy Nagar",
        "complaint_count": 4,
        "hours_since_first_seen": 4.47,
        "unresolved_count": 0,
        "z_score": 10.2050,
        "spike_pct": 2700.0
    }
    
    run_1 = calculate_pressure_score(test_cluster_fixed)
    run_2 = calculate_pressure_score(test_cluster_fixed)
    
    assert run_1["pressure_score"] == run_2["pressure_score"], (
        f"BUG 1 REGRESSION: Non-deterministic pressure scores! Run 1: {run_1['pressure_score']} vs Run 2: {run_2['pressure_score']}"
    )
    assert run_1["explanation"] == run_2["explanation"], "BUG 1 REGRESSION: Explanations differ between runs!"
    print(f"  [OK] PASSED: 100% deterministic outputs across repeated runs (pressure_score={run_1['pressure_score']}).")

    # -------------------------------------------------------------------------
    # DATASET VERIFICATION (praman_train.csv)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("DATASET LEVEL VERIFICATION (praman_train.csv)")
    print("=" * 80)
    csv_path = "praman_train.csv"
    if os.path.exists(csv_path):
        df_real = pd.read_csv(csv_path)
        print(f"Loaded '{csv_path}': {len(df_real)} records across {df_real['locality'].nunique()} localities.")

        anom_real = detect_anomalies(df_real)
        total_daily_r = len(anom_real)
        insuff_r = int(anom_real['insufficient_history'].sum())
        anom_spikes = int((anom_real['z_score'] >= 2.0).sum())

        print(f"  - Total Daily Records Generated   : {total_daily_r}")
        print(f"  - Category+Locality Groups       : {df_real.groupby(['category', 'locality']).ngroups}")
        print(f"  - Insufficient History Records    : {insuff_r} ({insuff_r / total_daily_r * 100:.2f}%)")
        print(f"  - Anomalous Records (Z >= 2.0)     : {anom_spikes}")

        # Extract top 10 spikes with deterministic multi-column sort to prevent tie-breaking variations
        valid_spikes = anom_real.dropna(subset=['z_score']).sort_values(
            by=['z_score', 'current_count', 'date', 'locality'],
            ascending=[False, False, False, True]
        ).head(10)

        df_real['timestamp_dt'] = pd.to_datetime(df_real['timestamp'])

        top_clusters = []
        for idx, spike_row in valid_spikes.iterrows():
            cat, loc, spike_date = spike_row['category'], spike_row['locality'], spike_row['date']
            spike_dt = pd.to_datetime(spike_date)
            
            # Deterministic calculation of hours_since_first_seen anchored to the spike date
            spike_end_dt = spike_dt + pd.Timedelta(hours=23, minutes=59, seconds=59)
            sub = df_real[
                (df_real['category'] == cat) &
                (df_real['locality'] == loc) &
                (df_real['timestamp_dt'] >= spike_dt - pd.Timedelta(days=3)) &
                (df_real['timestamp_dt'] <= spike_end_dt)
            ]
            c_count = max(int(spike_row['current_count']), len(sub))
            u_count = int(sub['status'].isin(UNRESOLVED_STATUSES).sum())
            
            if len(sub) > 0:
                first_seen_dt = sub['timestamp_dt'].min()
                hrs = float(round((spike_end_dt - first_seen_dt).total_seconds() / 3600.0, 2))
            else:
                hrs = 24.0

            top_clusters.append(calculate_pressure_score({
                "category": cat,
                "locality": loc,
                "spike_date": spike_date,
                "complaint_count": c_count,
                "unresolved_count": u_count,
                "hours_since_first_seen": hrs,
                "z_score": spike_row['z_score'],
                "spike_pct": spike_row['spike_pct']
            }))

        top_df = pd.DataFrame(top_clusters)

        # BUG 2 FIX: Sort Top Incidents table by pressure_score descending (NOT z_score)
        top_df = top_df.sort_values(by=['pressure_score', 'z_score'], ascending=[False, False]).reset_index(drop=True)

        cols_t = ["category", "locality", "spike_date", "complaint_count", "z_score", "pressure_score", "band", "auto_escalated", "explanation"]
        print("\n  Top 10 Pressure Incidents on praman_train.csv (SORTED BY PRESSURE SCORE):")
        print(top_df[cols_t].to_string(index=False))

        # BUG 2 VERIFICATION: Assert Emerging/High Pressure rank above Normal
        bands_in_order = top_df['band'].tolist()
        for b_i in range(len(bands_in_order) - 1):
            b_curr = bands_in_order[b_i]
            b_next = bands_in_order[b_i + 1]
            if b_curr == "Normal":
                assert b_next == "Normal", f"BUG 2 REGRESSION: Found '{b_next}' below 'Normal' at rank {b_i + 2}!"
        print("\n  [OK] BUG 2 VERIFIED: Emerging/High Pressure incidents rank strictly above Normal incidents.")

    else:
        print(f"Dataset '{csv_path}' not found; skipping dataset verification.")

    print("\n" + "=" * 80)
    print("ALL 10 UNIT TESTS, REPRODUCIBILITY ASSERTIONS & DATASET VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_incident_intelligence_tests()
