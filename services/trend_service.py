from collections import defaultdict
from services.complaint_service import get_all_complaints
import dateutil.parser


def get_trends():
    """Aggregate complaint volume by date, category, and locality.
    
    Generates time series suitable for Recharts / Plotly on the Frontend.
    """
    complaints = get_all_complaints()

    daily_totals = defaultdict(int)
    by_category_daily = defaultdict(lambda: defaultdict(int))
    by_locality_daily = defaultdict(lambda: defaultdict(int))
    all_categories = set()
    all_localities = set()

    for c in complaints:
        ts = c.get("timestamp", "")
        # Robustly extract YYYY-MM-DD
        try:
            parsed_date = dateutil.parser.isoparse(ts)
            date_key = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            try:
                parsed_date = dateutil.parser.parse(ts)
                date_key = parsed_date.strftime("%Y-%m-%d")
            except Exception:
                date_key = "Unknown"

        cat = c.get("category", "Other")
        loc = c.get("locality", "Unknown")

        daily_totals[date_key] += 1
        by_category_daily[date_key][cat] += 1
        by_locality_daily[date_key][loc] += 1

        all_categories.add(cat)
        all_localities.add(loc)

    sorted_dates = sorted([d for d in daily_totals.keys() if d != "Unknown"])

    trends_by_category = []
    for d in sorted_dates:
        entry = {"date": d, "total": daily_totals[d]}
        for cat in all_categories:
            entry[cat] = by_category_daily[d].get(cat, 0)
        trends_by_category.append(entry)

    trends_by_locality = []
    for d in sorted_dates:
        entry = {"date": d, "total": daily_totals[d]}
        for loc in all_localities:
            entry[loc] = by_locality_daily[d].get(loc, 0)
        trends_by_locality.append(entry)

    return {
        "dates": sorted_dates,
        "daily_totals": [{"date": d, "count": daily_totals[d]} for d in sorted_dates],
        "by_category": trends_by_category,
        "by_locality": trends_by_locality,
        "categories": sorted(list(all_categories)),
        "localities": sorted(list(all_localities))
    }
