from models.session_controller import SessionController
from core.events import note_queue, NoteEvent
import time


def handle_note(freq: float, note: str) -> None:
    event: NoteEvent = {"frequency": freq, "note": note, "timestamp": time.time()}

    note_queue.put(event)


def process_notes(controller: SessionController):
    while True:
        event = note_queue.get()

        freq = event["frequency"]
        note = event["note"]

        current_time = controller.get_current_time()

        expected = controller.target.get_expected_note(current_time)

        session = controller.get_session()

        session.add_note(
            note=note,
            frequency=freq,
            expected_note=expected,
        )
