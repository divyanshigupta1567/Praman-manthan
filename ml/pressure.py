"""
ml/pressure.py

Pressure-Scoring Module for Praman Civic Incident Intelligence.

Calculates composite pressure scores and assigns severity bands for incident clusters
based on four normalized sub-scores:
- Spike Score (40% weight): Z-score normalized against 3.0 standard deviations (with volume dampener for sparse data)
- Size Score (30% weight): Complaint volume normalized against baseline of 30 complaints
- Duration Score (20% weight): Cluster age normalized against 72 hours (3 days)
- Unresolved Score (10% weight): Ratio of unresolved complaints to total complaints

When historical Z-score baseline is unavailable (insufficient history / zero baseline),
a bounded `new_activity_score` is computed based on size and unresolved ratio and substituted
into the 40% slot to ensure significant new incidents are not falsely marked as Normal.

Bands:
- 0 to 59: Normal (auto_escalated = False)
- 60 to 79: Emerging (auto_escalated = False)
- 80 to 100: High Pressure (auto_escalated = True)
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, List

# =====================================================================
# STATUS MAPPING CONFIGURATION FOR UNRESOLVED COMPLAINTS
# Easily configurable by the team:
# - UNRESOLVED_STATUSES: Counted towards unresolved_count
# - RESOLVED_STATUSES: Counted as closed-out / resolved
# =====================================================================
UNRESOLVED_STATUSES = {"Open", "On-the-Job", "Re-opened"}
RESOLVED_STATUSES = {"Resolved", "Closed", "Rejected"}


def calculate_pressure_score(cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the composite pressure score, severity band, and escalation status for an incident cluster.

    Parameters
    ----------
    cluster : dict
        Cluster object containing:
        - complaint_count (int)
        - hours_since_first_seen (float)
        - unresolved_count (int)
        - z_score (float or None)
        - spike_pct (str or float, optional)

    Returns
    -------
    dict
        Copy of input cluster dictionary updated with:
        - spike_score (float 0-100)
        - size_score (float 0-100)
        - duration_score (float 0-100)
        - unresolved_score (float 0-100)
        - new_activity_score (float or None)
        - pressure_score (float 0-100)
        - band (str: "Normal", "Emerging", "High Pressure")
        - auto_escalated (bool)
        - spike_pct (str or float)
        - explanation (str)
    """
    res = dict(cluster)

    # -------------------------------------------------------------------------
    # 0. INPUT SANITIZATION & CLAMPING
    # -------------------------------------------------------------------------
    raw_count = res.get('complaint_count', 0)
    complaint_count = max(0, int(raw_count) if raw_count is not None and not pd.isna(raw_count) else 0)

    raw_hours = res.get('hours_since_first_seen', 0.0)
    hours_since_first_seen = max(0.0, float(raw_hours) if raw_hours is not None and not pd.isna(raw_hours) else 0.0)

    raw_unresolved = res.get('unresolved_count', 0)
    unresolved_count = max(0, int(raw_unresolved) if raw_unresolved is not None and not pd.isna(raw_unresolved) else 0)
    
    # Clamp unresolved_count to not exceed total complaint_count
    if complaint_count > 0:
        unresolved_count = min(complaint_count, unresolved_count)
    else:
        unresolved_count = 0

    z_score = res.get('z_score', None)
    if z_score is not None and pd.isna(z_score):
        z_score = None

    spike_pct = res.get('spike_pct', "N/A (new activity)")

    # -------------------------------------------------------------------------
    # 1. SUB-SCORE CALCULATIONS (0-100 Bounded)
    # -------------------------------------------------------------------------
    
    # Size Sub-Score (30% weight, 0-100 scale: maxed at 30 complaints)
    size_score = min(100.0, max(0.0, (complaint_count / 30.0) * 100.0))

    # Duration Sub-Score (20% weight, 0-100 scale: maxed at 72 hours)
    duration_score = min(100.0, max(0.0, (hours_since_first_seen / 72.0) * 100.0))

    # Unresolved Sub-Score (10% weight, 0-100 scale)
    if complaint_count > 0:
        unresolved_ratio = (unresolved_count / complaint_count) * 100.0
        unresolved_score = min(100.0, max(0.0, unresolved_ratio))
    else:
        unresolved_score = 0.0

    # -------------------------------------------------------------------------
    # 2. SPIKE SCORE & NEW ACTIVITY HANDLING STRATEGY
    # -------------------------------------------------------------------------
    new_activity_score = None

    if z_score is None:
        # STRATEGY FOR NEW ACTIVITY / UNAVAILABLE HISTORICAL BASELINE:
        # When z_score is unavailable, compute a bounded new_activity_score derived from
        # complaint size and unresolved ratio. Substitute this score into the 40% slot.
        new_act_raw = 0.6 * size_score + 0.4 * unresolved_score
        new_activity_score = float(round(min(100.0, max(0.0, new_act_raw)), 2))
        spike_score = new_activity_score
    else:
        # SPARSE DATA & BASELINE VOLUME STABILIZER:
        # To prevent small complaint counts (<5) from triggering High Pressure solely due to a large Z-score,
        # scale the Z-score contribution by a volume dampener: min(1.0, complaint_count / 5.0)
        volume_dampener = min(1.0, complaint_count / 5.0) if complaint_count > 0 else 0.0
        raw_z_spike = min(100.0, max(0.0, (float(z_score) / 3.0) * 100.0))
        spike_score = raw_z_spike * volume_dampener

    spike_score = float(round(spike_score, 2))
    size_score = float(round(size_score, 2))
    duration_score = float(round(duration_score, 2))
    unresolved_score = float(round(unresolved_score, 2))

    # -------------------------------------------------------------------------
    # 3. COMPOSITE PRESSURE SCORE CALCULATION
    # Formula: 40% Spike (or New Activity) + 30% Size + 20% Duration + 10% Unresolved
    # -------------------------------------------------------------------------
    pressure_score = (
        0.4 * spike_score +
        0.3 * size_score +
        0.2 * duration_score +
        0.1 * unresolved_score
    )

    pressure_score_rounded = float(round(pressure_score, 2))

    # -------------------------------------------------------------------------
    # 4. SEVERITY BANDS & AUTO-ESCALATION
    # -------------------------------------------------------------------------
    if pressure_score_rounded >= 80.0:
        band = "High Pressure"
        auto_escalated = True
    elif pressure_score_rounded >= 60.0:
        band = "Emerging"
        auto_escalated = False
    else:
        band = "Normal"
        auto_escalated = False

    # -------------------------------------------------------------------------
    # 5. DETERMINISTIC EXPLAINABILITY GENERATION
    # -------------------------------------------------------------------------
    if auto_escalated:
        explanation = (
            f"HIGH PRESSURE ESCALATION: {complaint_count} complaints with "
            f"{unresolved_score:.1f}% unresolved ratio and high severity indicators."
        )
    elif new_activity_score is not None:
        explanation = (
            f"NEW ACTIVITY DETECTED: {complaint_count} complaints ({unresolved_score:.1f}% unresolved) "
            f"with no prior historical baseline (New Activity Score: {new_activity_score:.1f})."
        )
    elif band == "Emerging":
        explanation = (
            f"EMERGING CONCERN: Moderate spike (spike_score={spike_score:.1f}) and volume "
            f"({complaint_count} complaints, {hours_since_first_seen:.1f} hrs active)."
        )
    else:
        explanation = (
            f"NORMAL ACTIVITY: Low volume/spike intensity (pressure_score={pressure_score_rounded:.1f})."
        )

    # Attach output attributes
    res.update({
        'complaint_count': complaint_count,
        'hours_since_first_seen': hours_since_first_seen,
        'unresolved_count': unresolved_count,
        'spike_score': spike_score,
        'size_score': size_score,
        'duration_score': duration_score,
        'unresolved_score': unresolved_score,
        'new_activity_score': new_activity_score,
        'pressure_score': pressure_score_rounded,
        'band': band,
        'auto_escalated': auto_escalated,
        'spike_pct': spike_pct,
        'explanation': explanation
    })

    return res


def calculate_pressure_scores_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Batch calculates pressure scores for a DataFrame of clusters.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing cluster objects as rows.

    Returns
    -------
    pd.DataFrame
        DataFrame with added pressure scoring metrics, bands, and explanations.
    """
    scored_records = [calculate_pressure_score(row.to_dict()) for _, row in df.iterrows()]
    return pd.DataFrame(scored_records)


# =====================================================================
# STANDALONE DEMO & TEST EXECUTION
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING PRESSURE SCORING (ml/pressure.py) DEMO & TEST SUITE")
    print("=" * 70)

    # Test cases
    c_normal = {
        'complaint_count': 5,
        'hours_since_first_seen': 12.0,
        'unresolved_count': 2,
        'z_score': 0.5,
        'spike_pct': 15.0
    }

    c_new = {
        'complaint_count': 30,
        'hours_since_first_seen': 2.0,
        'unresolved_count': 30,
        'z_score': None,
        'spike_pct': "N/A (new activity)"
    }

    res_normal = calculate_pressure_score(c_normal)
    res_new = calculate_pressure_score(c_new)

    print("\nNormal Cluster Result:")
    print(f"  pressure_score={res_normal['pressure_score']} | band='{res_normal['band']}' | explanation='{res_normal['explanation']}'")

    print("\nLarge New Activity Result (Day 1 - 30 complaints):")
    print(f"  new_activity_score={res_new['new_activity_score']} | pressure_score={res_new['pressure_score']} | band='{res_new['band']}' | auto_escalated={res_new['auto_escalated']}")
    print(f"  explanation='{res_new['explanation']}'")

    assert res_new['band'] == "High Pressure" and res_new['auto_escalated'] == True, "New activity 30 complaints should escalate to High Pressure"
    print("\nALL PRESSURE SCORING DEMO TESTS PASSED SUCCESSFULLY!")
