import queue

from app.models.session_controller import SessionController
from app.core.events import (
    PerformedNoteEvent,
    LiveDashboardMetrics,
    WebSocketBroadcastEvent,
)


def process_notes(
    controller: SessionController,
    inbound_queue: queue.Queue[PerformedNoteEvent],
    websocket_broadcast_queue: queue.Queue[WebSocketBroadcastEvent],
) -> None:
    """
    Pipeline stage:
    Raw pitch → LiveDashboardMetrics → session + websocket consumers
    """
    while True:
        event = inbound_queue.get()

        try:
            session = controller.get_session()
            if not controller.get_active_state():
                inbound_queue.task_done()
                continue

        except RuntimeError:
            inbound_queue.task_done()
            continue

        # -------------------------
        # 1. Transform input event
        # -------------------------
        relative_time = event["timestamp"] - session.start_time

        expected = controller.target.get_expected_note(relative_time)

        metrics: LiveDashboardMetrics = {
            "frequency": event["frequency"],
            "note": event["note"],
            "time": relative_time,
            "expected_note": expected,
        }

        # -------------------------
        # 2. Side effect: session storage
        # -------------------------
        relative_event: PerformedNoteEvent = {
            "note": event["note"],
            "frequency": event["frequency"],
            "timestamp": relative_time,
        }
        print("RELATIVE EVENT (from pipeline.py)")
        print(relative_event)

        if relative_event["note"] != "REST":
            session.add_performed_note(relative_event)

        session.add_event(metrics)

        print(len(session.get_performed_notes()))

        # -------------------------
        # 3. Side effect: websocket output
        # -------------------------
        websocket_broadcast_queue.put(
            {
                "type": "pitch",
                "data": metrics,
            }
        )

        inbound_queue.task_done()
