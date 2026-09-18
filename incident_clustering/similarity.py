# ml/similarity.py
"""Text-similarity helpers for the Praman incident-clustering module.

SCHEMA ASSUMPTION (the shared schema block was left as a paste placeholder in
the brief). A complaint is assumed to be a plain ``dict`` with at least:

    complaint_id:   str | int   - unique identifier
    complaint_text: str         - free-text description (may be empty)
    category:       str         - e.g. "Garbage", "Water", "Roads"

Latitude/longitude/timestamp/status are only needed by ``ml.clustering``.
For robustness a few common aliases are accepted for the text and category
fields (see ``TEXT_KEYS`` / ``CATEGORY_KEYS``), but ``complaint_id`` is
required and never aliased.

Pure functions, no global state, no printing.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
from scipy.sparse import spmatrix  # transitively available via scikit-learn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

__all__ = [
    "DUPLICATE_THRESHOLD",
    "RELATED_THRESHOLD",
    "LABEL_DUPLICATE",
    "LABEL_RELATED",
    "LABEL_UNRELATED",
    "build_tfidf_matrix",
    "compute_similarity_matrix",
    "label_similarity",
    "find_similar_pairs",
]

# --------------------------------------------------------------------------
# Tunable constants (single source of truth for the labelling thresholds).
# --------------------------------------------------------------------------

#: Cosine similarity at or above which two complaints are called duplicates.
DUPLICATE_THRESHOLD: float = 0.85

#: Cosine similarity at or above which two complaints are called related.
RELATED_THRESHOLD: float = 0.55

LABEL_DUPLICATE: str = "Potential Duplicate"
LABEL_RELATED: str = "Potentially Related"
LABEL_UNRELATED: str = "Unrelated"

#: Field aliases accepted when reading a complaint dict.
TEXT_KEYS: Tuple[str, ...] = ("complaint_text", "text", "description")
CATEGORY_KEYS: Tuple[str, ...] = ("category", "complaint_category")

#: Vectoriser configuration mandated by the spec, kept in one place.
TFIDF_PARAMS: Dict[str, Any] = {
    "lowercase": True,
    "stop_words": "english",
    "ngram_range": (1, 2),
    "min_df": 1,
    "sublinear_tf": True,
}

DEFAULT_CATEGORY: str = "Uncategorized"


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


def get_text(complaint: Mapping[str, Any]) -> str:
    """Extract the complaint free-text, normalised to a stripped string.

    Args:
        complaint: A complaint mapping.

    Returns:
        The complaint text with surrounding whitespace removed; an empty
        string when the field is missing, ``None`` or whitespace-only.
    """
    value = _first_present(complaint, TEXT_KEYS, default="")
    return str(value).strip()


def get_category(complaint: Mapping[str, Any]) -> str:
    """Extract the complaint category, normalised to a stripped string.

    Args:
        complaint: A complaint mapping.

    Returns:
        The category string, or ``DEFAULT_CATEGORY`` when missing/blank.
    """
    value = _first_present(complaint, CATEGORY_KEYS, default="")
    text = str(value).strip()
    return text if text else DEFAULT_CATEGORY


def build_tfidf_matrix(texts: Sequence[str]) -> Tuple[spmatrix, TfidfVectorizer]:
    """Fit a TF-IDF vectoriser on ``texts`` and transform them.

    Args:
        texts: Sequence of document strings. ``None`` entries are treated as
            empty strings.

    Returns:
        A ``(sparse_matrix, vectorizer)`` tuple, where ``sparse_matrix`` has
        shape ``(len(texts), n_features)`` and ``vectorizer`` is the fitted
        :class:`~sklearn.feature_extraction.text.TfidfVectorizer`.

    Raises:
        ValueError: If ``texts`` is empty, or if the corpus yields an empty
            vocabulary (every document is blank or entirely stop words).
            Callers that want to tolerate this should catch ``ValueError``.
    """
    cleaned = ["" if t is None else str(t) for t in texts]
    if not cleaned:
        raise ValueError("build_tfidf_matrix requires at least one document, got an empty sequence")

    vectorizer = TfidfVectorizer(**TFIDF_PARAMS)
    # Raises ValueError("empty vocabulary; perhaps the documents only contain stop words")
    matrix = vectorizer.fit_transform(cleaned)
    return matrix, vectorizer


def compute_similarity_matrix(texts: Sequence[str]) -> np.ndarray:
    """Compute the pairwise cosine-similarity matrix for ``texts``.

    Degenerate corpora are handled rather than raised: an empty input yields a
    ``(0, 0)`` array, and a corpus with an empty vocabulary yields an identity
    matrix (each document is similar only to itself).

    Args:
        texts: Sequence of document strings.

    Returns:
        A dense ``numpy`` array of shape ``(n, n)`` with ``n = len(texts)``,
        values in ``[0.0, 1.0]``.

    Raises:
        ValueError: Never raised for degenerate corpora; propagated only for
            genuinely malformed input that ``TfidfVectorizer`` rejects for
            other reasons.
    """
    n = len(texts)
    if n == 0:
        return np.zeros((0, 0), dtype=float)

    try:
        matrix, _ = build_tfidf_matrix(texts)
    except ValueError:
        # Empty vocabulary: no usable tokens anywhere in this corpus.
        return np.eye(n, dtype=float)

    if matrix.shape[1] == 0:
        return np.eye(n, dtype=float)

    sims = cosine_similarity(matrix)
    sims = np.asarray(sims, dtype=float)
    # Numerical hygiene: clamp into range and force an exact unit diagonal.
    np.clip(sims, 0.0, 1.0, out=sims)
    np.fill_diagonal(sims, 1.0)
    return sims


def label_similarity(score: float) -> str:
    """Map a cosine-similarity score onto a human-readable label.

    Boundaries are inclusive at the bottom of each band:
    ``score >= 0.85`` -> ``"Potential Duplicate"``;
    ``0.55 <= score < 0.85`` -> ``"Potentially Related"``;
    otherwise ``"Unrelated"``.

    Args:
        score: A cosine-similarity score, normally in ``[0.0, 1.0]``.

    Returns:
        One of ``LABEL_DUPLICATE``, ``LABEL_RELATED`` or ``LABEL_UNRELATED``.

    Raises:
        ValueError: If ``score`` is not a finite number.
    """
    try:
        value = float(score)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"score must be a number, got {score!r}") from exc

    if not np.isfinite(value):
        raise ValueError(f"score must be finite, got {score!r}")

    if value >= DUPLICATE_THRESHOLD:
        return LABEL_DUPLICATE
    if value >= RELATED_THRESHOLD:
        return LABEL_RELATED
    return LABEL_UNRELATED


def group_by_category(complaints: Iterable[Mapping[str, Any]]) -> Dict[str, List[Mapping[str, Any]]]:
    """Group complaints by category, deterministically ordered.

    Categories are returned in sorted order and, within each category,
    complaints are sorted by the string form of ``complaint_id``. This keeps
    every downstream matrix index stable across runs.

    Args:
        complaints: Iterable of complaint mappings.

    Returns:
        An ordered ``dict`` mapping category name to its list of complaints.
        The complaint mappings themselves are the original objects (never
        copied or mutated here).

    Raises:
        ValueError: If a complaint is not a mapping or lacks ``complaint_id``.
    """
    buckets: Dict[str, List[Mapping[str, Any]]] = {}
    for complaint in complaints:
        if not isinstance(complaint, Mapping):
            raise ValueError(f"each complaint must be a mapping, got {type(complaint).__name__}")
        if complaint.get("complaint_id") is None:
            raise ValueError(f"complaint is missing a complaint_id: {dict(complaint)!r}")
        buckets.setdefault(get_category(complaint), []).append(complaint)

    return {
        category: sorted(items, key=lambda c: str(c["complaint_id"]))
        for category, items in sorted(buckets.items(), key=lambda kv: kv[0])
    }


def find_similar_pairs(complaints: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Find similar complaint pairs, comparing only within the same category.

    TF-IDF is fitted **per category**, not globally, so that IDF weights
    reflect the vocabulary of that complaint type. Self-pairs and pairs
    labelled ``"Unrelated"`` are excluded. Blank complaint texts and
    categories whose corpus yields an empty vocabulary simply produce no
    pairs rather than raising.

    Args:
        complaints: Sequence of complaint mappings. May be empty.

    Returns:
        A list of dicts, each with keys ``complaint_id_a``, ``complaint_id_b``,
        ``similarity_score`` (rounded to 4 decimal places) and ``label``.
        ``complaint_id_a`` is always the lexicographically smaller id, and the
        list is sorted by ``(complaint_id_a, complaint_id_b)`` within
        alphabetically ordered categories, so the output is deterministic.

    Raises:
        ValueError: If ``complaints`` is not a sequence of mappings, or if any
            complaint lacks ``complaint_id``.
    """
    if complaints is None:
        raise ValueError("complaints must be a sequence, got None")
    if isinstance(complaints, Mapping) or isinstance(complaints, (str, bytes)):
        raise ValueError("complaints must be a sequence of complaint mappings")

    grouped = group_by_category(complaints)

    pairs: List[Dict[str, Any]] = []
    for _category, members in grouped.items():
        if len(members) < 2:
            # Nothing to compare against.
            continue

        texts = [get_text(c) for c in members]
        if not any(texts):
            # Every text blank: no signal at all.
            continue

        sims = compute_similarity_matrix(texts)
        if sims.shape[0] != len(members):
            continue

        category_pairs: List[Dict[str, Any]] = []
        for i in range(len(members)):
            if not texts[i]:
                continue
            for j in range(i + 1, len(members)):
                if not texts[j]:
                    continue
                id_a = str(members[i]["complaint_id"])
                id_b = str(members[j]["complaint_id"])
                if id_a == id_b:
                    continue  # defensive: duplicate ids are not self-pairs

                score = float(sims[i, j])
                label = label_similarity(score)
                if label == LABEL_UNRELATED:
                    continue

                low, high = (id_a, id_b) if id_a <= id_b else (id_b, id_a)
                category_pairs.append(
                    {
                        "complaint_id_a": low,
                        "complaint_id_b": high,
                        "similarity_score": round(score, 4),
                        "label": label,
                    }
                )

        category_pairs.sort(key=lambda p: (p["complaint_id_a"], p["complaint_id_b"]))
        pairs.extend(category_pairs)

    return pairs