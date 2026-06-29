from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timezone, datetime

from app.database import models
from app.database.connection import get_db
from app.models.session_models import (
    EndSessionOutput,
    HistoricalSessionOutput,
    StartSessionOutput,
    StartSessionPayload,
)
from app.core.logging import logger
from app.core.shared_engines import session_controller, score_engine
from app.services.session_service import (
    create_session_history_record,
    get_historical_sessions,
)

router = APIRouter()


@router.post("/start", response_model=StartSessionOutput)
def start_session(payload: StartSessionPayload, db: Session = Depends(get_db)):
    """Starts the active practice session recording window."""
    if session_controller.is_active():
        logger.warning("Session start rejected: session already running.")
        raise HTTPException(
            status_code=400, detail="Session is already actively running."
        )

    try:
        session_controller.start_session(
            db=db,
            piece_id=payload.piece_id,
            start_bar=payload.start_bar,
            end_bar=payload.end_bar,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StartSessionOutput(
        message="Practice session started successfully.",
        session_active=session_controller.is_active(),
    )


@router.post("/end")
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

        # 2. Extract all performed note sequences tracked in memory during this window
        performed_notes_list = domain_session.get_performed_notes()

        # 2. Build the parent database record row
        db_session_record = models.SessionRecord(
            end_time=datetime.now(timezone.utc),
            total_score=final_score["total_score"],
            pitch_accuracy=final_score["pitch_accuracy"],
            timing_accuracy=final_score["timing_accuracy"],
            notes_hit=final_score["notes_hit"],
            notes_total=final_score["notes_total"],
        )

        # 3. Delegate data staging completely to your service layer
        db_session_record = create_session_history_record(
            db=db, final_score=final_score, performed_notes_list=performed_notes_list
        )

        # 4. Commit the entire transaction atomically here at the transaction boundary line
        db.commit()

        session_id = db_session_record.id

        # 5. Wipe memory states in the live engine controller safely after data is on disk
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
        records = get_historical_sessions(db, limit=limit)

        # Format database models into our clean API schema output
        history_timeline = []
        for record in records:
            history_timeline.append(
                {
                    "id": record.id,
                    "start_time": (
                        record.start_time.isoformat() if record.start_time else ""
                    ),
                    "end_time": (
                        record.end_time.isoformat() if record.end_time else None
                    ),
                    "total_score": record.total_score,
                    "pitch_accuracy": record.pitch_accuracy,
                    "timing_accuracy": record.timing_accuracy,
                    "notes_hit": record.notes_hit,
                    "notes_total": record.notes_total,
                }
            )

        return history_timeline

    except Exception as e:
        logger.error("Failed to fetch session history timeline.", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Database retrieval failed: {str(e)}"
        )
