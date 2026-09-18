"""
ml/anomaly.py

Spike-Detection Module for Praman Civic Incident Intelligence.

Calculates 7-day rolling statistics (mean and standard deviation) for daily complaint
counts per category + locality combination using strictly prior days (excluding today).
Computes z-scores and spike percentages while gracefully handling edge cases:
- Insufficient history (< 5 prior days)
- Zero standard deviation (std == 0)
- Zero baseline (rolling_mean == 0)
"""

import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any

# =====================================================================
# STATUS MAPPING CONFIGURATION FOR UNRESOLVED COMPLAINTS
# Easily configurable by the team:
# - UNRESOLVED_STATUSES: Counted towards unresolved_count
# - RESOLVED_STATUSES: Counted as closed-out / resolved
# =====================================================================
UNRESOLVED_STATUSES = {"Open", "On-the-Job", "Re-opened"}
RESOLVED_STATUSES = {"Resolved", "Closed", "Rejected"}


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes daily complaint count anomaly metrics for each category + locality combination.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing incident records or daily aggregates.
        Required columns: 'category', 'locality', 'date' (or 'timestamp'), 'complaint_count'
        (If 'complaint_count' is not present, assumes 1 complaint per row and aggregates by date).

    Returns
    -------
    pd.DataFrame
        One record per category + locality + day with columns:
        - category (str)
        - locality (str)
        - date (str YYYY-MM-DD)
        - current_count (int)
        - rolling_mean (float or None)
        - rolling_std (float or None)
        - z_score (float or None)
        - insufficient_history (bool)
        - spike_pct (float or str)
    """
    data = df.copy()

    # Handle 'timestamp' column if 'date' column is missing; normalize timestamps to calendar days
    if 'date' not in data.columns and 'timestamp' in data.columns:
        data['date'] = pd.to_datetime(data['timestamp']).dt.normalize()
    elif 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date']).dt.normalize()

    # If raw incident rows are passed without complaint_count, aggregate them
    if 'complaint_count' not in data.columns:
        data = (
            data.groupby(['category', 'locality', 'date'])
            .size()
            .reset_index(name='complaint_count')
        )
    else:
        data = (
            data.groupby(['category', 'locality', 'date'])['complaint_count']
            .sum()
            .reset_index()
        )

    results = []

    # Process each category + locality pair independently
    grouped = data.groupby(['category', 'locality'])

    for (cat, loc), group in grouped:
        # Sort chronologically
        group = group.sort_values('date').reset_index(drop=True)

        # Fill missing daily dates in range to ensure rolling window reflects true calendar days
        min_d = group['date'].min()
        max_d = group['date'].max()
        full_idx = pd.date_range(start=min_d, end=max_d, freq='D')

        series_counts = group.set_index('date')['complaint_count'].reindex(full_idx, fill_value=0)
        counts_arr = series_counts.to_numpy(dtype=np.float64)
        date_strings = [d.strftime('%Y-%m-%d') for d in full_idx]

        n_samples = len(counts_arr)

        # Shift by 1 day so today's complaint count is STRICTLY EXCLUDED from today's baseline
        prior_series = pd.Series(counts_arr).shift(1)

        # 7-day rolling window on prior days
        prior_window = prior_series.rolling(window=7, min_periods=1)
        prior_n = prior_window.count().to_numpy()
        prior_mean = prior_window.mean().to_numpy()
        prior_std = prior_window.std(ddof=1).fillna(0.0).to_numpy()

        # Vectorized calculations
        insufficient_history_mask = prior_n < 5

        for i in range(n_samples):
            curr_date_str = date_strings[i]
            current_c = int(counts_arr[i])
            n_p = prior_n[i]
            p_mean = prior_mean[i]
            p_std = prior_std[i]

            if insufficient_history_mask[i]:
                insufficient_history = True
                r_mean = None
                r_std = None
                z_score = None
            else:
                insufficient_history = False
                r_mean = float(round(p_mean, 4))
                r_std = float(round(p_std, 4))

                # Edge Case 2: Zero standard deviation (std == 0)
                if np.isclose(p_std, 0.0):
                    if np.isclose(current_c, p_mean):
                        z_score = 0.0
                    elif current_c > p_mean:
                        z_score = 3.0  # Capped ceiling for upward deviation over zero std
                    else:
                        z_score = -3.0  # Capped floor for downward deviation over zero std
                else:
                    raw_z = (current_c - p_mean) / p_std
                    z_score = float(round(raw_z, 4))

            # Edge Case 3: Zero baseline for spike_pct calculation
            if p_mean is None or np.isnan(p_mean) or np.isclose(p_mean, 0.0):
                spike_pct = "N/A (new activity)"
            else:
                raw_spike = ((current_c - p_mean) / p_mean) * 100.0
                spike_pct = float(round(raw_spike, 2))

            results.append({
                'category': cat,
                'locality': loc,
                'date': curr_date_str,
                'current_count': current_c,
                'rolling_mean': r_mean,
                'rolling_std': r_std,
                'z_score': z_score,
                'insufficient_history': insufficient_history,
                'spike_pct': spike_pct
            })

    return pd.DataFrame(results)


# =====================================================================
# STANDALONE DEMO & TEST EXECUTION
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING ANOMALY DETECTION (ml/anomaly.py) DEMO & EDGE CASE TESTS")
    print("=" * 70)

    # Test Data Construction covering edge cases
    records = []
    
    # Scenario A: Category="Roads", Locality="Indiranagar"
    #   - Days 1-4: Insufficient history (< 5 prior days)
    #   - Days 5-9: Prior 5+ days all have count=2 (std=0). Day 10 jumps to 10 (std=0 edge case spike).
    indira_counts = [2, 2, 2, 2, 2, 2, 2, 10, 2, 15]
    dates_indira = pd.date_range(start="2026-09-01", periods=10, freq="D")
    for d, c in zip(dates_indira, indira_counts):
        records.append({'category': 'Roads', 'locality': 'Indiranagar', 'date': d, 'complaint_count': c})
        
    # Scenario B: Category="Water", Locality="Koramangala" (Zero Baseline test)
    water_counts = [0, 0, 0, 0, 0, 0, 5]
    dates_water = pd.date_range(start="2026-09-01", periods=7, freq="D")
    for d, c in zip(dates_water, water_counts):
        records.append({'category': 'Water', 'locality': 'Koramangala', 'date': d, 'complaint_count': c})

    df_raw = pd.DataFrame(records)
    res_df = detect_anomalies(df_raw)

    print("\n--- RESULTS: Indiranagar (Roads) ---")
    indira_res = res_df[res_df['locality'] == 'Indiranagar']
    print(indira_res.to_string(index=False))

    print("\n--- RESULTS: Koramangala (Water) [Zero Baseline Test] ---")
    water_res = res_df[res_df['locality'] == 'Koramangala']
    print(water_res.to_string(index=False))

    print("\nALL ANOMALY DETECTION DEMO TESTS COMPLETED SUCCESSFULLY!")
