# ml/clustering.py
"""Incident clustering for Praman.

SCHEMA ASSUMPTIONS
------------------
The shared schema block in the brief was left as a paste placeholder
(``<<<PASTE SCHEMA HERE>>>``), so the following field names are assumed. They
are read defensively (aliases in brackets) and are easy to change in the
``*_KEYS`` constants below, but the **output** field names are treated as
fixed because the brief spells them out explicitly.

Complaint (input) object::

    complaint_id:   str | int          required, unique
    complaint_text: str                [text, description]
    category:       str                [complaint_category]; blank -> "Uncategorized"
    latitude:       float              [lat]
    longitude:      float              [lng, lon, long]
    timestamp:      str (ISO) | datetime   [created_at, reported_at]
    status:         str                [complaint_status]; missing -> unresolved

Incident cluster (output) object, exactly these keys in this order::

    incident_id:            str     "INC-{CATEGORY_SLUG}-{index:03d}"
    category:               str
    centroid_lat:           float
    centroid_lng:           float
    cluster_radius_km:      float   3dp
    complaint_count:        int
    similar_complaint_count:int
    unresolved_count:       int
    first_seen:             str     ISO 8601, timezone-naive
    last_seen:              str     ISO 8601, timezone-naive
    complaint_ids:          list[str]  sorted

DEFINITION OF ``similar_complaint_count`` (ambiguous in the spec, pinned here)
    The number of DISTINCT complaints in this cluster that appear as an
    endpoint of at least one pair labelled ``"Potential Duplicate"`` where the
    *other* endpoint is also a member of this cluster. It is therefore always
    in ``[0, complaint_count]``, and is 0 when the cluster is merely
    "related" rather than duplicated.

Pure functions, no global state, no printing. Inputs are never mutated.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd

from .geo_utils import haversine_km
from .similarity import (
    DEFAULT_CATEGORY,
    LABEL_DUPLICATE,
    compute_similarity_matrix,
    find_similar_pairs,
    get_category,
    get_text,
)

__all__ = [
    "SIMILARITY_THRESHOLD",
    "MAX_DISTANCE_KM",
    "MAX_TIME_WINDOW_HOURS",
    "MIN_CLUSTER_SIZE",
    "RESOLVED_STATUS",
    "build_graph",
    "find_clusters",
    "build_incident",
    "cluster_complaints",
    "cluster_complaints_with_warnings",
]

# --------------------------------------------------------------------------
# Tunable constants: the three edge rules and the minimum cluster size.
# --------------------------------------------------------------------------

#: Minimum cosine similarity for an edge (rule a).
SIMILARITY_THRESHOLD: float = 0.55

#: Maximum great-circle distance in km for an edge (rule b).
MAX_DISTANCE_KM: float = 2.0

#: Maximum absolute time difference in hours for an edge (rule c).
MAX_TIME_WINDOW_HOURS: float = 72.0

#: Connected components smaller than this are discarded.
MIN_CLUSTER_SIZE: int = 3

#: Status value (compared case-insensitively) that counts as resolved.
RESOLVED_STATUS: str = "resolved"

LAT_KEYS: Tuple[str, ...] = ("latitude", "lat")
LNG_KEYS: Tuple[str, ...] = ("longitude", "lng", "lon", "long")
TIMESTAMP_KEYS: Tuple[str, ...] = ("timestamp", "created_at", "reported_at")
STATUS_KEYS: Tuple[str, ...] = ("status", "complaint_status")

_SLUG_RE = re.compile(r"[^A-Za-z0-9]+")


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------


def _first_present(record: Mapping[str, Any], keys: Sequence[str], default: Any = None) -> Any:
    """Return the first non-``None`` value among ``keys`` in ``record``.

    Args:
        record: Mapping to read from.
        keys: Candidate keys, in priority order.
        default: Value returned when no key is present.

    Returns:
        The first value found, otherwise ``default``.
    """
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return default


def _slugify(value: str) -> str:
    """Turn a category name into an uppercase, hyphen-free id fragment.

    Args:
        value: Arbitrary category string.

    Returns:
        An uppercase alphanumeric slug, e.g. ``"Street Lights"`` -> ``"STREETLIGHTS"``.
        Falls back to ``"GENERAL"`` when nothing alphanumeric remains.
    """
    slug = _SLUG_RE.sub("", str(value)).upper()
    return slug if slug else "GENERAL"


def parse_timestamp(value: Any) -> Optional[pd.Timestamp]:
    """Parse a timestamp into a timezone-naive :class:`pandas.Timestamp`.

    Timezone-aware values are converted to UTC and then stripped of their
    tzinfo, so that all timestamps live on one comparable scale.

    Args:
        value: An ISO 8601 string, ``datetime``, ``pandas.Timestamp`` or any
            value ``pandas.to_datetime`` understands.

    Returns:
        A timezone-naive ``pandas.Timestamp``, or ``None`` when the value is
        missing or unparseable.

    Raises:
        Nothing: parse failures are reported as ``None`` so callers can collect
        a warning and skip the row.
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None

    try:
        parsed = pd.to_datetime(value, errors="raise")
    except (ValueError, TypeError, OverflowError, pd.errors.ParserError):
        return None

    if isinstance(parsed, pd.Series) or isinstance(parsed, pd.DatetimeIndex):
        return None
    if parsed is pd.NaT or (isinstance(parsed, float) and np.isnan(parsed)):
        return None

    ts = pd.Timestamp(parsed)
    if ts is pd.NaT:
        return None
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts


def _parse_coordinate(value: Any, low: float, high: float) -> Optional[float]:
    """Parse and range-check a coordinate value.

    Args:
        value: Raw latitude or longitude value.
        low: Inclusive lower bound.
        high: Inclusive upper bound.

    Returns:
        The coordinate as a float, or ``None`` when missing, non-numeric,
        NaN or out of range.
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number) or number < low or number > high:
        return None
    return number


def _normalise(
    complaints: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Validate and normalise raw complaints into internal records.

    The input list and its dicts are never mutated; new dicts are built.

    Args:
        complaints: Sequence of raw complaint mappings.

    Returns:
        A ``(records, warnings)`` tuple. Each record is a dict with keys
        ``complaint_id``, ``category``, ``text``, ``lat``, ``lng``, ``ts``
        (a timezone-naive ``pandas.Timestamp``) and ``status``. ``warnings``
        holds one human-readable string per skipped complaint.

    Raises:
        ValueError: If ``complaints`` is not a sequence of mappings, or if a
            complaint lacks ``complaint_id``.
    """
    records: List[Dict[str, Any]] = []
    warnings: List[str] = []
    seen_ids: Set[str] = set()

    for position, raw in enumerate(complaints):
        if not isinstance(raw, Mapping):
            raise ValueError(
                f"complaint at index {position} must be a mapping, got {type(raw).__name__}"
            )
        if raw.get("complaint_id") is None:
            raise ValueError(f"complaint at index {position} is missing a complaint_id")

        complaint_id = str(raw["complaint_id"])
        if complaint_id in seen_ids:
            warnings.append(f"{complaint_id}: duplicate complaint_id, keeping the first occurrence")
            continue

        lat = _parse_coordinate(_first_present(raw, LAT_KEYS), -90.0, 90.0)
        lng = _parse_coordinate(_first_present(raw, LNG_KEYS), -180.0, 180.0)
        if lat is None or lng is None:
            warnings.append(f"{complaint_id}: missing or invalid latitude/longitude, skipped")
            continue

        ts = parse_timestamp(_first_present(raw, TIMESTAMP_KEYS))
        if ts is None:
            warnings.append(f"{complaint_id}: missing or unparseable timestamp, skipped")
            continue

        status_value = _first_present(raw, STATUS_KEYS)
        records.append(
            {
                "complaint_id": complaint_id,
                "category": get_category(raw),
                "text": get_text(raw),
                "lat": lat,
                "lng": lng,
                "ts": ts,
                "status": None if status_value is None else str(status_value),
            }
        )
        seen_ids.add(complaint_id)

    return records, warnings


def _as_record(complaint: Mapping[str, Any]) -> Dict[str, Any]:
    """Coerce a raw or already-normalised complaint into an internal record.

    Lets ``build_graph`` / ``build_incident`` be called directly from tests or
    from a notebook with plain schema dicts.

    Args:
        complaint: A raw complaint mapping or an internal record.

    Returns:
        An internal record dict.

    Raises:
        ValueError: If the complaint lacks ``complaint_id``, coordinates, or a
            parseable timestamp.
    """
    if {"lat", "lng", "ts"} <= set(complaint.keys()) and isinstance(complaint.get("ts"), pd.Timestamp):
        return dict(complaint)

    if complaint.get("complaint_id") is None:
        raise ValueError("complaint is missing a complaint_id")

    lat = _parse_coordinate(_first_present(complaint, LAT_KEYS), -90.0, 90.0)
    lng = _parse_coordinate(_first_present(complaint, LNG_KEYS), -180.0, 180.0)
    ts = parse_timestamp(_first_present(complaint, TIMESTAMP_KEYS))
    if lat is None or lng is None:
        raise ValueError(f"complaint {complaint['complaint_id']} has missing/invalid coordinates")
    if ts is None:
        raise ValueError(f"complaint {complaint['complaint_id']} has an unparseable timestamp")

    return {
        "complaint_id": str(complaint["complaint_id"]),
        "category": get_category(complaint),
        "text": get_text(complaint),
        "lat": lat,
        "lng": lng,
        "ts": ts,
        "status": None if _first_present(complaint, STATUS_KEYS) is None else str(_first_present(complaint, STATUS_KEYS)),
    }


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def build_graph(
    complaints_in_category: Sequence[Mapping[str, Any]],
    sim_matrix: np.ndarray,
) -> nx.Graph:
    """Build the complaint graph for one category.

    Nodes are ``complaint_id`` strings, added in sorted order. An edge is
    added between complaints ``i`` and ``j`` only if **all three** rules hold:

    a. ``sim_matrix[i, j] >= SIMILARITY_THRESHOLD`` (0.55)
    b. haversine distance ``<= MAX_DISTANCE_KM`` (2.0 km)
    c. ``abs(timestamp difference) <= MAX_TIME_WINDOW_HOURS`` (72 h)

    Each edge carries ``similarity``, ``distance_km`` and ``hours_apart``
    attributes (rounded to 4, 4 and 4 decimal places respectively). Node
    attributes ``category``, ``lat``, ``lng``, ``timestamp`` and ``status``
    are stored for convenience.

    Args:
        complaints_in_category: Complaints belonging to a single category, in
            the same order as the rows/columns of ``sim_matrix``. Raw schema
            dicts or internal records are both accepted.
        sim_matrix: Square cosine-similarity matrix of shape ``(n, n)``.

    Returns:
        A :class:`networkx.Graph`.

    Raises:
        ValueError: If ``sim_matrix`` is not square or its size does not match
            the number of complaints, or if a complaint is unusable.
    """
    records = [_as_record(c) for c in complaints_in_category]
    n = len(records)

    matrix = np.asarray(sim_matrix, dtype=float)
    if matrix.shape != (n, n):
        raise ValueError(f"sim_matrix must have shape ({n}, {n}), got {matrix.shape}")

    graph = nx.Graph()
    for record in sorted(records, key=lambda r: r["complaint_id"]):
        graph.add_node(
            record["complaint_id"],
            category=record["category"],
            lat=record["lat"],
            lng=record["lng"],
            timestamp=record["ts"].isoformat(),
            status=record["status"],
        )

    for i in range(n):
        for j in range(i + 1, n):
            similarity = float(matrix[i, j])
            if similarity < SIMILARITY_THRESHOLD:
                continue

            distance = float(
                haversine_km(records[i]["lat"], records[i]["lng"], records[j]["lat"], records[j]["lng"])
            )
            if distance > MAX_DISTANCE_KM:
                continue

            hours_apart = abs((records[i]["ts"] - records[j]["ts"]).total_seconds()) / 3600.0
            if hours_apart > MAX_TIME_WINDOW_HOURS:
                continue

            graph.add_edge(
                records[i]["complaint_id"],
                records[j]["complaint_id"],
                similarity=round(similarity, 4),
                distance_km=round(distance, 4),
                hours_apart=round(hours_apart, 4),
            )

    return graph


def find_clusters(graph: nx.Graph) -> List[Set[str]]:
    """Extract connected components large enough to count as incidents.

    Args:
        graph: A graph produced by :func:`build_graph`.

    Returns:
        A list of sets of ``complaint_id``, each with at least
        ``MIN_CLUSTER_SIZE`` members. Ordered deterministically by descending
        size, then by the smallest member id.

    Raises:
        ValueError: If ``graph`` is not a ``networkx.Graph``.
    """
    if not isinstance(graph, nx.Graph):
        raise ValueError(f"graph must be a networkx.Graph, got {type(graph).__name__}")

    components = [
        set(component)
        for component in nx.connected_components(graph)
        if len(component) >= MIN_CLUSTER_SIZE
    ]
    components.sort(key=lambda comp: (-len(comp), sorted(comp)[0]))
    return components


def build_incident(
    component: Iterable[str],
    complaints_lookup: Mapping[str, Mapping[str, Any]],
    pairs: Sequence[Mapping[str, Any]],
    index: int = 1,
) -> Dict[str, Any]:
    """Assemble one incident-cluster dict from a connected component.

    ``similar_complaint_count`` is the number of DISTINCT complaints in this
    cluster that appear as an endpoint of at least one pair labelled
    ``"Potential Duplicate"`` whose other endpoint is also in this cluster.
    (The spec is ambiguous here; this is the definition used throughout, and
    it is repeated in README_CLUSTERING.md.)

    ``unresolved_count`` counts complaints whose status is not ``"Resolved"``
    compared case-insensitively; a missing or blank status counts as
    unresolved.

    Args:
        component: The ``complaint_id`` values that form this incident.
        complaints_lookup: Mapping from ``complaint_id`` to the complaint
            (raw schema dict or internal record) for every member.
        pairs: The pair dicts from :func:`ml.similarity.find_similar_pairs`.
            Pairs touching complaints outside the component are ignored.
        index: 1-based ordinal used in ``incident_id``.

    Returns:
        A single incident-cluster dict matching the documented output schema.

    Raises:
        ValueError: If the component is empty, if a member is absent from
            ``complaints_lookup``, or if members disagree on category.
    """
    member_ids = sorted({str(cid) for cid in component})
    if not member_ids:
        raise ValueError("cannot build an incident from an empty component")

    members: List[Dict[str, Any]] = []
    for cid in member_ids:
        if cid not in complaints_lookup:
            raise ValueError(f"complaint_id {cid!r} is missing from complaints_lookup")
        members.append(_as_record(complaints_lookup[cid]))

    categories = sorted({m["category"] for m in members})
    if len(categories) > 1:
        raise ValueError(f"a cluster must share one category, got {categories}")
    category = categories[0] if categories else DEFAULT_CATEGORY

    lats = np.array([m["lat"] for m in members], dtype=float)
    lngs = np.array([m["lng"] for m in members], dtype=float)
    centroid_lat = float(lats.mean())
    centroid_lng = float(lngs.mean())

    if len(members) == 1:
        radius = 0.0
    else:
        distances = haversine_km(centroid_lat, centroid_lng, lats, lngs)
        radius = float(np.max(np.asarray(distances, dtype=float)))

    member_set = set(member_ids)
    duplicate_members: Set[str] = set()
    for pair in pairs:
        if pair.get("label") != LABEL_DUPLICATE:
            continue
        a = str(pair.get("complaint_id_a"))
        b = str(pair.get("complaint_id_b"))
        if a in member_set and b in member_set:
            duplicate_members.add(a)
            duplicate_members.add(b)

    unresolved = 0
    for m in members:
        status = m["status"]
        if status is None or str(status).strip().lower() != RESOLVED_STATUS:
            unresolved += 1

    timestamps = [m["ts"] for m in members]
    first_seen = min(timestamps)
    last_seen = max(timestamps)

    return {
        "incident_id": f"INC-{_slugify(category)}-{index:03d}",
        "category": category,
        "centroid_lat": round(centroid_lat, 6),
        "centroid_lng": round(centroid_lng, 6),
        "cluster_radius_km": round(radius, 3),
        "complaint_count": len(members),
        "similar_complaint_count": len(duplicate_members),
        "unresolved_count": unresolved,
        "first_seen": first_seen.isoformat(),
        "last_seen": last_seen.isoformat(),
        "complaint_ids": member_ids,
    }


def cluster_complaints_with_warnings(
    complaints: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Run the full clustering pipeline and also return skip warnings.

    Pipeline: validate input -> group by category -> per-category TF-IDF
    similarity -> build graph -> connected components -> build incidents.

    Args:
        complaints: Sequence of complaint mappings. May be empty. Neither the
            sequence nor its dicts are mutated.

    Returns:
        A ``(incidents, warnings)`` tuple. ``incidents`` is sorted by
        ``complaint_count`` descending, then ``first_seen`` ascending, then
        ``incident_id`` ascending. ``warnings`` lists complaints that were
        skipped and why.

    Raises:
        ValueError: If ``complaints`` is not a sequence of mappings, or if a
            complaint lacks ``complaint_id``.
    """
    if complaints is None:
        raise ValueError("complaints must be a sequence, got None")
    if isinstance(complaints, (Mapping, str, bytes)):
        raise ValueError("complaints must be a sequence of complaint mappings")

    records, warnings = _normalise(complaints)
    if not records:
        return [], warnings

    pairs = find_similar_pairs(
        [
            {
                "complaint_id": r["complaint_id"],
                "complaint_text": r["text"],
                "category": r["category"],
            }
            for r in records
        ]
    )

    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        buckets.setdefault(record["category"], []).append(record)

    lookup = {r["complaint_id"]: r for r in records}

    incidents: List[Dict[str, Any]] = []
    for category in sorted(buckets):
        members = sorted(buckets[category], key=lambda r: r["complaint_id"])
        if len(members) < MIN_CLUSTER_SIZE:
            continue

        sims = compute_similarity_matrix([m["text"] for m in members])
        graph = build_graph(members, sims)
        components = find_clusters(graph)

        for position, component in enumerate(components, start=1):
            incidents.append(build_incident(component, lookup, pairs, index=position))

    incidents.sort(key=lambda inc: (-inc["complaint_count"], inc["first_seen"], inc["incident_id"]))
    return incidents, warnings


def cluster_complaints(complaints: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Cluster complaints into incident objects. Single public entrypoint.

    Args:
        complaints: Sequence of complaint mappings (see the module docstring
            for the assumed field names). May be empty. Never mutated.

    Returns:
        A list of incident-cluster dicts, sorted by ``complaint_count``
        descending then ``first_seen`` ascending. Empty input yields ``[]``.

    Raises:
        ValueError: If ``complaints`` is not a sequence of mappings, or if a
            complaint lacks ``complaint_id``.
    """
    incidents, _warnings = cluster_complaints_with_warnings(complaints)
    return incidents