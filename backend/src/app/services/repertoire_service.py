from sqlalchemy.orm import Session
from app.database import models


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
