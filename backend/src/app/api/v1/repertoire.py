from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.repertoire_service import (
    create_piece,
    get_active_practice_piece,
    get_all_repertoire,
    update_piece,
)
from app.database.connection import get_db
from app.models.repertoire_models import PieceCreate, PieceOut, PiecePatch

router = APIRouter()


@router.get("", response_model=list[PieceOut])
def get_repertoire(db: Session = Depends(get_db)):
    return get_all_repertoire(db)


@router.post("", response_model=PieceOut)
def add_piece(payload: PieceCreate, db: Session = Depends(get_db)):
    piece = create_piece(
        db,
        title=payload.title,
        bpm=payload.bpm,
        time_signature_numerator=payload.time_signature_numerator,
    )
    return piece


@router.get("/active", response_model=PieceOut)
def get_active_piece(db: Session = Depends(get_db)):
    """
    Fetches the targeted practicing piece from the database,
    populating its historical note array timeline.
    """
    # For now, we query the piece we seeded by its title
    piece = get_active_practice_piece(db, "Gym")

    if not piece:
        raise HTTPException(
            status_code=404,
            detail="Active practice piece template missing from storage.",
        )

    return piece


@router.patch("/{piece_id}", response_model=PieceOut)
def patch_piece(piece_id: int, payload: PiecePatch, db: Session = Depends(get_db)):
    piece = update_piece(db, piece_id, payload)

    if not piece:
        raise HTTPException(status_code=404, detail="Piece not found")

    return piece
