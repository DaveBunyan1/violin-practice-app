from core.events import note_queue


def handle_note(freq: float, note: str) -> None:
    note_queue.put((freq, note))
