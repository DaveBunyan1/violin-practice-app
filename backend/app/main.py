import audio.record as record
from models.session_controller import SessionController
from models.practice_target import ExpectedNote, PracticeTarget

from websocket.server import run as run_server
import threading
import asyncio

from services.pipeline import handle_note, process_notes

target = PracticeTarget(
    mode="piece",
    notes=[
        ExpectedNote("A4", 0),
        ExpectedNote("B4", 1),
        ExpectedNote("C#5", 2),
        ExpectedNote("D5", 3),
    ],
)

controller = SessionController(target)
controller.start_session(target)


async def main():
    record.on_note_detected = handle_note
    threading.Thread(target=record.start_audio_stream, daemon=True).start()
    threading.Thread(target=process_notes, args=(controller,), daemon=True).start()

    await run_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
