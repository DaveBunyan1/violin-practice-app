import queue
import threading

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core application imports
from app.pipeline.ingestion import AudioIngestionStream
from app.core.shared_engines import (
    session_controller,
)
from app.core.pipeline import run_segmentation_pipeline
from app.models.events import (
    PerformedNoteEvent,
)

from app.models.router_models import HealthCheckReturn
from app.pipeline.note_segmenter import NoteSegmenter

from app.api.v1.repertoire import router as repertoire_router
from app.api.v1.session import router as session_router
from app.api.v1.telemetry import router as telemetry_router
from app.pipeline.note_processing_worker import NoteProcessingWorker


# -----------------------------------------------------------------
# 1. FastAPI Lifespan (Thread Topology Management)
# -----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events, safely wrapping
    the background real-time processing topology threads.
    """

    # ----------------------------
    # queues (data channels)
    # ----------------------------
    pitch_queue = queue.Queue()
    segmented_queue = queue.Queue()
    broadcast_queue = queue.Queue()
    retry_queue = queue.Queue()
    dead_letter_queue = queue.Queue()

    # ----------------------------
    # core components
    # ----------------------------
    segmenter = NoteSegmenter(stability_threshold=0.1)

    def on_segmented(note: PerformedNoteEvent):
        segmented_queue.put(note)

    segmenter.set_callback(on_segmented)

    audio_streamer = AudioIngestionStream(inbound_queue=pitch_queue)

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
        websocket_broadcast_queue=broadcast_queue,
        retry_queue=retry_queue,
        dead_letter_queue=dead_letter_queue,
    )

    threading.Thread(target=worker.run, daemon=True).start()

    yield


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
