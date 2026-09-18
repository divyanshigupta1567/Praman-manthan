# tests/test_clustering.py
"""Tests for the Praman incident-clustering module.

Run from the repository root so that the ``ml`` package is importable:

    python -m pytest tests/ -v
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

import pytest

from incident_clustering.clustering import (
    MAX_DISTANCE_KM,
    MAX_TIME_WINDOW_HOURS,
    MIN_CLUSTER_SIZE,
    SIMILARITY_THRESHOLD,
    build_graph,
    cluster_complaints,
    cluster_complaints_with_warnings,
    find_clusters,
)
from incident_clustering.geo_utils import haversine_km
from incident_clustering.similarity import (
    DUPLICATE_THRESHOLD,
    LABEL_DUPLICATE,
    LABEL_RELATED,
    LABEL_UNRELATED,
    RELATED_THRESHOLD,
    compute_similarity_matrix,
    find_similar_pairs,
    label_similarity,
)

# --------------------------------------------------------------------------
# Fixtures / builders
# --------------------------------------------------------------------------

BASE_LAT = 28.6139  # Connaught Place, Delhi
BASE_LNG = 77.2090

# Near-identical wording on purpose. With a small corpus, IDF weights unique
# tokens heavily, so loose paraphrases score well below 0.55; see
# README_CLUSTERING.md, "Why the thresholds behave differently on tiny inputs".
GARBAGE_TEXTS = [
    "Garbage not collected near the main market for over a week, terrible smell",
    "Garbage not collected near the main market for over a week, very bad smell",
    "Garbage not collected near the main market for a week, terrible smell",
]


def make_complaint(
    complaint_id: str,
    text: str,
    category: str = "Garbage",
    lat: float = BASE_LAT,
    lng: float = BASE_LNG,
    timestamp: str = "2026-03-01T09:00:00",
    status: str = "Open",
) -> Dict[str, Any]:
    """Build a complaint dict in the assumed input schema."""
    return {
        "complaint_id": complaint_id,
        "complaint_text": text,
        "category": category,
        "latitude": lat,
        "longitude": lng,
        "timestamp": timestamp,
        "status": status,
    }


def three_similar(**overrides: Any) -> List[Dict[str, Any]]:
    """Three near-identical garbage complaints, same locality, same day."""
    return [
        make_complaint("C1", GARBAGE_TEXTS[0], timestamp="2026-03-01T09:00:00", **overrides),
        make_complaint("C2", GARBAGE_TEXTS[1], timestamp="2026-03-01T11:30:00", **overrides),
        make_complaint("C3", GARBAGE_TEXTS[2], timestamp="2026-03-01T17:45:00", **overrides),
    ]


# --------------------------------------------------------------------------
# geo_utils
# --------------------------------------------------------------------------


def test_haversine_known_city_pair_within_one_percent():
    # London (51.5074, -0.1278) to Paris (48.8566, 2.3522): ~343.5 km great-circle.
    distance = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert distance == pytest.approx(343.5, rel=0.01)


def test_haversine_second_known_city_pair_within_one_percent():
    # Delhi to Mumbai: ~1148 km great-circle.
    distance = haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
    assert distance == pytest.approx(1148.0, rel=0.01)


def test_haversine_identical_points_is_zero():
    assert haversine_km(BASE_LAT, BASE_LNG, BASE_LAT, BASE_LNG) == pytest.approx(0.0, abs=1e-9)


def test_haversine_is_symmetric():
    forward = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
    backward = haversine_km(13.0827, 80.2707, 12.9716, 77.5946)
    assert forward == pytest.approx(backward, abs=1e-9)


def test_haversine_accepts_arrays():
    import numpy as np

    lats = np.array([BASE_LAT, BASE_LAT + 0.01])
    lngs = np.array([BASE_LNG, BASE_LNG])
    result = haversine_km(BASE_LAT, BASE_LNG, lats, lngs)
    assert result.shape == (2,)
    assert result[0] == pytest.approx(0.0, abs=1e-9)
    assert result[1] > 0.0


@pytest.mark.parametrize(
    "args",
    [
        (91.0, 0.0, 0.0, 0.0),
        (-91.0, 0.0, 0.0, 0.0),
        (0.0, 181.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, -180.5),
    ],
)
def test_haversine_rejects_out_of_range_coordinates(args):
    with pytest.raises(ValueError):
        haversine_km(*args)


# --------------------------------------------------------------------------
# similarity
# --------------------------------------------------------------------------


def test_label_similarity_exactly_at_duplicate_boundary():
    assert label_similarity(DUPLICATE_THRESHOLD) == LABEL_DUPLICATE
    assert label_similarity(0.85) == LABEL_DUPLICATE


def test_label_similarity_just_below_duplicate_boundary():
    assert label_similarity(0.8499) == LABEL_RELATED


def test_label_similarity_exactly_at_related_boundary():
    assert label_similarity(RELATED_THRESHOLD) == LABEL_RELATED
    assert label_similarity(0.55) == LABEL_RELATED


def test_label_similarity_just_below_related_boundary():
    assert label_similarity(0.5499) == LABEL_UNRELATED


def test_label_similarity_extremes():
    assert label_similarity(1.0) == LABEL_DUPLICATE
    assert label_similarity(0.0) == LABEL_UNRELATED


def test_find_similar_pairs_empty_input():
    assert find_similar_pairs([]) == []


def test_find_similar_pairs_single_complaint_in_category():
    assert find_similar_pairs([make_complaint("C1", GARBAGE_TEXTS[0])]) == []


def test_find_similar_pairs_ignores_blank_text():
    complaints = [
        make_complaint("C1", "   "),
        make_complaint("C2", ""),
        make_complaint("C3", GARBAGE_TEXTS[0]),
    ]
    assert find_similar_pairs(complaints) == []


def test_find_similar_pairs_empty_vocabulary_returns_no_pairs():
    # Every document is pure stop words, so TfidfVectorizer has empty vocabulary.
    complaints = [
        make_complaint("C1", "the and of"),
        make_complaint("C2", "and the of"),
        make_complaint("C3", "of the and"),
    ]
    assert find_similar_pairs(complaints) == []


def test_find_similar_pairs_never_crosses_categories():
    complaints = [
        make_complaint("C1", GARBAGE_TEXTS[0], category="Garbage"),
        make_complaint("C2", GARBAGE_TEXTS[1], category="Water"),
    ]
    assert find_similar_pairs(complaints) == []


def test_find_similar_pairs_excludes_self_and_unrelated():
    complaints = three_similar() + [
        make_complaint("C4", "Broken water pipeline flooding the lane since morning")
    ]
    pairs = find_similar_pairs(complaints)
    assert pairs, "expected at least one related pair"
    for pair in pairs:
        assert pair["complaint_id_a"] != pair["complaint_id_b"]
        assert pair["label"] != LABEL_UNRELATED
        assert 0.0 <= pair["similarity_score"] <= 1.0
        assert pair["similarity_score"] == round(pair["similarity_score"], 4)
    assert not any("C4" in (p["complaint_id_a"], p["complaint_id_b"]) for p in pairs)


def test_compute_similarity_matrix_shapes():
    assert compute_similarity_matrix([]).shape == (0, 0)
    sims = compute_similarity_matrix(GARBAGE_TEXTS)
    assert sims.shape == (3, 3)
    assert sims[0][0] == pytest.approx(1.0)
    assert sims[0][1] == pytest.approx(sims[1][0])


# --------------------------------------------------------------------------
# clustering: the three edge rules
# --------------------------------------------------------------------------


def test_three_similar_complaints_form_one_cluster_of_three():
    incidents = cluster_complaints(three_similar())
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident["complaint_count"] == 3
    assert incident["complaint_ids"] == ["C1", "C2", "C3"]
    assert incident["category"] == "Garbage"


def test_two_similar_complaints_are_below_min_cluster_size():
    complaints = three_similar()[:2]
    assert len(complaints) < MIN_CLUSTER_SIZE
    assert cluster_complaints(complaints) == []


def test_distance_rule_fifty_km_apart_yields_no_cluster():
    complaints = three_similar()
    # Roughly 50 km north and 50 km further north.
    complaints[1]["latitude"] = BASE_LAT + 0.45
    complaints[2]["latitude"] = BASE_LAT + 0.90
    assert haversine_km(BASE_LAT, BASE_LNG, complaints[1]["latitude"], BASE_LNG) > MAX_DISTANCE_KM
    assert cluster_complaints(complaints) == []


def test_time_rule_ten_days_apart_yields_no_cluster():
    complaints = three_similar()
    complaints[1]["timestamp"] = "2026-03-11T09:00:00"
    complaints[2]["timestamp"] = "2026-03-21T09:00:00"
    assert 10 * 24 > MAX_TIME_WINDOW_HOURS
    assert cluster_complaints(complaints) == []


def test_different_categories_yield_no_cluster():
    complaints = three_similar()
    complaints[0]["category"] = "Garbage"
    complaints[1]["category"] = "Water"
    complaints[2]["category"] = "Roads"
    assert cluster_complaints(complaints) == []


def test_unrelated_text_same_place_and_time_yields_no_cluster():
    complaints = [
        make_complaint("C1", "Garbage dump not cleared near the market, terrible smell"),
        make_complaint("C2", "Stray dogs chasing schoolchildren every morning"),
        make_complaint("C3", "Loudspeaker noise from construction site after midnight"),
    ]
    assert cluster_complaints(complaints) == []


def test_edge_attributes_are_stored():
    complaints = three_similar()
    sims = compute_similarity_matrix([c["complaint_text"] for c in complaints])
    graph = build_graph(complaints, sims)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() >= 1
    for _u, _v, data in graph.edges(data=True):
        assert data["similarity"] >= SIMILARITY_THRESHOLD
        assert data["distance_km"] <= MAX_DISTANCE_KM
        assert data["hours_apart"] <= MAX_TIME_WINDOW_HOURS


def test_build_graph_rejects_mismatched_matrix():
    complaints = three_similar()
    with pytest.raises(ValueError):
        build_graph(complaints, compute_similarity_matrix(["only one doc"]))


def test_find_clusters_drops_small_components():
    import networkx as nx

    graph = nx.Graph()
    graph.add_edge("A", "B")  # size 2, dropped
    graph.add_edges_from([("X", "Y"), ("Y", "Z")])  # size 3, kept
    clusters = find_clusters(graph)
    assert clusters == [{"X", "Y", "Z"}]


# --------------------------------------------------------------------------
# clustering: incident payload
# --------------------------------------------------------------------------


def test_incident_schema_fields_and_values():
    complaints = three_similar()
    complaints[2]["status"] = "resolved"  # lowercase on purpose
    del complaints[1]["status"]  # missing status counts as unresolved

    incidents = cluster_complaints(complaints)
    assert len(incidents) == 1
    incident = incidents[0]

    expected_keys = {
        "incident_id",
        "category",
        "centroid_lat",
        "centroid_lng",
        "cluster_radius_km",
        "complaint_count",
        "similar_complaint_count",
        "unresolved_count",
        "first_seen",
        "last_seen",
        "complaint_ids",
    }
    assert set(incident.keys()) == expected_keys

    assert incident["incident_id"] == "INC-GARBAGE-001"
    assert incident["centroid_lat"] == pytest.approx(BASE_LAT, abs=1e-6)
    assert incident["centroid_lng"] == pytest.approx(BASE_LNG, abs=1e-6)
    assert incident["cluster_radius_km"] == pytest.approx(0.0, abs=1e-6)
    assert incident["complaint_count"] == 3
    assert incident["unresolved_count"] == 2
    assert incident["first_seen"] == "2026-03-01T09:00:00"
    assert incident["last_seen"] == "2026-03-01T17:45:00"
    assert 0 <= incident["similar_complaint_count"] <= incident["complaint_count"]


def test_cluster_radius_is_non_negative_and_rounded():
    complaints = three_similar()
    complaints[1]["latitude"] = BASE_LAT + 0.005  # ~0.55 km north
    complaints[2]["longitude"] = BASE_LNG + 0.005
    incidents = cluster_complaints(complaints)
    assert len(incidents) == 1
    radius = incidents[0]["cluster_radius_km"]
    assert radius > 0.0
    assert radius == round(radius, 3)


def test_incidents_sorted_by_count_desc_then_first_seen():
    big = three_similar()
    water = [
        make_complaint("W1", "Sewage overflowing on the main road near the bus stop",
                       category="Water", timestamp="2026-02-20T08:00:00"),
        make_complaint("W2", "Sewage overflow on main road close to the bus stop",
                       category="Water", timestamp="2026-02-20T12:00:00"),
        make_complaint("W3", "Sewage is overflowing onto the main road by the bus stop",
                       category="Water", timestamp="2026-02-21T09:00:00"),
        make_complaint("W4", "Overflowing sewage across the main road near bus stop",
                       category="Water", timestamp="2026-02-21T15:00:00"),
    ]
    incidents = cluster_complaints(big + water)
    assert len(incidents) == 2
    counts = [i["complaint_count"] for i in incidents]
    assert counts == sorted(counts, reverse=True)
    assert incidents[0]["category"] == "Water"


# --------------------------------------------------------------------------
# clustering: contract behaviours
# --------------------------------------------------------------------------


def test_empty_input_returns_empty_list():
    assert cluster_complaints([]) == []


def test_determinism_under_shuffling():
    complaints = three_similar() + [
        make_complaint("D1", "Large pothole on the service lane is damaging two wheelers every day",
                       category="Roads", timestamp="2026-03-02T08:00:00"),
        make_complaint("D2", "Large pothole on the service lane is damaging two wheelers daily",
                       category="Roads", timestamp="2026-03-02T10:00:00"),
        make_complaint("D3", "Large pothole on the service lane keeps damaging two wheelers every day",
                       category="Roads", timestamp="2026-03-02T14:00:00"),
    ]

    first_order = list(complaints)
    second_order = list(complaints)
    random.Random(7).shuffle(first_order)
    random.Random(99).shuffle(second_order)

    run_a = cluster_complaints(first_order)
    run_b = cluster_complaints(second_order)

    assert run_a == run_b
    sets_a = [frozenset(i["complaint_ids"]) for i in run_a]
    sets_b = [frozenset(i["complaint_ids"]) for i in run_b]
    assert sets_a == sets_b


def test_input_is_never_mutated():
    complaints = three_similar()
    import copy

    snapshot = copy.deepcopy(complaints)
    cluster_complaints(complaints)
    assert complaints == snapshot


def test_unparseable_timestamp_is_skipped_with_warning():
    complaints = three_similar()
    complaints[0]["timestamp"] = "not-a-date"
    incidents, warnings = cluster_complaints_with_warnings(complaints)
    assert incidents == []  # only 2 usable, below MIN_CLUSTER_SIZE
    assert any("C1" in w for w in warnings)


def test_missing_coordinates_are_skipped_with_warning():
    complaints = three_similar()
    complaints[1]["latitude"] = None
    incidents, warnings = cluster_complaints_with_warnings(complaints)
    assert incidents == []
    assert any("C2" in w for w in warnings)


def test_timezone_aware_timestamps_are_handled():
    complaints = [
        make_complaint("C1", GARBAGE_TEXTS[0], timestamp="2026-03-01T09:00:00+05:30"),
        make_complaint("C2", GARBAGE_TEXTS[1], timestamp="2026-03-01T06:00:00Z"),
        make_complaint("C3", GARBAGE_TEXTS[2], timestamp="2026-03-01T04:00:00+00:00"),
    ]
    incidents = cluster_complaints(complaints)
    assert len(incidents) == 1
    assert incidents[0]["complaint_count"] == 3


def test_missing_complaint_id_raises():
    with pytest.raises(ValueError):
        cluster_complaints([{"complaint_text": "x", "latitude": 1.0, "longitude": 1.0}])


def test_non_sequence_input_raises():
    with pytest.raises(ValueError):
        cluster_complaints(None)