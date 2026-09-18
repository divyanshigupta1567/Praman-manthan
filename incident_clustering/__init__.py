# ml/__init__.py
"""Praman incident-clustering library.

Importable, dependency-light (pandas / numpy / scikit-learn / networkx only),
with no Flask, no database and no global state. The backend only ever needs::

    from ml.clustering import cluster_complaints
    incidents = cluster_complaints(complaints)
"""

from __future__ import annotations

from .clustering import cluster_complaints
from .similarity import find_similar_pairs

__all__ = ["cluster_complaints", "find_similar_pairs"]

__version__ = "0.1.0"