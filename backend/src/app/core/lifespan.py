import asyncio
from contextlib import asynccontextmanager
import queue
import threading

from fastapi import FastAPI

from app.controllers.session_controller import SessionController
from app.core.event_bus import EventBus
from app.core.pipeline import run_segmentation_pipeline
from app.core.runtime import RuntimeGraph
from app.models.events import PerformedNoteEvent, PitchObservationEvent
from app.pipeline.ingestion import AudioIngestionStream
from app.pipeline.note_processing_worker import NoteProcessingWorker
from app.pipeline.note_segmenter import NoteSegmenter
from app.scoring.scoring_engine import ScoreEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages startup/shutdown of the full real-time processing graph.
    """
    # ----------------------------
    # queues (still valid for pipeline stages)
    # ----------------------------
    pitch_queue: queue.Queue[PitchObservationEvent] = queue.Queue()
    segmented_queue: queue.Queue[PerformedNoteEvent] = queue.Queue()
    retry_queue: queue.Queue[PerformedNoteEvent] = queue.Queue()
    dead_letter_queue: queue.Queue[PerformedNoteEvent] = queue.Queue()

    # ----------------------------
    # event bus (NEW backbone for UI + observers)
    # ----------------------------
    event_bus = EventBus()

    # ----------------------------
    # core components
    # ----------------------------
    segmenter = NoteSegmenter(stability_threshold=0.1)

    audio_streamer = AudioIngestionStream(inbound_queue=pitch_queue)

    session_controller = SessionController(segmenter=segmenter)
    score_engine = ScoreEngine(session_controller)

    runtime = RuntimeGraph(
        pitch_queue=pitch_queue,
        segmented_queue=segmented_queue,
        event_bus=event_bus,
        retry_queue=retry_queue,
        dead_letter_queue=dead_letter_queue,
        segmenter=segmenter,
        session_controller=session_controller,
        score_engine=score_engine,
    )

    app.state.runtime = runtime

    # ----------------------------
    # callback wiring (segmenter → queue)
    # ----------------------------
    def on_segmented(note: PerformedNoteEvent):
        segmented_queue.put(note)

    segmenter.set_callback(on_segmented)

    # ----------------------------
    # threads (runtime topology)
    # ----------------------------
    threading.Thread(target=audio_streamer.start, daemon=True).start()

    threading.Thread(
        target=run_segmentation_pipeline,
        args=(pitch_queue, segmenter),
        daemon=True,
    ).start()

    worker = NoteProcessingWorker(
        controller=session_controller,
        inbound_queue=segmented_queue,
        event_bus=event_bus,
        retry_queue=retry_queue,
        dead_letter_queue=dead_letter_queue,
        loop=asyncio.get_running_loop(),
    )

    threading.Thread(target=worker.run, daemon=True).start()

    yield
