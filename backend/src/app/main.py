import threading

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core application imports
from app.pipeline.ingestion import AudioIngestionStream
from app.core.shared_engines import (
    segmenter,
    session_controller,
    pitch_queue,
    broadcast_queue,
    segmented_queue,
)
from app.core.pipeline import run_segmentation_pipeline
from app.models.events import (
    PerformedNoteEvent,
)
from app.core.logging import logger

from app.models.router_models import HealthCheckReturn
from app.pipeline.process_notes import process_notes
from app.api.v1.repertoire import router as repertoire_router
from app.api.v1.session import router as session_router
from app.api.v1.telemetry import router as telemetry_router

# Database imports
from app.database.connection import engine, Base


# -----------------------------------------------------------------
# 1. FastAPI Lifespan (Thread Topology Management)
# -----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events, safely wrapping
    the background real-time processing topology threads.
    """

    logger.info("Syncing relational database structural schemas...")
    Base.metadata.create_all(bind=engine)

    # Wire up Stage 2 (Segmentation) callback to queue
    def on_segmented(note: PerformedNoteEvent):
        logger.info(
            f"Segmenter committed note: {note['note']}",
            extra={
                "extra_context": {
                    "duration": round(note["duration"], 2),
                    "avg_pitch_error_cents": note.get("avg_pitch_error_cents"),
                }
            },
        )
        segmented_queue.put(note)

    segmenter.set_callback(on_segmented)

    # Instantiate Object-Oriented Audio Ingestion
    audio_streamer = AudioIngestionStream(inbound_queue=pitch_queue)

    logger.info("Initializing system harness topology background threads.")

    # Thread A: Microphone Input Ingestion
    threading.Thread(target=audio_streamer.start, daemon=True).start()

    # Thread B: Note Segmentation State Machine
    threading.Thread(
        target=run_segmentation_pipeline, args=(pitch_queue,), daemon=True
    ).start()

    # Thread C: Sequence Alignment & Scoring Engine
    threading.Thread(
        target=process_notes,
        args=(session_controller, segmented_queue, broadcast_queue),
        daemon=True,
    ).start()

    yield  # FastAPI Application Runs Here

    logger.info("Shutting down background service threads.")


# -----------------------------------------------------------------
# 2. FastAPI Initialization
# -----------------------------------------------------------------
app = FastAPI(
    title="Violin Intonation Pipeline API",
    version="1.3.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> HealthCheckReturn:
    return {
        "status": "healthy",
        "version": "1.3.0",
        "session_active": session_controller.is_active(),
    }


app.include_router(repertoire_router, prefix="/repertoire", tags=["repertoire"])
app.include_router(session_router, prefix="/session", tags=["session"])
app.include_router(telemetry_router, tags=["telemetry"])
