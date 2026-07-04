import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from app.core.logging import logger


# -------------------------------------------------
# Event tracing helpers
# -------------------------------------------------
def generate_event_id() -> str:
    return str(uuid.uuid4())


# -------------------------------------------------
# Core telemetry engine
# -------------------------------------------------
class PipelineTelemetryEngine:
    def __init__(self, window_size: int = 100):
        self._window_size = window_size
        self._durations = defaultdict(list)
        self._latencies = defaultdict(list)

    # -------------------------------------------------
    # internal rolling storage
    # -------------------------------------------------
    def _record(
        self,
        store: Dict[str, List[float]],
        component: str,
        value: float,
    ) -> None:
        history = store[component]
        history.append(value)

        if len(history) > self._window_size:
            history.pop(0)

    # -------------------------------------------------
    # component-level timing
    # -------------------------------------------------
    def record_duration(
        self,
        component: str,
        duration_ms: float,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        self._record(self._durations, component, duration_ms)

        logger.info(
            "pipeline_duration",
            extra={
                "extra_context": {
                    "component": component,
                    "duration_ms": round(duration_ms, 3),
                    "moving_average_ms": round(
                        self.get_average_duration(component),
                        3,
                    ),
                    **(metadata or {}),
                }
            },
        )

    def record_latency(
        self,
        component: str,
        latency_ms: float,
        metadata: Dict[str, Any] | None = None,
    ) -> None:

        self._record(self._latencies, component, latency_ms)

        logger.info(
            "pipeline_latency",
            extra={
                "extra_context": {
                    "component": component,
                    "latency_ms": round(latency_ms, 3),
                    "moving_average_ms": round(
                        self.get_average_latency(component),
                        3,
                    ),
                    **(metadata or {}),
                }
            },
        )

    # -------------------------------------------------
    # Event-level latency
    # -------------------------------------------------
    def record_event_latency(
        self,
        component: str,
        start_time: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Measures end-to-end latency for a single event.
        Returns latency in milliseconds.
        """
        latency_ms = (time.perf_counter() - start_time) * 1000

        self._record(self._latencies, component, latency_ms)

        logger.info(
            "pipeline_event_latency",
            extra={
                "extra_context": {
                    "component": component,
                    "latency_ms": round(latency_ms, 3),
                    "moving_average_ms": round(self.get_average_latency(component), 3),
                    **(metadata or {}),
                }
            },
        )

        return latency_ms

    # -------------------------------------------------
    # rolling averages
    # -------------------------------------------------
    def get_average_duration(self, component: str) -> float:
        values = self._durations.get(component, [])
        return sum(values) / len(values) if values else 0.0

    def get_average_latency(self, component: str) -> float:
        values = self._latencies.get(component, [])
        return sum(values) / len(values) if values else 0.0

    # -------------------------------------------------
    # context manager
    # -------------------------------------------------
    @contextmanager
    def measure(self, component: str):
        """
        Measures execution time of a code block.
        You can attach metadata dynamically via ctx dict.
        """
        start = time.perf_counter()
        metadata_ctx: Dict[str, Any] = {}

        try:
            yield metadata_ctx
        finally:
            duration = (time.perf_counter() - start) * 1000
            self.record_duration(component, duration)


telemetry = PipelineTelemetryEngine()
