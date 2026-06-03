from models.session_controller import SessionController
from core.events import note_queue, NoteEvent, WebSocketBroadcastEvent
import time
import queue


def handle_note(freq: float, note: str) -> None:
    event: NoteEvent = {"frequency": freq, "note": note, "timestamp": time.time()}

    note_queue.put(event)


def process_notes(
    controller: SessionController,
    inbound_queue: queue.Queue[NoteEvent],
    websocket_broadcast_queue: queue.Queue[WebSocketBroadcastEvent],
) -> None:
    """
    Consumes raw audio pitch events, evaluates expectations,
    saves them to the session, and pipes them out to the WebSocket layer.
    """
    while True:
        event = inbound_queue.get()

        try:
            session = controller.get_session()
        except RuntimeError:
            # Skip processing if user hasn't active/started a session yet
            inbound_queue.task_done()
            continue

        freq = event["frequency"]
        note = event["note"]

        relative_time = event["timestamp"] - session.start_time

        expected = controller.target.get_expected_note(relative_time)

        session.add_note(
            note=note,
            frequency=freq,
            relative_time=relative_time,
            expected_note=expected,
        )

        # 4. Push down the line to the WebSocket broadcast loop
        # This gives your frontend the exact note data + the calculated expected note
        websocket_broadcast_queue.put(
            {
                "type": "pitch",
                "data": {
                    "frequency": freq,
                    "note": note,
                    "time": relative_time,
                    "expected_note": expected,
                },
            }
        )

        inbound_queue.task_done()
