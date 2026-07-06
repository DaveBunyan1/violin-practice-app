from contextlib import asynccontextmanager
import queue
import threading
from typing import Optional, Tuple

from fastapi import FastAPI

from app.controllers.session_controller import SessionController
from app.core.pipeline import run_segmentation_pipeline
from app.core.runtime import RuntimeGraph
from app.core.telemetry import DistributedTelemetryHarness
from app.core.logging import logger
from app.database.connection import Base, engine
from app.models.events import (
    PerformedNoteEvent,
    PitchObservationEvent,
    WebSocketBroadcastEvent,
)
from app.models.telemetry_models import TelemetryMeta
from app.pipeline.ingestion import AudioIngestionStream
from app.pipeline.note_processing_worker import NoteProcessingWorker
from app.pipeline.note_segmenter import NoteSegmenter
from app.pipeline.practice_target import PracticeTarget
from app.scoring.scoring_engine import ScoreEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events, safely wrapping
    the background real-time processing topology threads.
    """
    # 1. Initialize Telemetry & Database
    telemetry = DistributedTelemetryHarness()
    telemetry.start_session()
    logger.info("Syncing relational database structural schemas...")
    Base.metadata.create_all(bind=engine)

    # 2. Instantiate Queues
    pitch_queue: queue.Queue[Tuple[PitchObservationEvent, Optional[TelemetryMeta]]] = (
        queue.Queue()
    )
    segmented_queue: queue.Queue[Tuple[PerformedNoteEvent, Optional[TelemetryMeta]]] = (
        queue.Queue()
    )
    broadcast_queue: queue.Queue[
        Tuple[WebSocketBroadcastEvent, Optional[TelemetryMeta]]
    ] = queue.Queue()
    retry_queue: queue.Queue[Tuple[PerformedNoteEvent, Optional[TelemetryMeta]]] = (
        queue.Queue()
    )
    dead_letter_queue: queue.Queue[
        Tuple[PerformedNoteEvent, Optional[TelemetryMeta]]
    ] = queue.Queue()

    # 3. Instantiate Domain Components (Passing dependencies explicitly)
    target = PracticeTarget(mode="piece", active_piece=None)
    segmenter = NoteSegmenter(telemetry=telemetry)
    session_controller = SessionController(target, segmenter)
    score_engine = ScoreEngine(session_controller)

    # 4. Assemble the Runtime Graph
    runtime = RuntimeGraph(
        pitch_queue=pitch_queue,
        segmented_queue=segmented_queue,
        broadcast_queue=broadcast_queue,
        retry_queue=retry_queue,
        dead_letter_queue=dead_letter_queue,
        target=target,
        segmenter=segmenter,
        session_controller=session_controller,
        score_engine=score_engine,
        telemetry=telemetry,
    )

    # Expose graph to FastAPI endpoints via app.state
    app.state.runtime = runtime

    # Wire up Stage 2 (Segmentation) Callback
    def on_segmented(note: PerformedNoteEvent, trace: Optional[TelemetryMeta]):
        logger.info(
            f"Segmenter committed note: {note['note']}",
            extra={
                "extra_context": {
                    "duration": round(note["duration"], 2),
                    "avg_pitch_error_cents": note.get("avg_pitch_error_cents"),
                }
            },
        )
        runtime.segmented_queue.put((note, trace))

    runtime.segmenter.set_callback(on_segmented)

    # 6. Initialize Audio Ingestion Source
    audio_streamer = AudioIngestionStream(
        inbound_queue=runtime.pitch_queue, telemetry=runtime.telemetry
    )

    logger.info("Initializing system harness topology background threads.")

    # Thread A: Microphone Input Ingestion
    threading.Thread(target=audio_streamer.start, daemon=True).start()

    # Thread B: Note Segmentation State Machine
    threading.Thread(
        target=run_segmentation_pipeline,
        args=(runtime.pitch_queue, runtime.segmenter),
        daemon=True,
    ).start()

    # Thread C: Note Processing Worker
    worker = NoteProcessingWorker(
        controller=runtime.session_controller,
        inbound_queue=runtime.segmented_queue,
        broadcast_queue=runtime.broadcast_queue,
        retry_queue=runtime.retry_queue,
        dead_letter_queue=runtime.dead_letter_queue,
        telemetry=runtime.telemetry,
    )

    threading.Thread(target=worker.run, daemon=True).start()

    yield  # FastAPI Application Runs Here

    # 7. Teardown & Metrics Serialization
    app.state.runtime.shutdown()
    logger.info("Shutting down background service threads.")
