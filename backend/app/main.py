import asyncio
import threading
import queue

# Core application imports
import audio.record as record
from core.events import NoteEvent, WebSocketBroadcastEvent
from models.session_controller import SessionController
from models.practice_target import ExpectedNote, PracticeTarget
from services.pipeline import process_notes

# Websocket server and event structures
from websocket.server import run as run_server, create_handler, broadcaster

# ---------------------------------------------------
# 1. Initialize Domain Objects & Targets
# ---------------------------------------------------
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


# ---------------------------------------------------
# 2. Async Runtime Entrypoint
# ---------------------------------------------------
async def main():
    # Explicitly instantiate thread-safe queues
    inbound_queue: queue.Queue[NoteEvent] = queue.Queue()
    broadcast_queue: queue.Queue[WebSocketBroadcastEvent] = queue.Queue()

    # Wire up the audio recorder callback to put raw events into the inbound queue
    def handle_incoming_audio_note(event: NoteEvent) -> None:
        inbound_queue.put(event)

    record.on_note_detected = handle_incoming_audio_note

    # A. Spin up the Audio Streaming Thread
    threading.Thread(target=record.start_audio_stream, daemon=True).start()

    # B. Spin up the Note Processing Pipeline Thread
    threading.Thread(
        target=process_notes,
        args=(controller, inbound_queue, broadcast_queue),
        daemon=True,
    ).start()

    # ---------------------------------------------------
    # 3. WebSocket Configuration & Factory Wiring
    # ---------------------------------------------------
    # Create the incoming WebSocket action handler
    handler = create_handler(controller)

    # Wrap the broadcaster execution in a lambda factory.
    # This defers execution so server.py can invoke it safely within its running event loop.
    broadcaster_task_factory = lambda: broadcaster(broadcast_queue)

    await run_server(handler, broadcaster_task_factory)


# ---------------------------------------------------
# 4. Process Bootstrap
# ---------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down backend services...")
