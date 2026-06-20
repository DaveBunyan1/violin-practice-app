import asyncio
import threading
import queue

# Core application imports
from app.audio.ingestion import AudioIngestionStream
from app.scoring.scoring_engine import ScoreEngine
from app.services.note_segmenter import NoteSegmenter
from app.core.events import (
    PitchObservationEvent,
    PerformedNoteEvent,
    WebSocketBroadcastEvent,
)
from app.models.session_controller import SessionController
from app.models.practice_target import ExpectedNote, PracticeTarget
from app.services.pipeline import process_notes

# Websocket server and event structures
from app.websocket.server import run as run_server, create_handler, broadcaster

# ---------------------------------------------------
# 1. Initialize Domain Objects & Targets
# ---------------------------------------------------
target = PracticeTarget(
    mode="piece",
    notes=[
        ExpectedNote("G3", 1),
        ExpectedNote("D4", 2),
        ExpectedNote("A4", 3),
        ExpectedNote("E5", 4),
    ],
)

segmenter = NoteSegmenter()
controller = SessionController(target, segmenter)
score_engine = ScoreEngine(controller)


def run_segmentation_pipeline(
    inbound_raw_queue: queue.Queue[PitchObservationEvent],
) -> None:
    """
    Worker Loop Thread: Pulls raw observations from the queue
    and passes them to the segmenter's state machine.
    """
    while True:
        try:
            # Block until a raw pitch event is available from the microphone thread
            raw_event = inbound_raw_queue.get(timeout=1.0)
            segmenter.process(raw_event)
            inbound_raw_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print("SEGMENTATION THREAD CRASH", e)


# ---------------------------------------------------
# 2. Async Runtime Entrypoint
# ---------------------------------------------------
async def main():
    # Explicitly instantiate thread-safe queues
    pitch_queue: queue.Queue[PitchObservationEvent] = queue.Queue()
    segmented_queue: queue.Queue[PerformedNoteEvent] = queue.Queue()
    broadcast_queue: queue.Queue[WebSocketBroadcastEvent] = queue.Queue()

    # Wire up Stage 2 (Segmentation) output to pipe into Stage 3
    def on_segmented(note: PerformedNoteEvent):
        segmented_queue.put(note)

    segmenter.set_callback(on_segmented)

    # Instantiate Object-Oriented Audio Ingestion
    audio_streamer = AudioIngestionStream(inbound_queue=pitch_queue)

    # ---------------------------------------------------
    # Threading Topology Configuration
    # ---------------------------------------------------

    # Thread A: Microphone Engine & DSP Frequency Detection -> Pushes to pitch_queue
    threading.Thread(target=audio_streamer.start, daemon=True).start()

    # Thread B: Listens to pitch_queue -> Runs NoteSegmenter State Machine -> Pushes to segmented_queue
    threading.Thread(
        target=run_segmentation_pipeline, args=(pitch_queue,), daemon=True
    ).start()

    # Thread C: Listens to segmented_queue -> Sequence Alignment & Evaluation -> Pushes to broadcast_queue
    threading.Thread(
        target=process_notes,
        args=(controller, segmented_queue, broadcast_queue),
        daemon=True,
    ).start()

    # ---------------------------------------------------
    # Async WebSocket Infrastructure Context
    # ---------------------------------------------------
    handler = create_handler(controller, score_engine)
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
