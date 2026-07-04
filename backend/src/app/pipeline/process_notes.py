import queue
import time
from typing import Optional, Tuple

from app.controllers.session_controller import SessionController
from app.core.telemetry import telemetry
from app.models.events import (
    PerformedNoteEvent,
    LiveDashboardMetrics,
    WebSocketBroadcastEvent,
)
from app.models.telemetry_models import TelemetryMeta


def process_notes(
    controller: SessionController,
    inbound_queue: queue.Queue[Tuple[PerformedNoteEvent, Optional[TelemetryMeta]]],
    websocket_broadcast_queue: queue.Queue[
        Tuple[WebSocketBroadcastEvent, Optional[TelemetryMeta]]
    ],
) -> None:
    """
    Pipeline stage:
    PerformedNoteEvent → SessionEvent + LiveDashboardMetrics
    """
    while True:
        event, trace = inbound_queue.get()

        try:
            session = controller.get_session()

            if not controller.is_active():
                inbound_queue.task_done()
                if trace:
                    telemetry.complete_trace(trace)
                continue

        except RuntimeError:
            inbound_queue.task_done()
            if trace:
                telemetry.complete_trace(trace)
            continue

        # ------------------------------------------------
        # 1. Normalize time (single source of truth)
        # ------------------------------------------------
        relative_start = event["start_time"] - session.start_time
        relative_end = event["end_time"] - session.start_time

        # ------------------------------------------------
        # 2. Expected note lookup (time-based)
        # ------------------------------------------------
        expected = controller.target.get_expected_note(relative_start)

        # ------------------------------------------------
        # 3. Session event (clean storage format)
        # ------------------------------------------------
        avg_cents = event.get("avg_pitch_error_cents")

        session.add_performed_note(
            {
                "note": event["note"],
                "frequency": event["frequency"],
                "start_time": relative_start,
                "end_time": relative_end,
                "duration": event["duration"],
                "avg_pitch_error_cents": avg_cents,
            }
        )

        # ------------------------------------------------
        # 4. Live UI metrics
        # ------------------------------------------------
        metrics: LiveDashboardMetrics = {
            "frequency": event["frequency"],
            "note": event["note"],
            "time": relative_start,
            "expected_note": expected,
            "pitch_cents_error": avg_cents,
        }

        # ------------------------------------------------
        # 5. WebSocket output
        # ------------------------------------------------
        if trace:
            trace["t_process"] = time.perf_counter()

        websocket_broadcast_queue.put(
            (
                {
                    "type": "pitch",
                    "data": metrics,
                },
                trace,
            )
        )

        event, trace = websocket_broadcast_queue.get()
        if trace:
            telemetry.complete_trace(trace)
        inbound_queue.task_done()
