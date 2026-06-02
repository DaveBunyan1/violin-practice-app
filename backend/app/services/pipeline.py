from core.events import note_queue, NoteEvent
import time
from services.session import session


def handle_note(freq: float, note: str) -> None:
    event: NoteEvent = {"frequency": freq, "note": note, "timestamp": time.time()}

    note_queue.put(event)


def process_notes():
    while True:
        event = note_queue.get()

        freq = event["frequency"]
        note = event["note"]

        session.add_note(note, freq, expected_note=None)
