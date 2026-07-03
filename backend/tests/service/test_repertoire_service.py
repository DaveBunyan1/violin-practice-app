from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import RepertoireNote, RepertoirePiece


def test_database_cascade_delete_integrity(client: TestClient, db_session: Session):
    """
    Data Integrity Test: Verifies that deleting a piece automatically cascades
    and purges all nested note rows from the database to prevent memory/orphaned row leaks.
    """
    # 1. Arrange: Seed a piece with an attached note
    test_piece = RepertoirePiece(title="Deletable Piece", bpm=60, total_duration=1.0)
    db_session.add(test_piece)
    db_session.commit()

    note_id = 9999
    nested_note = RepertoireNote(
        id=note_id, piece_id=test_piece.id, note="C4", time=0.0, duration=1.0
    )
    db_session.add(nested_note)
    db_session.commit()

    # 2. Act: Issue a DELETE request targeting this piece
    # (Adjust endpoint syntax if your delete route is structured differently)
    response = client.delete(f"/repertoire/{test_piece.id}")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    # 3. Assert: Query the database directly to verify the child note was completely wiped
    orphaned_note = (
        db_session.query(RepertoireNote).filter(RepertoireNote.id == note_id).first()
    )
    assert (
        orphaned_note is None
    ), "Data Leak: RepertoireNote was not purged when its parent piece was deleted!"


def test_negative_note_duration_returns_422(
    client: TestClient,
    db_session: Session,
):
    """
    Validation Test: Notes cannot have a negative duration.
    """

    piece = RepertoirePiece(
        title="Validation Test",
        bpm=120,
        time_signature_numerator=4,
        total_duration=0.0,
    )

    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    payload = {
        "notes": [
            {
                "note": "A4",
                "time": 0,
                "duration": -1,
            }
        ]
    }

    response = client.patch(f"/repertoire/{piece.id}", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_negative_note_time_returns_422(
    client: TestClient,
    db_session: Session,
):
    """
    Validation Test: Notes cannot begin before the piece starts.
    """

    piece = RepertoirePiece(
        title="Negative Time Test",
        bpm=120,
        time_signature_numerator=4,
        total_duration=0.0,
    )

    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    payload = {
        "notes": [
            {
                "note": "A4",
                "time": -0.5,
                "duration": 1,
            }
        ]
    }

    response = client.patch(f"/repertoire/{piece.id}", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_repertoire_empty_and_populated(client: TestClient, db_session: Session):
    # 🌟 Targets Line 18 (Happy Path)
    # 1. Test empty list format
    response = client.get("/repertoire")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # 2. Seed a piece to ensure it populates the return data array
    piece = RepertoirePiece(title="Gymnopédie No.1", bpm=65, time_signature_numerator=3)
    db_session.add(piece)
    db_session.commit()

    response = client.get("/repertoire")
    assert response.status_code == 200
    assert len(response.json()) >= 1
