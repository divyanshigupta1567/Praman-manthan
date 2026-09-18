"""Synthetic Citizen Complaint Data Generator for Praman.

Generates realistic civic complaints across categories with slot-based templates,
scripted spikes, and near-duplicate reports.
"""

import argparse
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd


CATEGORIES: List[str] = [
    "Pothole",
    "Garbage",
    "Water Leakage",
    "Streetlight",
    "Sewage",
    "Traffic Hazard",
]

LOCALITIES: Dict[str, Tuple[float, float]] = {
    "Area A": (12.9716, 77.5946),
    "Area B": (12.9352, 77.6245),
    "Area C": (12.9850, 77.6050),
    "Area D": (12.9121, 77.6446),
    "Area E": (13.0033, 77.5645),
    "Area F": (12.9560, 77.7010),
    "Area G": (12.9249, 77.5562),
    "Area H": (13.0280, 77.5409),
}

STATUSES: List[str] = ["Open", "In Progress", "Resolved", "Pending Verification"]
STATUS_WEIGHTS: List[float] = [0.45, 0.25, 0.20, 0.10]

SLOTS: Dict[str, List[str]] = {
    "road_type": [
        "main road", "service lane", "cross road", "highway junction", "residential street",
        "inner lane", "arterial road", "market lane", "bus route"
    ],
    "severity_pothole": [
        "deep crater", "massive pothole", "cluster of sharp potholes", "dangerous surface depression",
        "uneven broken tarmac", "large cave-in"
    ],
    "pothole_hazard": [
        "causing two-wheelers to skid", "severe accident risk for daily commuters",
        "heavy vehicle damage", "traffic slowdown during peak hours", "danger to school buses"
    ],
    "garbage_type": [
        "pile of household waste", "overflowing open dumpster", "scattered plastic debris",
        "uncollected commercial garbage", "rotten vegetable and food waste", "construction and demolition debris"
    ],
    "garbage_impact": [
        "emitting intolerable foul odor", "attracting stray dogs and pests", "blocking pedestrian footpath",
        "posing health hazards to residents", "choking rainwater roadside gutters"
    ],
    "water_source": [
        "municipal supply pipeline", "underground drinking water line", "broken roadside valve",
        "overhead connection pipe", "damaged fire hydrant pipe"
    ],
    "water_impact": [
        "wasting thousands of liters of clean water", "flooding the main thoroughfare",
        "causing low pressure in neighborhood homes", "creating heavy mud and waterlogging",
        "weakening road foundation"
    ],
    "light_problem": [
        "completely unlit for several days", "flickering constantly", "damaged pole after storm",
        "broken bulb and hanging wires", "dim and non-functional"
    ],
    "light_impact": [
        "making the street unsafe for women at night", "pitch darkness increasing burglary risk",
        "severe visibility issues for drivers", "unsafe for evening pedestrians"
    ],
    "sewage_problem": [
        "overflowing manhole", "blocked sewage drain", "black toxic wastewater backup",
        "stagnant sewer runoff", "broken underground drainage pipe"
    ],
    "sewage_impact": [
        "spreading foul stench throughout the locality", "entering ground floor residential compounds",
        "extreme risk of dengue and waterborne diseases", "inundating the entire lane"
    ],
    "traffic_hazard": [
        "fallen tree branches blocking lanes", "broken road divider jutting onto carriageway",
        "unmarked construction barrier", "blind turn blocked by unauthorized parked trucks",
        "hanging overhead cable across traffic", "defective non-functional traffic signal"
    ],
    "urgency": [
        "Please fix immediately.", "Kindly resolve on urgent priority.", "Action required before a major accident occurs.",
        "Request the municipal team to address this today.", "Residents have been suffering for days."
    ],
    "landmark": [
        "near the metro pillar", "opposite the community park", "close to the primary school",
        "behind the grocery supermarket", "near the government clinic", "at the 3rd cross junction",
        "beside the public library", "adjacent to the bus stop"
    ],
}

TEMPLATES: Dict[str, List[str]] = {
    "Pothole": [
        "A {severity_pothole} on {road_type} {landmark} is {pothole_hazard}. {urgency}",
        "Dangerous road condition: {severity_pothole} observed {landmark} along the {road_type}. It is {pothole_hazard}.",
        "Motorists facing hazard due to {severity_pothole} on {road_type}. {urgency}",
        "Report of {severity_pothole} {landmark}. It is {pothole_hazard}. Please inspect road quality.",
        "Deep crater formed on {road_type} {landmark}. {pothole_hazard}. {urgency}",
    ],
    "Garbage": [
        "Huge {garbage_type} has piled up {landmark}. It is {garbage_impact}. {urgency}",
        "Sanitation failure: {garbage_type} dumped along {road_type} {landmark}, {garbage_impact}.",
        "Unattended {garbage_type} {landmark}. Not cleared for multiple days and is {garbage_impact}. {urgency}",
        "Public health concern: {garbage_type} {landmark} is {garbage_impact}. Kindly arrange garbage truck.",
        "Noticeable {garbage_type} left open on {road_type}. {garbage_impact}. {urgency}",
    ],
    "Water Leakage": [
        "Severe {water_source} leakage {landmark}, {water_impact}. {urgency}",
        "Continuous leak from {water_source} on {road_type} {landmark}. It is {water_impact}.",
        "Clean drinking water wastage: {water_source} burst {landmark} and is {water_impact}. {urgency}",
        "Urgent repair needed: {water_source} leaking heavily {landmark}. {water_impact}.",
        "Water overflowing onto {road_type} from damaged {water_source} {landmark}. {water_impact}. {urgency}",
    ],
    "Streetlight": [
        "The streetlight {landmark} has been {light_problem}, {light_impact}. {urgency}",
        "No lighting on {road_type}: Streetlights are {light_problem} {landmark}. {light_impact}.",
        "Dark street safety concern: Streetlight {landmark} is {light_problem}. {light_impact}. {urgency}",
        "Faulty street lamp pole {landmark} is {light_problem}. {urgency}",
        "Illumination needed on {road_type} {landmark}. Lamps are {light_problem}, {light_impact}.",
    ],
    "Sewage": [
        "Severe drainage issue: {sewage_problem} {landmark}, {sewage_impact}. {urgency}",
        "Filthy wastewater flooding {road_type} due to {sewage_problem} {landmark}. {sewage_impact}.",
        "Open {sewage_problem} {landmark} is {sewage_impact}. Please deploy sewage suction vehicle immediately.",
        "Manhole backing up: {sewage_problem} on {road_type} {landmark}, {sewage_impact}. {urgency}",
        "Sanitary emergency with {sewage_problem} {landmark}. {sewage_impact}. {urgency}",
    ],
    "Traffic Hazard": [
        "Severe road obstruction: {traffic_hazard} on {road_type} {landmark}. {urgency}",
        "Traffic safety threat: {traffic_hazard} {landmark} causing massive gridlock and safety hazard.",
        "Commuter alert: {traffic_hazard} reported on {road_type} {landmark}. {urgency}",
        "High risk of collision: {traffic_hazard} {landmark} along {road_type}. Please clear the road.",
        "Obstacle on roadway: {traffic_hazard} {landmark}. {urgency}",
    ],
}


def fill_template(template_str: str, category: str, rng: random.Random) -> str:
    """Fills slot variables in a category template with natural variations."""
    slots_needed = {
        "road_type": rng.choice(SLOTS["road_type"]),
        "landmark": rng.choice(SLOTS["landmark"]),
        "urgency": rng.choice(SLOTS["urgency"]),
    }
    if category == "Pothole":
        slots_needed["severity_pothole"] = rng.choice(SLOTS["severity_pothole"])
        slots_needed["pothole_hazard"] = rng.choice(SLOTS["pothole_hazard"])
    elif category == "Garbage":
        slots_needed["garbage_type"] = rng.choice(SLOTS["garbage_type"])
        slots_needed["garbage_impact"] = rng.choice(SLOTS["garbage_impact"])
    elif category == "Water Leakage":
        slots_needed["water_source"] = rng.choice(SLOTS["water_source"])
        slots_needed["water_impact"] = rng.choice(SLOTS["water_impact"])
    elif category == "Streetlight":
        slots_needed["light_problem"] = rng.choice(SLOTS["light_problem"])
        slots_needed["light_impact"] = rng.choice(SLOTS["light_impact"])
    elif category == "Sewage":
        slots_needed["sewage_problem"] = rng.choice(SLOTS["sewage_problem"])
        slots_needed["sewage_impact"] = rng.choice(SLOTS["sewage_impact"])
    elif category == "Traffic Hazard":
        slots_needed["traffic_hazard"] = rng.choice(SLOTS["traffic_hazard"])

    return template_str.format(**slots_needed)


def perturb_text_for_duplicate(original_text: str, rng: random.Random) -> str:
    """Creates a natural minor variation of an existing complaint text."""
    substitutions = [
        ("Please fix immediately.", "Kindly take swift action."),
        ("Kindly resolve on urgent priority.", "Needs urgent attention from the authority."),
        ("Action required before a major accident occurs.", "Accident risk is very high."),
        ("Request the municipal team to address this today.", "Please send a team to rectify this as soon as possible."),
        ("Residents have been suffering for days.", "Local citizens are facing great difficulty."),
        ("Dangerous", "Hazardous"),
        ("Severe", "Critical"),
        ("Huge", "Large"),
        ("causing", "leading to"),
        ("Urgent repair needed:", "Immediate repair required:"),
        ("Public health concern:", "Serious civic issue:"),
    ]
    perturbed = original_text
    applied = False
    for old, new in rng.sample(substitutions, len(substitutions)):
        if old in perturbed:
            perturbed = perturbed.replace(old, new, 1)
            applied = True
            break
    if not applied:
        prefixes = [
            "Second report: ",
            "Complaint reminder: ",
            "Citizen follow-up: ",
            "Reporting again: ",
        ]
        perturbed = rng.choice(prefixes) + perturbed
    return perturbed


def generate_complaints_data(
    total_count: int = 800,
    seed: int = 42,
    base_start_time: datetime = datetime(2026, 8, 10, 8, 0, 0),
    time_span_days: int = 35,
) -> pd.DataFrame:
    """Generates synthetic complaints dataset with slots, spikes, and duplicates."""
    rng = random.Random(seed)

    # 3 scripted spike definitions: (category, locality, start_day_offset, duration_days, spike_multiplier)
    spikes = [
        {"category": "Sewage", "locality": "Area C", "start_day": 8, "duration": 3, "count": 45},
        {"category": "Pothole", "locality": "Area A", "start_day": 19, "duration": 3, "count": 50},
        {"category": "Water Leakage", "locality": "Area E", "start_day": 28, "duration": 3, "count": 45},
    ]

    target_duplicates = 18
    total_spike_records = sum(s["count"] for s in spikes)
    base_records_count = max(100, total_count - total_spike_records - target_duplicates)

    records: List[Dict] = []
    complaint_counter = 1001

    locality_names = list(LOCALITIES.keys())

    # 1. Base Normal Complaints Distribution
    for _ in range(base_records_count):
        cat = rng.choice(CATEGORIES)
        loc = rng.choice(locality_names)
        center_lat, center_lon = LOCALITIES[loc]

        # Small spatial jitter around locality center (approx within 500m - 1km)
        lat = round(center_lat + rng.gauss(0, 0.004), 6)
        lon = round(center_lon + rng.gauss(0, 0.004), 6)

        # Time distribution over time_span_days
        day_offset = rng.uniform(0, time_span_days)
        # Weight towards realistic active hours (7 AM to 10 PM)
        hour = rng.choices(
            population=list(range(24)),
            weights=[1, 1, 1, 1, 1, 2, 4, 6, 8, 9, 8, 8, 7, 7, 8, 8, 9, 9, 8, 6, 5, 4, 2, 1],
            k=1,
        )[0]
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        timestamp = base_start_time + timedelta(days=int(day_offset), hours=hour, minutes=minute, seconds=second)

        template = rng.choice(TEMPLATES[cat])
        text = fill_template(template, cat, rng)
        status = rng.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        records.append({
            "complaint_id": f"PRM-{complaint_counter}",
            "complaint_text": text,
            "category": cat,
            "latitude": lat,
            "longitude": lon,
            "locality": loc,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
        })
        complaint_counter += 1

    # 2. Scripted Spikes (Category + Area + 3-day window)
    for spike in spikes:
        cat = spike["category"]
        loc = spike["locality"]
        center_lat, center_lon = LOCALITIES[loc]

        spike_start = base_start_time + timedelta(days=spike["start_day"])
        for _ in range(spike["count"]):
            lat = round(center_lat + rng.gauss(0, 0.0025), 6)
            lon = round(center_lon + rng.gauss(0, 0.0025), 6)

            # Random offset within the 3-day spike duration
            offset_seconds = rng.uniform(0, spike["duration"] * 86400)
            timestamp = spike_start + timedelta(seconds=offset_seconds)

            template = rng.choice(TEMPLATES[cat])
            text = fill_template(template, cat, rng)
            status = rng.choices(STATUSES, weights=[0.60, 0.25, 0.10, 0.05], k=1)[0]

            records.append({
                "complaint_id": f"PRM-{complaint_counter}",
                "complaint_text": text,
                "category": cat,
                "latitude": lat,
                "longitude": lon,
                "locality": loc,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
            })
            complaint_counter += 1

    # 3. Near-Duplicate Complaints (15-20 near-duplicates)
    # Pick randomly from already created complaints and create near-duplicates
    candidates_for_dup = rng.sample(records, target_duplicates)
    for orig in candidates_for_dup:
        orig_time = datetime.strptime(orig["timestamp"], "%Y-%m-%d %H:%M:%S")
        # Timestamp close to original: between +12 minutes and +150 minutes
        jitter_minutes = rng.randint(12, 150)
        dup_time = orig_time + timedelta(minutes=jitter_minutes)

        # Same locality, very close lat/lon jitter
        dup_lat = round(orig["latitude"] + rng.gauss(0, 0.0004), 6)
        dup_lon = round(orig["longitude"] + rng.gauss(0, 0.0004), 6)

        dup_text = perturb_text_for_duplicate(orig["complaint_text"], rng)

        records.append({
            "complaint_id": f"PRM-{complaint_counter}",
            "complaint_text": dup_text,
            "category": orig["category"],
            "latitude": dup_lat,
            "longitude": dup_lon,
            "locality": orig["locality"],
            "timestamp": dup_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": orig["status"],
        })
        complaint_counter += 1

    df = pd.DataFrame(records)
    # Sort chronologically by timestamp
    df["dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("dt").reset_index(drop=True)
    df = df.drop(columns=["dt"])

    return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic citizen complaints dataset for Praman.")
    parser.add_argument("--count", type=int, default=800, help="Number of records to generate (500-1000).")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed for reproducibility.")
    parser.add_argument("--output", type=str, default="data/synthetic_dataset.csv", help="Target CSV output path.")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print(f"Generating {args.count} synthetic complaints with seed={args.seed}...")
    df = generate_complaints_data(total_count=args.count, seed=args.seed)

    df.to_csv(args.output, index=False)
    print(f"Successfully saved {len(df)} complaints to {args.output}")
    print("\nDataset Summary:")
    print(f"- Shape: {df.shape}")
    print(f"- Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print("\nCategory Distribution:")
    print(df["category"].value_counts().to_string())
    print("\nLocality Distribution:")
    print(df["locality"].value_counts().to_string())
    print("\nStatus Distribution:")
    print(df["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
