from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.repertoire_service import (
    get_active_practice_piece,
    get_all_repertoire,
)
from app.database.connection import get_db
from app.models.repertoire_models import PieceOut

router = APIRouter()


@router.get("", response_model=list[PieceOut])
def get_repertoire(db: Session = Depends(get_db)):
    return get_all_repertoire(db)


@router.get("/active", response_model=PieceOut)
def get_active_piece(db: Session = Depends(get_db)):
    """
    Fetches the targeted practicing piece from the database,
    populating its historical note array timeline.
    """
    # For now, we query the piece we seeded by its title
    piece = get_active_practice_piece(db, "Open Strings Horizon")

    if not piece:
        raise HTTPException(
            status_code=404,
            detail="Active practice piece template missing from storage.",
        )

    return piece
