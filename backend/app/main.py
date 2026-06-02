import audio.record as record
from websocket.server import run as run_server
import threading
import asyncio

from services.pipeline import handle_note, process_notes


async def main():
    record.on_note_detected = handle_note
    threading.Thread(target=record.start_audio_stream, daemon=True).start()
    threading.Thread(target=process_notes, daemon=True).start()

    await run_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
