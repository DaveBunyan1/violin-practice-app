from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base


class SessionRecord(Base):
    """
    SQLAlchemy model representing a finalized violin practice session.
    """

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time = Column(DateTime, nullable=True)

    # Final v1.2.0 scoring metrics aggregated on completion
    total_score = Column(Float, nullable=False, default=0.0)
    pitch_accuracy = Column(Float, nullable=False, default=0.0)
    timing_accuracy = Column(Float, nullable=False, default=0.0)
    notes_hit = Column(Integer, nullable=False, default=0)
    notes_total = Column(Integer, nullable=False, default=0)

    # Relationship to child notes.
    # 'cascade="all, delete-orphan"' ensures if a session is deleted, its notes are cleaned up too.
    performed_notes = relationship(
        "PerformedNoteRecord", back_populates="session", cascade="all, delete-orphan"
    )


class PerformedNoteRecord(Base):
    """
    SQLAlchemy model representing an individual note segment processed
    and committed during a practice session.
    """

    __tablename__ = "performed_notes"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking back to the parent 'sessions' table
    session_id = Column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Core note performance properties from your domain events
    note = Column(String, nullable=False)  # e.g., "A4"
    start_time = Column(
        Float, nullable=False
    )  # Offset timestamp relative to session start
    duration = Column(Float, nullable=False)

    # v1.2.0 precision data layer addition
    avg_pitch_error_cents = Column(Float, nullable=True)

    # Bidirectional relationship link back up to the parent record
    session = relationship("SessionRecord", back_populates="performed_notes")
