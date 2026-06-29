from typing import List, Optional

from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.database.connection import Base


class SessionRecord(Base):
    """
    SQLAlchemy model representing a finalized violin practice session.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Final v1.2.0 scoring metrics aggregated on completion
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    pitch_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    timing_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    notes_hit: Mapped[int] = mapped_column(Integer, default=0)
    notes_total: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship to child notes.
    performed_notes: Mapped[List["PerformedNoteRecord"]] = relationship(
        "PerformedNoteRecord", back_populates="session", cascade="all, delete-orphan"
    )


class PerformedNoteRecord(Base):
    """
    SQLAlchemy model representing an individual note segment processed
    and committed during a practice session.
    """

    __tablename__ = "performed_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key linking back to the parent 'sessions' table
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Core note performance properties from your domain events
    note: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "A4"
    start_time: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Offset timestamp relative to session start
    duration: Mapped[float] = mapped_column(Float, nullable=False)

    # v1.2.0 precision data layer addition
    avg_pitch_error_cents: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Bidirectional relationship link back up to the parent record
    session: Mapped["SessionRecord"] = relationship(
        "SessionRecord", back_populates="performed_notes"
    )


class RepertoirePiece(Base):
    __tablename__ = "repertoire_pieces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    total_duration: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Total length of the piece in seconds
    image_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # One-to-Many relationship pointing to the note timeline sequence
    notes: Mapped[List["RepertoireNote"]] = relationship(
        "RepertoireNote",
        back_populates="piece",
        cascade="all, delete-orphan",
        order_by="RepertoireNote.time",  # Automatically keeps notes sorted chronologically
    )

    bpm: Mapped[int] = mapped_column(Integer, default=120)
    time_signature_numerator: Mapped[int] = mapped_column(Integer, default=4)


class RepertoireNote(Base):
    __tablename__ = "repertoire_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    piece_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repertoire_pieces.id", ondelete="CASCADE"), nullable=False
    )

    note: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "G3", "D4", "A4"
    time: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Absolute start offset time in seconds
    duration: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Total note window duration in seconds

    # Inverse relationship link back to parent metadata
    piece: Mapped["RepertoirePiece"] = relationship(
        "RepertoirePiece", back_populates="notes"
    )
