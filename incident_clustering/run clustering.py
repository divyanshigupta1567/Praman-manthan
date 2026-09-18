#!/usr/bin/env python3
# scripts/run_clustering.py
"""CLI wrapper around :func:`ml.clustering.cluster_complaints`.

Reads a complaints CSV, clusters it, writes pretty-printed JSON incidents and
prints a small summary table. This is the ONLY file in the module allowed to
print; everything under ``ml/`` stays silent and side-effect free.

SCHEMA ASSUMPTION: the CSV is expected to have the columns
``complaint_id, complaint_text, category, latitude, longitude, timestamp,
status``. Extra columns are ignored; ``lat``/``lng``/``lon`` are accepted as
aliases. Rows with missing coordinates or unparseable timestamps are skipped
and reported under "warnings".

Usage::

    python scripts/run_clustering.py
    python scripts/run_clustering.py data/complaints.csv
    python scripts/run_clustering.py --input data/complaints.csv --output data/incidents.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

# Allow "python scripts/run_clustering.py" from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from incident_clustering.clustering import cluster_complaints_with_warnings  # noqa: E402

DEFAULT_INPUT = Path("data/complaints.csv")
DEFAULT_OUTPUT = Path("data/incidents.json")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Supports both a positional path and ``--input`` for convenience.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        The parsed namespace with ``input``, ``output`` and ``quiet``.

    Raises:
        SystemExit: On malformed arguments (argparse behaviour).
    """
    parser = argparse.ArgumentParser(description="Cluster Praman complaints into incidents.")
    parser.add_argument("positional_input", nargs="?", default=None, help="Path to the complaints CSV.")
    parser.add_argument("--input", "-i", default=None, help=f"Path to the complaints CSV (default: {DEFAULT_INPUT}).")
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT), help=f"Output JSON path (default: {DEFAULT_OUTPUT}).")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress the summary table.")

    args = parser.parse_args(argv)
    args.input = args.input or args.positional_input or str(DEFAULT_INPUT)
    return args


def load_complaints(csv_path: Path) -> List[Dict[str, Any]]:
    """Load complaints from a CSV into a list of plain dicts.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        A list of complaint dicts with NaN values replaced by ``None``.

    Raises:
        FileNotFoundError: If the CSV does not exist.
        ValueError: If the CSV has no ``complaint_id`` column.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"complaints CSV not found: {csv_path}")

    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    if "complaint_id" not in frame.columns:
        raise ValueError(f"{csv_path} has no 'complaint_id' column (found: {list(frame.columns)})")

    records: List[Dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        records.append({key: (None if pd.isna(value) else value) for key, value in row.items()})
    return records


def summarise(incidents: Sequence[Dict[str, Any]]) -> List[tuple[str, str]]:
    """Build the rows of the summary table.

    Args:
        incidents: The incident dicts returned by the clustering pipeline.

    Returns:
        A list of ``(label, value)`` string pairs.
    """
    if not incidents:
        return [("Clusters found", "0"), ("Largest cluster", "-"), ("Avg radius (km)", "-")]

    largest = max(incidents, key=lambda i: i["complaint_count"])
    avg_radius = sum(i["cluster_radius_km"] for i in incidents) / len(incidents)
    total_complaints = sum(i["complaint_count"] for i in incidents)
    categories = sorted({i["category"] for i in incidents})

    return [
        ("Clusters found", str(len(incidents))),
        ("Complaints clustered", str(total_complaints)),
        ("Largest cluster", f"{largest['incident_id']} ({largest['complaint_count']} complaints)"),
        ("Avg radius (km)", f"{avg_radius:.3f}"),
        ("Categories", ", ".join(categories)),
    ]


def print_table(rows: Sequence[tuple[str, str]]) -> None:
    """Print a two-column table with aligned separators.

    Args:
        rows: ``(label, value)`` pairs.

    Returns:
        None.
    """
    if not rows:
        return
    label_width = max(len(label) for label, _ in rows)
    value_width = max(len(value) for _, value in rows)
    rule = "+" + "-" * (label_width + 2) + "+" + "-" * (value_width + 2) + "+"

    print(rule)
    for label, value in rows:
        print(f"| {label.ljust(label_width)} | {value.ljust(value_width)} |")
    print(rule)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` on a handled input error.
    """
    args = parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        complaints = load_complaints(input_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    incidents, warnings = cluster_complaints_with_warnings(complaints)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(incidents, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"Read {len(complaints)} complaints from {input_path}")
        print(f"Wrote {len(incidents)} incidents to {output_path}")
        print()
        print_table(summarise(incidents))
        if warnings:
            print(f"\n{len(warnings)} row(s) skipped:")
            for warning in warnings[:10]:
                print(f"  - {warning}")
            if len(warnings) > 10:
                print(f"  ... and {len(warnings) - 10} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())