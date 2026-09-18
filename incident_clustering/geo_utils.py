# ml/geo_utils.py
"""Geospatial helpers for the Praman incident-clustering module.

SCHEMA ASSUMPTION (the shared schema block was left as a paste placeholder):
this module is schema-agnostic. It only deals with raw numeric latitude and
longitude values; the complaint/incident field names are assumed in
``ml/clustering.py`` and documented there.

Pure functions, no global state, no printing.
"""

from __future__ import annotations

from typing import Union

import numpy as np

__all__ = ["EARTH_RADIUS_KM", "MIN_LAT", "MAX_LAT", "MIN_LON", "MAX_LON", "haversine_km"]

#: Mean Earth radius in kilometres, as mandated by the spec.
EARTH_RADIUS_KM: float = 6371.0

MIN_LAT: float = -90.0
MAX_LAT: float = 90.0
MIN_LON: float = -180.0
MAX_LON: float = 180.0

Number = Union[float, int, np.ndarray]


def _coerce(value: Number, name: str) -> np.ndarray:
    """Coerce a coordinate input to a float numpy array.

    Args:
        value: Scalar or array-like coordinate value.
        name: Parameter name, used in error messages.

    Returns:
        A float64 numpy array (0-d for scalar input).

    Raises:
        ValueError: If the value cannot be interpreted as float, or contains
            NaN / infinite entries.
    """
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a float or an array of floats, got {value!r}") from exc

    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values: {value!r}")

    return arr


def _validate_range(arr: np.ndarray, name: str, low: float, high: float) -> None:
    """Validate that every element of ``arr`` lies within ``[low, high]``.

    Args:
        arr: Float array to check.
        name: Parameter name, used in error messages.
        low: Inclusive lower bound.
        high: Inclusive upper bound.

    Returns:
        None.

    Raises:
        ValueError: If any element is outside the closed interval.
    """
    if np.any(arr < low) or np.any(arr > high):
        bad = arr[(arr < low) | (arr > high)] if arr.ndim else arr
        raise ValueError(f"{name} must be within [{low}, {high}], got {bad.tolist() if arr.ndim else float(arr)}")


def haversine_km(
    lat1: Number,
    lon1: Number,
    lat2: Number,
    lon2: Number,
) -> Union[float, np.ndarray]:
    """Great-circle distance between two points (or two sets of points).

    Accepts scalars or numpy arrays; array arguments are broadcast against each
    other, so this can be used to compute a whole column of distances at once
    (for example centroid-to-members).

    Args:
        lat1: Latitude(s) of the first point, in decimal degrees, in [-90, 90].
        lon1: Longitude(s) of the first point, in decimal degrees, in [-180, 180].
        lat2: Latitude(s) of the second point, in decimal degrees, in [-90, 90].
        lon2: Longitude(s) of the second point, in decimal degrees, in [-180, 180].

    Returns:
        The distance in kilometres. A ``float`` when all four inputs are
        scalars, otherwise a numpy array of the broadcast shape.

    Raises:
        ValueError: If any coordinate is non-numeric, NaN/infinite, or outside
            its valid range.
    """
    a_lat = _coerce(lat1, "lat1")
    a_lon = _coerce(lon1, "lon1")
    b_lat = _coerce(lat2, "lat2")
    b_lon = _coerce(lon2, "lon2")

    _validate_range(a_lat, "lat1", MIN_LAT, MAX_LAT)
    _validate_range(b_lat, "lat2", MIN_LAT, MAX_LAT)
    _validate_range(a_lon, "lon1", MIN_LON, MAX_LON)
    _validate_range(b_lon, "lon2", MIN_LON, MAX_LON)

    phi1 = np.radians(a_lat)
    phi2 = np.radians(b_lat)
    d_phi = phi2 - phi1
    d_lambda = np.radians(b_lon - a_lon)

    h = np.sin(d_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lambda / 2.0) ** 2
    # Clip guards against tiny floating-point overshoot above 1.0.
    central_angle = 2.0 * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))
    distance = EARTH_RADIUS_KM * central_angle

    if np.ndim(distance) == 0:
        return float(distance)
    return distance