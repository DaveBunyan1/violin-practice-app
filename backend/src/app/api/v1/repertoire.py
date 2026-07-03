from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.repertoire_models import PieceCreate, PieceOut, PiecePatch
from app.services.repertoire_service import (
    create_piece,
    get_all_repertoire,
    update_piece,
    get_piece_by_id,
)

from app.core.logging import logger
from app.core.telemetry import telemetry

router = APIRouter()


@router.get("", response_model=list[PieceOut])
def get_repertoire(db: Session = Depends(get_db)):
    """Fetches all items present in the repertoire storage layer."""
    with telemetry.measure("api_get_all_repertoire"):
        return get_all_repertoire(db)


@router.post("", response_model=PieceOut)
def add_piece(payload: PieceCreate, db: Session = Depends(get_db)):
    """Creates and inserts a fresh repertoire template tracking reference."""
    with telemetry.measure("api_add_repertoire_piece"):
        return create_piece(
            db,
            title=payload.title,
            bpm=payload.bpm,
            time_signature_numerator=payload.time_signature_numerator,
        )


@router.patch("/{piece_id}", response_model=PieceOut)
def patch_piece(piece_id: int, payload: PiecePatch, db: Session = Depends(get_db)):
    with telemetry.measure("api_patch_repertoire_piece") as ctx:
        ctx["piece_id"] = piece_id
        piece = update_piece(db, piece_id, payload)

        if not piece:
            # 🌟 Add a clear, structural warning log for debugging 404s
            logger.warning(
                "piece_patch_failed_not_found",
                extra={"extra_context": {"piece_id": piece_id}},
            )
            raise HTTPException(status_code=404, detail="Piece not found")

        return piece


@router.delete("/{piece_id}", status_code=204)
def delete_repertoire_piece(piece_id: int, db: Session = Depends(get_db)):
    with telemetry.measure("api_delete_repertoire_piece") as ctx:
        ctx["piece_id"] = piece_id

        piece = get_piece_by_id(db, piece_id)
        if not piece:
            # Track malicious or broken frontend deletion links
            logger.warning(
                "piece_deletion_failed_not_found",
                extra={"extra_context": {"piece_id": piece_id}},
            )
            raise HTTPException(status_code=404, detail="Piece not found")

        db.delete(piece)
        db.commit()
        return Response(status_code=204)
