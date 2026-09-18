import json
import os
import threading
from datetime import datetime, timezone
import pandas as pd

CSV_TRAIN_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "praman_train.csv")
CSV_TEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "praman_test.csv")
NEW_SUBMISSIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "new_submissions.json")

# In-memory storage seeded from CSV/JSON
_complaints = []
_new_submissions = []
_lock = threading.Lock()
ANCHOR_DATE = None

def get_anchor_date():
    global ANCHOR_DATE
    if ANCHOR_DATE is None:
        _load_complaints()
    return ANCHOR_DATE

def _load_complaints():
    global _complaints, _new_submissions, ANCHOR_DATE
    
    _complaints = []
    _new_submissions = []
    
    # 1. Load train and test datasets
    dfs = []
    if os.path.exists(CSV_TRAIN_PATH):
        dfs.append(pd.read_csv(CSV_TRAIN_PATH))
    if os.path.exists(CSV_TEST_PATH):
        dfs.append(pd.read_csv(CSV_TEST_PATH))
        
    if dfs:
        df = pd.concat(dfs, ignore_index=True)

    if dfs:
        try:
            for _, row in df.iterrows():
                text = str(row.get("complaint_text", ""))
                # Skip prediction for historical data to save startup time since category is known
                # But we populate predicted_category with the actual category for consistency
                cat = str(row.get("category", ""))
                
                # Parse timestamp slightly defensively to standard ISO with UTC Z
                ts_raw = str(row.get("timestamp", "")).strip()
                try:
                    ts = ts_raw.replace(" ", "T")
                    if not ts.endswith("Z") and "+" not in ts:
                        ts = ts + "Z"
                except:
                    ts = ts_raw

                _complaints.append({
                    "complaint_id": str(row.get("complaint_id", "")),
                    "complaint_text": text,
                    "category": cat,
                    "predicted_category": cat,
                    "confidence": 1.0,
                    "latitude": float(row.get("latitude", 0.0)),
                    "longitude": float(row.get("longitude", 0.0)),
                    "locality": str(row.get("locality", "")),
                    "timestamp": ts,
                    "status": str(row.get("status", "Open")).replace("unresolved", "Open")
                })
        except Exception as e:
            print(f"Error loading CSVs: {e}")

    # Compute ANCHOR_DATE from the dataset max timestamp
    if _complaints:
        max_ts = max(c["timestamp"] for c in _complaints)
        if not max_ts.endswith("Z") and "+" not in max_ts:
            max_ts = max_ts + "Z"
        ANCHOR_DATE = max_ts
    else:
        ANCHOR_DATE = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 2. Load and append new submissions
    if os.path.exists(NEW_SUBMISSIONS_PATH):
        try:
            with open(NEW_SUBMISSIONS_PATH, "r", encoding="utf-8") as f:
                _new_submissions = json.load(f)
                _complaints.extend(_new_submissions)
        except Exception:
            pass


def get_all_complaints(category=None, locality=None, status=None):
    """Retrieve all complaints with optional filtering.
    
    Swap hook: When ML Member 1 lands real classifier / dataset,
    this service can read directly from the generated CSV/model output.
    """
    if not _complaints:
        _load_complaints()

    results = _complaints
    if category:
        results = [c for c in results if c.get("category", "").lower() == category.lower()]
    if locality:
        results = [c for c in results if c.get("locality", "").lower() == locality.lower()]
    if status:
        results = [c for c in results if c.get("status", "").lower() == status.lower()]

    return results


def predict_category_placeholder(text):
    """Keyword-based scoring classifier until Member 1 classifier is plugged in.
    
    Uses regex word boundaries and category scoring to prevent false matches.
    Designed so Member 1's ml/classifier.py can be cleanly called here.
    """
    import re
    text_lower = text.lower()
    keywords = {
        "Water Leakage": ["water", "leak", "leakage", "pipe", "pipeline", "gushing", "hydrant", "burst", "drinking water", "waterlogging"],
        "Sewage": ["sewage", "drain", "drainage", "manhole", "foul", "sewer", "wastewater", "stagnant", "suction", "stench"],
        "Pothole": ["pothole", "potholes", "crater", "craters", "asphalt", "cave-in", "depression", "road surface", "tar"],
        "Garbage": ["garbage", "trash", "waste", "dump", "debris", "plastic", "rubbish", "litter", "refuse", "bin"],
        "Streetlight": ["streetlight", "street light", "lamp", "lantern", "illumination", "darkness", "unlit", "pole"],
        "Traffic Hazard": ["traffic", "divider", "barricade", "barrier", "gridlock", "collision", "blind turn", "obstruction", "hazard"]
    }
    scores = {cat: 0 for cat in keywords}
    for cat, words in keywords.items():
        for w in words:
            matches = len(re.findall(r'\b' + re.escape(w) + r'\b', text_lower))
            scores[cat] += matches * (2 if len(w) > 5 else 1)

    best_cat, best_score = max(scores.items(), key=lambda x: x[1])
    if best_score > 0:
        conf = min(0.96, 0.82 + (best_score * 0.04))
        return best_cat, round(conf, 2)
    return "Pothole", 0.75



def create_complaint(payload):
    """Create and append a new complaint.
    
    Accepts payload: {complaint_text, latitude, longitude, locality (optional)}
    Generates complaint_id, assigns predicted_category + confidence, status='unresolved'.
    """
    if not _complaints:
        _load_complaints()

    complaint_text = payload.get("complaint_text", "").strip()
    try:
        latitude = float(payload.get("latitude", 0.0))
        longitude = float(payload.get("longitude", 0.0))
    except (ValueError, TypeError):
        latitude = 0.0
        longitude = 0.0

    locality = payload.get("locality", "Area A").strip() or "Area A"

    # Thread-safe ID generation and appending
    with _lock:
        existing_nums = []
        for c in _complaints:
            cid = c.get("complaint_id", "")
            if cid.startswith("PRM-") and cid[4:].isdigit():
                existing_nums.append(int(cid[4:]))
            elif cid.startswith("C") and cid[1:].isdigit():
                existing_nums.append(int(cid[1:]))
                
        next_id_num = max(existing_nums, default=0) + 1
        new_id = f"PRM-{next_id_num:04d}"

        predicted_cat, conf = predict_category_placeholder(complaint_text)

        new_complaint = {
            "complaint_id": new_id,
            "complaint_text": complaint_text,
            "category": predicted_cat,
            "predicted_category": predicted_cat,
            "confidence": conf,
            "latitude": latitude,
            "longitude": longitude,
            "locality": locality,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "unresolved"
        }

        _complaints.append(new_complaint)
        _new_submissions.append(new_complaint)

        # Persist back to runtime JSON file (only the new submissions)
        try:
            with open(NEW_SUBMISSIONS_PATH, "w", encoding="utf-8") as f:
                json.dump(_new_submissions, f, indent=2)
        except Exception:
            pass

    return new_complaint
