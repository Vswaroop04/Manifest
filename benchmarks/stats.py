"""
Statistical helpers used by both geocoding and routing benchmarks.

Percentiles use linear interpolation (same as numpy's default).
Relative error = |measured - expected| / expected * 100.
"""
import math
import statistics
from typing import Sequence


def percentile(data: Sequence[float], p: float) -> float:
    """Return the p-th percentile of data (0 ≤ p ≤ 100), linear interpolation."""
    if not data:
        raise ValueError("data is empty")
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    idx = (p / 100) * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    return sorted_data[lo] + (idx - lo) * (sorted_data[hi] - sorted_data[lo])


def latency_stats(latencies: Sequence[float]) -> dict:
    """Full latency profile with mean, stdev, and key percentiles."""
    s = sorted(latencies)
    return {
        "mean":   round(statistics.mean(s), 2),
        "stdev":  round(statistics.stdev(s), 2) if len(s) > 1 else 0.0,
        "min":    round(s[0], 2),
        "p50":    round(percentile(s, 50), 2),
        "p90":    round(percentile(s, 90), 2),
        "p95":    round(percentile(s, 95), 2),
        "p99":    round(percentile(s, 99), 2),
        "max":    round(s[-1], 2),
    }


def error_stats(errors: Sequence[float]) -> dict:
    """Distribution of distance/relative errors."""
    if not errors:
        return {k: None for k in ["mean", "stdev", "p50", "p90", "p95", "p99", "max"]}
    s = sorted(errors)
    return {
        "mean":   round(statistics.mean(s), 3),
        "stdev":  round(statistics.stdev(s), 3) if len(s) > 1 else 0.0,
        "p50":    round(percentile(s, 50), 3),
        "p90":    round(percentile(s, 90), 3),
        "p95":    round(percentile(s, 95), 3),
        "p99":    round(percentile(s, 99), 3),
        "max":    round(max(s), 3),
    }


def relative_error(measured: float, expected: float) -> float:
    """Relative error as a percentage: |measured - expected| / expected * 100."""
    if expected == 0:
        return 0.0
    return abs(measured - expected) / expected * 100


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
