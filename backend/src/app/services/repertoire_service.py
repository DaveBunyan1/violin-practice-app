from sqlalchemy.orm import Session
from app.database import models
from app.models.repertoire_models import PiecePatch


def get_all_repertoire(db: Session):
    return db.query(models.RepertoirePiece).all()


def get_active_practice_piece(db: Session, title: str) -> models.RepertoirePiece | None:
    """Queries the repository for a specific piece blueprint by its title."""
    return (
        db.query(models.RepertoirePiece)
        .filter(models.RepertoirePiece.title == title)
        .first()
    )


def get_piece_by_id(db: Session, piece_id: int) -> models.RepertoirePiece | None:
    """Queries the repository for a specific piece blueprint by its unique ID."""
    return (
        db.query(models.RepertoirePiece)
        .filter(models.RepertoirePiece.id == piece_id)
        .first()
    )


def create_piece(db: Session, title: str, bpm: int, time_signature_numerator: int):
    piece = models.RepertoirePiece(
        title=title,
        bpm=bpm,
        time_signature_numerator=time_signature_numerator,
        total_duration=0.0,  # placeholder until notes exist
    )

    db.add(piece)
    db.commit()
    db.refresh(piece)
    return piece


def update_piece(db: Session, piece_id: int, payload: PiecePatch):
    piece = db.query(models.RepertoirePiece).filter_by(id=piece_id).first()

    if not piece:
        return None

    # update scalar fields
    if payload.title is not None:
        piece.title = payload.title

    if payload.bpm is not None:
        piece.bpm = payload.bpm

    if payload.time_signature_numerator is not None:
        piece.time_signature_numerator = payload.time_signature_numerator

    # replace notes (simple v1 strategy)
    if payload.notes is not None:
        # delete old notes
        db.query(models.RepertoireNote).filter(
            models.RepertoireNote.piece_id == piece_id
        ).delete()

        # insert new notes
        piece.notes = [
            models.RepertoireNote(note=n.note, time=n.time, duration=n.duration)
            for n in payload.notes
        ]

        # recompute duration
        if payload.notes:
            piece.total_duration = max(n.time + n.duration for n in payload.notes)

    db.commit()
    db.refresh(piece)

    return piece
