import time
import random

from app.models.events import PerformedNoteEvent


def generate_fake_event(i: int) -> PerformedNoteEvent:
    now = time.perf_counter()

    return {
        "note": "A4",
        "frequency": 440.0,
        "avg_pitch_error_cents": random.uniform(-10.0, 10.0),
        "start_time": now,
        "end_time": now + 0.05,
        "duration": 0.05,
        "retry_count": 0,
        "telemetry": {
            "event_id": f"test-{i}",
            "created_at": now,
        },
    }
