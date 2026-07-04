from typing import TypedDict


class LatencySummary(TypedDict):
    count: int
    mean: float
    stdev: float
    min: float
    max: float
    p50: float
    p95: float
    p99: float
