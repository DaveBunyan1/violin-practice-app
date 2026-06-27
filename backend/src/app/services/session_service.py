from datetime import datetime, timezone
from typing import List
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.database import models
from app.models.events import PerformedNoteEvent, ScoreResult


def create_session_history_record(
    db: Session,
    final_score: ScoreResult,
    performed_notes_list: List[PerformedNoteEvent],
) -> models.SessionRecord:
    """
    Atomically writes a completed practice run summary and all individual
    performed note tracking segments into database storage.
    """
    # 1. Instantiate parent record
    db_session_record = models.SessionRecord(
        end_time=datetime.now(timezone.utc),
        total_score=final_score["total_score"],
        pitch_accuracy=final_score["pitch_accuracy"],
        timing_accuracy=final_score["timing_accuracy"],
        notes_hit=final_score["notes_hit"],
        notes_total=final_score["notes_total"],
    )

    db.add(db_session_record)
    db.flush()  # Populates db_session_record.id without finishing the transaction

    # 2. Map domain tracking events to child table rows
    for note_event in performed_notes_list:
        db_note = models.PerformedNoteRecord(
            session_id=db_session_record.id,
            note=note_event["note"],
            start_time=note_event["start_time"],
            duration=note_event["duration"],
            avg_pitch_error_cents=note_event.get("avg_pitch_error_cents"),
        )
        db.add(db_note)

    return db_session_record


def get_historical_sessions(db: Session, limit: int = 10) -> list[models.SessionRecord]:
    """Retrieves a timeline of past violin practice sessions, ordered from newest to oldest."""
    return (
        db.query(models.SessionRecord)
        .order_by(desc(models.SessionRecord.start_time))
        .limit(limit)
        .all()
    )
