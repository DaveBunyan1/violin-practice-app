from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.runtime import RuntimeGraph
from app.database.connection import get_db
from app.dependencies.runtime import get_runtime
from app.models.events import SessionStoredNote
from app.models.session_models import (
    EndSessionOutput,
    HistoricalSessionOutput,
    SessionDetailOutput,
    StartSessionOutput,
    StartSessionPayload,
)

from app.services.session_service import (
    create_session_history_record,
    get_historical_sessions,
    get_session_by_id,
)

from app.core.logging import logger
from app.core.telemetry import telemetry

router = APIRouter()


@router.post("/start", response_model=StartSessionOutput)
def start_session(
    payload: StartSessionPayload,
    db: Session = Depends(get_db),
    runtime: RuntimeGraph = Depends(get_runtime),
):
    """Starts the active practice session recording window."""
    if runtime.session_controller.is_active():
        logger.warning(
            "session_start_rejected_already_running",
            extra={"extra_context": {"attempted_piece_id": payload.piece_id}},
        )
        raise HTTPException(
            status_code=400, detail="Session is already actively running."
        )

    with telemetry.measure("api_start_session") as ctx:
        ctx["piece_id"] = payload.piece_id
        try:
            runtime.session_controller.start_session(
                db=db,
                piece_id=payload.piece_id,
                start_bar=payload.start_bar,
                end_bar=payload.end_bar,
                target_bpm=payload.target_bpm,
                countdownSeconds=payload.countdownSeconds,
            )
        except ValueError as e:
            logger.warning(
                "session_start_failed_invalid_piece",
                extra={
                    "extra_context": {"piece_id": payload.piece_id, "error": str(e)}
                },
            )
            raise HTTPException(status_code=404, detail=str(e))

        return StartSessionOutput(
            message="Practice session started successfully.",
            session_active=runtime.session_controller.is_active(),
        )


@router.post("/end")
def end_session(
    db: Session = Depends(get_db), runtime: RuntimeGraph = Depends(get_runtime)
) -> EndSessionOutput:
    """Stops the recording session and calculates final session score metrics."""
    if not runtime.session_controller.is_active():
        logger.warning("session_end_rejected_no_active_session")
        raise HTTPException(
            status_code=400, detail="No active session found to terminate."
        )

    with telemetry.measure("api_end_session") as ctx:
        try:
            domain_session = runtime.session_controller.get_session()
            ctx["piece_id"] = domain_session.piece_id

            # 1. Trigger the score engine calculation loop while state is isolated
            final_score = runtime.score_engine.compute()
            performed_notes_list = domain_session.get_performed_notes()

            # 2. Delegate database record creation completely to the service layer
            db_session_record = create_session_history_record(
                db=db,
                piece_id=domain_session.piece_id,
                final_score=final_score,
                performed_notes_list=performed_notes_list,
            )

            # 3. Commit the transaction atomically at the router boundary
            db.commit()
            session_id = db_session_record.id

            # 4. Clear memory states in the live controller after disk write completes
            runtime.session_controller.end_session()

        except RuntimeError as e:
            db.rollback()
            logger.error(
                "session_end_state_error", extra={"extra_context": {"error": str(e)}}
            )
            raise HTTPException(
                status_code=400, detail=f"Session state error: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            logger.error("session_analytics_commit_failed", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Scoring calculation failed: {str(e)}"
            )

        return EndSessionOutput(
            message="Session finalized successfully.",
            database_id=session_id,
            score_result=final_score,
        )


@router.get("/sessions", response_model=list[HistoricalSessionOutput])
def get_session_history(limit: int = 10, db: Session = Depends(get_db)):
    """Retrieves a timeline of past violin practice sessions, ordered from newest to oldest."""
    with telemetry.measure("api_get_session_history") as ctx:
        ctx["query_limit"] = limit
        try:
            records = get_historical_sessions(db, limit=limit)

            return [
                HistoricalSessionOutput(
                    id=record.id,
                    start_time=(
                        record.start_time.isoformat() if record.start_time else ""
                    ),
                    end_time=record.end_time.isoformat() if record.end_time else None,
                    total_score=record.total_score,
                    pitch_accuracy=record.pitch_accuracy,
                    timing_accuracy=record.timing_accuracy,
                    notes_hit=record.notes_hit,
                    notes_total=record.notes_total,
                )
                for record in records
            ]
        except Exception as e:
            logger.error("session_history_retrieval_failed", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Database retrieval failed: {str(e)}"
            )


@router.get("/sessions/{session_id}", response_model=SessionDetailOutput)
def get_session(session_id: int, db: Session = Depends(get_db)):
    with telemetry.measure("api_get_session_detail") as ctx:
        ctx["session_id"] = session_id
        try:
            record = get_session_by_id(db, session_id)
            if not record:
                raise HTTPException(status_code=404, detail="Session not found")

            return SessionDetailOutput(
                id=record.id,
                start_time=record.start_time.isoformat(),
                end_time=record.end_time.isoformat() if record.end_time else None,
                piece_id=record.piece_id,
                total_score=record.total_score,
                pitch_accuracy=record.pitch_accuracy,
                timing_accuracy=record.timing_accuracy,
                notes_hit=record.notes_hit,
                notes_total=record.notes_total,
                performed_notes=[
                    SessionStoredNote(
                        note=n.note,
                        avg_pitch_error_cents=n.avg_pitch_error_cents,
                        start_time=n.start_time,
                        duration=n.duration,
                    )
                    for n in record.performed_notes
                ],
            )
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error("session_detail_failed", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    with telemetry.measure("api_delete_session") as ctx:
        ctx["session_id"] = session_id

        session = get_session_by_id(db, session_id)
        if not session:
            # Track malicious or broken frontend deletion links
            logger.warning(
                "session_deletion_failed_not_found",
                extra={"extra_context": {"session_id": session_id}},
            )
            raise HTTPException(status_code=404, detail="Session not found")

        db.delete(session)
        db.commit()
        return Response(status_code=204)
