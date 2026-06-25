import asyncio
import threading
import queue
from contextlib import asynccontextmanager
from typing import TypedDict, cast
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone

# Core application imports
from app.audio.ingestion import AudioIngestionStream
from app.scoring.scoring_engine import ScoreEngine
from app.services.note_segmenter import NoteSegmenter
from app.core.events import (
    PitchObservationEvent,
    PerformedNoteEvent,
    ScoreResult,
    WebSocketBroadcastEvent,
)
from app.core.logging import logger
from app.models.session_controller import SessionController
from app.models.practice_target import ExpectedNote, PracticeTarget
from app.services.pipeline import process_notes

# Database imports
from app.database.connection import get_db, engine, Base
import app.database.models as db_models

# -----------------------------------------------------------------
# 1. Initialize Long-Lived Domain Objects (Singletons)
# -----------------------------------------------------------------
target = PracticeTarget(
    mode="piece",
    notes=[
        ExpectedNote("G3", 1),
        ExpectedNote("D4", 2),
        ExpectedNote("A4", 3),
        ExpectedNote("E5", 4),
    ],
)

Base.metadata.create_all(bind=engine)

segmenter = NoteSegmenter()

session_controller = SessionController(target, segmenter)
score_engine = ScoreEngine(session_controller)

# Thread safe queues mapped globally for routes to access
pitch_queue: queue.Queue[PitchObservationEvent] = queue.Queue()
segmented_queue: queue.Queue[PerformedNoteEvent] = queue.Queue()
broadcast_queue: queue.Queue[WebSocketBroadcastEvent] = queue.Queue()


def run_segmentation_pipeline(
    inbound_raw_queue: queue.Queue[PitchObservationEvent],
) -> None:
    """Worker Loop Thread: Pulls raw observations and passes them to the segmenter."""
    logger.info("Segmentation background thread worker started.")

    while True:
        try:
            raw_event = inbound_raw_queue.get(timeout=1.0)

            logger.debug(
                f"Processing raw frame: {raw_event['note']}",
                extra={
                    "extra_context": {
                        "frequency": round(raw_event["frequency"], 1),
                        "pitch_cents_error": raw_event.get("pitch_cents_error"),
                    }
                },
            )
            segmenter.process(raw_event)
            inbound_raw_queue.task_done()
        except queue.Empty:
            continue
        except Exception:
            logger.error(
                "Segmentation thread encountered a critical error.", exc_info=True
            )


# -----------------------------------------------------------------
# 2. FastAPI Lifespan (Thread Topology Management)
# -----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events, safely wrapping
    the background real-time processing topology threads.
    """

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
# 3. FastAPI Initialization
# -----------------------------------------------------------------
app = FastAPI(
    title="Violin Intonation Pipeline API", version="1.3.0", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheckReturn(TypedDict):
    status: str
    version: str
    session_active: bool


@app.get("/health")
def health_check() -> HealthCheckReturn:
    return {
        "status": "healthy",
        "version": "1.3.0",
        "session_active": session_controller.is_active(),
    }


# -----------------------------------------------------------------
# 4. Session Control REST Endpoints
# -----------------------------------------------------------------
class StartSessionOutput(TypedDict):
    message: str
    session_active: bool


class EndSessionOutput(TypedDict):
    message: str
    database_id: int
    score_result: ScoreResult


class HistoricalSessionOutput(TypedDict):
    id: int
    start_time: str
    end_time: str | None
    total_score: float
    pitch_accuracy: float
    timing_accuracy: float
    notes_hit: int
    notes_total: int


@app.post("/session/start")
def start_session() -> StartSessionOutput:
    """Starts the active practice session recording window."""
    if session_controller.is_active():
        logger.warning("Session start rejected: session already running.")
        raise HTTPException(
            status_code=400, detail="Session is already actively running."
        )

    session_controller.start_session()
    return {
        "message": "Practice session started successfully.",
        "session_active": session_controller.is_active(),
    }


@app.post("/session/end")
def end_session(db: Session = Depends(get_db)) -> EndSessionOutput:
    """Stops the recording session and calculates the final v1.2.0 score metrics."""
    if not session_controller.is_active():
        raise HTTPException(
            status_code=400, detail="No active session found to terminate."
        )

    try:
        # 1. Trigger the score engine calculation loop FIRST while the session is still active
        domain_session = session_controller.get_session()
        final_score = score_engine.compute()

        # 2. Build the parent database record row
        db_session_record = db_models.SessionRecord(
            end_time=datetime.now(timezone.utc),
            total_score=final_score["total_score"],
            pitch_accuracy=final_score["pitch_accuracy"],
            timing_accuracy=final_score["timing_accuracy"],
            notes_hit=final_score["notes_hit"],
            notes_total=final_score["notes_total"],
        )

        # 3. Add parent record to the transaction so it generates its auto-increment 'id'
        db.add(db_session_record)
        db.flush()  # Flushes state to assign id without fully finalizing the commit yet

        # 4. Extract all performed note sequences tracked in memory during this window
        performed_notes_list = domain_session.get_performed_notes()

        # 5. Convert domain events into child SQL table rows
        for note_event in performed_notes_list:
            db_note = db_models.PerformedNoteRecord(
                session_id=db_session_record.id,
                note=note_event["note"],
                start_time=note_event["start_time"],
                duration=note_event["duration"],
                avg_pitch_error_cents=note_event.get("avg_pitch_error_cents"),
            )
            db.add(db_note)

        # 6. Commit the entire transaction atomically to disk
        db.commit()

        session_id = cast(int, db_session_record.id)

        # 7. Wipe memory states in the live engine controller
        session_controller.end_session()

    except RuntimeError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Session state error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error("Failed to commit session analytics to database.", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Scoring calculation failed: {str(e)}"
        )

    return {
        "message": "Session finalized successfully.",
        "database_id": session_id,
        "score_result": final_score,
    }


# -----------------------------------------------------------------
# 5. Historical Query Endpoints
# -----------------------------------------------------------------


@app.get("/sessions", response_model=list[HistoricalSessionOutput])
def get_session_history(
    limit: int = 10, db: Session = Depends(get_db)
) -> list[
    HistoricalSessionOutput
]:  # Using Any inside the list to bypass strict SQLAlchemy object instance lint mapping
    """
    Retrieves a timeline of past violin practice sessions,
    ordered from newest to oldest.
    """
    try:
        # Query database records sorting by most recent
        records = (
            db.query(db_models.SessionRecord)
            .order_by(desc(db_models.SessionRecord.start_time))
            .limit(limit)
            .all()
        )

        # Format database models into our clean API schema output
        history_timeline = []
        for record in records:
            history_timeline.append(
                {
                    "id": cast(int, record.id),
                    "start_time": (
                        record.start_time.isoformat()
                        if cast(datetime, record.start_time)
                        else ""
                    ),
                    "end_time": (
                        record.end_time.isoformat()
                        if cast(datetime, record.end_time)
                        else None
                    ),
                    "total_score": cast(float, record.total_score),
                    "pitch_accuracy": cast(float, record.pitch_accuracy),
                    "timing_accuracy": cast(float, record.timing_accuracy),
                    "notes_hit": cast(int, record.notes_hit),
                    "notes_total": cast(int, record.notes_total),
                }
            )

        return history_timeline

    except Exception as e:
        logger.error("Failed to fetch session history timeline.", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Database retrieval failed: {str(e)}"
        )


# -----------------------------------------------------------------
# 6. Real-Time Telemetry WebSocket
# -----------------------------------------------------------------


@app.websocket("/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    Accepts incoming telemetry connections and streams real-time
    note and pitch error updates to the client.
    """
    await websocket.accept()
    logger.info("Client connected to live telemetry stream.")

    try:
        while True:
            # Check the broadcast queue for pipeline events without blocking the async loop.
            # Using asyncio.sleep allows other network connections to share resources smoothly.
            try:
                # Get the event from Thread C's queue output
                event = broadcast_queue.get_nowait()

                # Send it over the active WebSocket network channel
                await websocket.send_json(event)
                broadcast_queue.task_done()

            except queue.Empty:
                # If no data is ready, yield control back to the async engine for a brief moment
                await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("Client disconnected from live telemetry stream.")
