import json
import os
from datetime import datetime, timezone

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "complaints.json")

# In-memory storage seeded from JSON
_complaints = []


def _load_complaints():
    global _complaints
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                _complaints = json.load(f)
        except Exception:
            _complaints = []
    else:
        _complaints = []


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
    """Keyword-based placeholder until Member 1 classifier is plugged in.
    
    Designed so Member 1's ml/classifier.py can be cleanly called here.
    """
    text_lower = text.lower()
    if any(k in text_lower for k in ["pothole", "crater", "road", "asphalt"]):
        return "Pothole", 0.92
    elif any(k in text_lower for k in ["garbage", "trash", "waste", "dump", "bin"]):
        return "Garbage", 0.90
    elif any(k in text_lower for k in ["water", "leak", "pipe", "pipeline", "gushing"]):
        return "Water Leakage", 0.94
    elif any(k in text_lower for k in ["light", "streetlight", "dark", "lamp", "pole"]):
        return "Streetlight", 0.89
    elif any(k in text_lower for k in ["sewage", "drain", "manhole", "foul", "sewer"]):
        return "Sewage", 0.91
    elif any(k in text_lower for k in ["traffic", "divider", "tree", "hazard", "obstruction"]):
        return "Traffic Hazard", 0.88
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

    # Generate sequential ID (e.g. C0018)
    existing_nums = []
    for c in _complaints:
        cid = c.get("complaint_id", "")
        if cid.startswith("C") and cid[1:].isdigit():
            existing_nums.append(int(cid[1:]))
    next_id_num = max(existing_nums, default=0) + 1
    new_id = f"C{next_id_num:04d}"

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

    # Persist back to JSON file
    try:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(_complaints, f, indent=2)
    except Exception:
        pass

    return new_complaint
