from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import models
from app.database.connection import get_db
from app.models.repertoire_models import PieceOut

router = APIRouter()


@router.get("/repertoire/active", response_model=PieceOut)
def get_active_piece(db: Session = Depends(get_db)):
    """
    Fetches the targeted practicing piece from the database,
    populating its historical note array timeline.
    """
    # For now, we query the piece we seeded by its title
    piece = (
        db.query(models.RepertoirePiece)
        .filter(models.RepertoirePiece.title == "Open Strings Horizon")
        .first()
    )

    if not piece:
        raise HTTPException(
            status_code=404,
            detail="Active practice piece template missing from storage.",
        )

    return piece
