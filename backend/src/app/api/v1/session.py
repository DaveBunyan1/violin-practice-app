from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from datetime import timezone, datetime

from app.database import models
from app.database.connection import get_db
from app.models.session_models import (
    EndSessionOutput,
    HistoricalSessionOutput,
    StartSessionOutput,
)
from app.core.logging import logger
from app.core.shared_engines import session_controller, score_engine

router = APIRouter()


@router.post("/session/start")
def start_session() -> StartSessionOutput:
    """Starts the active practice session recording window."""
    if session_controller.is_active():
        logger.warning("Session start rejected: session already running.")
        raise HTTPException(
            status_code=400, detail="Session is already actively running."
        )

    session_controller.start_session()
    return StartSessionOutput(
        message="Practice session started successfully.",
        session_active=session_controller.is_active(),
    )


@router.post("/session/end")
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
        db_session_record = models.SessionRecord(
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
            db_note = models.PerformedNoteRecord(
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

    return EndSessionOutput(
        message="Session finalized successfully.",
        database_id=session_id,
        score_result=final_score,
    )


# -----------------------------------------------------------------
# Historical Query Endpoints
# -----------------------------------------------------------------


@router.get("/sessions", response_model=list[HistoricalSessionOutput])
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
            db.query(models.SessionRecord)
            .order_by(desc(models.SessionRecord.start_time))
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
