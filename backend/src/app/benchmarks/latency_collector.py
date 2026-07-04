import statistics
from collections import defaultdict
from typing import List, Dict

from app.models.benchmark_models import LatencySummary


class LatencyCollector:
    def __init__(self):
        self.samples: Dict[str, List[float]] = defaultdict(list)

    def record(self, scenario: str, value_ms: float):
        self.samples[scenario].append(value_ms)

    def summary(self, scenario: str) -> LatencySummary | None:
        data = self.samples[scenario]
        if not data:
            return None

        data_sorted = sorted(data)

        def percentile(p: float) -> float:
            k = int(len(data_sorted) * p)
            return data_sorted[min(k, len(data_sorted) - 1)]

        return {
            "count": len(data),
            "mean": statistics.mean(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
        }
