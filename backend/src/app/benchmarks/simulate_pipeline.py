import time
from typing import Callable

from app.benchmarks.run_latency_test import generate_fake_event
from app.benchmarks.latency_collector import LatencyCollector
from app.models.events import PerformedNoteEvent

collector = LatencyCollector()


def run_test(
    worker_fn: Callable[[PerformedNoteEvent], None], n: int = 1000, label: str = "queue"
):
    for i in range(n):
        event = generate_fake_event(i)

        start = event["telemetry"]["created_at"]

        worker_fn(event)

        end = time.perf_counter()

        latency = (end - start) * 1000
        collector.record(label, latency)


def print_results(label: str):
    print(f"\n=== {label} ===")
    print(collector.summary(label))
