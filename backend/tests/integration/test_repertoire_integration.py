from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import RepertoireNote, RepertoirePiece


def test_patch_repertoire_endpoint(client: TestClient, db_session: Session):
    """
    Integration Test: Verifies the FastAPI HTTP patch router, validation layers,
    and database relationship cascade loops work smoothly together.
    """
    # 1. Arrange: Seed a piece directly into the database context
    test_piece = RepertoirePiece(
        title="API Integration Test",
        bpm=120,  # 120 BPM means 1 beat = 0.5 seconds
        time_signature_numerator=4,
        total_duration=0.0,
    )
    db_session.add(test_piece)
    db_session.commit()
    db_session.refresh(test_piece)

    # 2. Act: Hit the virtual live endpoint using our overrode TestClient fixture
    # We send a single quarter note at beat 0 (0.0s) lasting 1 beat (0.5s)
    payload = {"notes": [{"note": "E5", "time": 0.0, "duration": 0.5}]}

    response = client.patch(f"/repertoire/{test_piece.id}", json=payload)

    # 3. Assert: Verify the network layer responds with standard REST compliance
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "API Integration Test"
    assert data["total_duration"] == 0.5
    assert len(data["notes"]) == 1
    assert data["notes"][0]["note"] == "E5"


def test_bpm_lower_boundary_guardrail(client: TestClient, db_session: Session):
    """
    Validation Test: Enforces that zero or negative BPM configurations are
    blocked by the validation layer before causing division-by-zero math errors.
    """
    # 1. Arrange: Seed a piece
    test_piece = RepertoirePiece(title="Guardrail Test", bpm=120, total_duration=0.0)
    db_session.add(test_piece)
    db_session.commit()

    # 2. Act: Attempt to set the BPM to an invalid zero/negative value
    payload = {"bpm": 0}
    response = client.patch(f"/repertoire/{test_piece.id}", json=payload)

    # 3. Assert: FastAPI must reject this request automatically
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_empty_sequence_resets_duration(client: TestClient, db_session: Session):
    """
    Edge Case Test: Sending an empty array of notes should clear existing notes
    and smoothly reset total_duration back to 0.0 without throwing maximum range loop crashes.
    """
    # 1. Arrange: Seed a piece that already contains an active note record
    test_piece = RepertoirePiece(title="Clearing Test", bpm=60, total_duration=1.0)
    db_session.add(test_piece)
    db_session.commit()

    existing_note = RepertoireNote(
        piece_id=test_piece.id, note="A4", time=0.0, duration=1.0
    )
    db_session.add(existing_note)
    db_session.commit()

    # 2. Act: Send an empty list patch to clear out everything
    payload = {"notes": []}
    response = client.patch(f"/repertoire/{test_piece.id}", json=payload)

    # 3. Assert: The endpoint succeeds and duration correctly resets to zero
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_duration"] == 0.0
    assert len(data["notes"]) == 0


def test_patch_missing_piece_returns_404(client: TestClient):
    """
    Integration Test: Updating a non-existent piece should return HTTP 404.
    """
    payload = {"bpm": 80}

    response = client.patch("/repertoire/999999", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_missing_piece_returns_404(client: TestClient):
    """
    Integration Test: Deleting a non-existent piece should return HTTP 404.
    """
    response = client.delete("/repertoire/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_patch_updates_only_requested_fields(
    client: TestClient,
    db_session: Session,
):
    """
    Integration Test: PATCH should only modify supplied fields and preserve
    all others.
    """
    piece = RepertoirePiece(
        title="Original Title",
        bpm=120,
        time_signature_numerator=4,
        total_duration=0.0,
    )

    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    response = client.patch(
        f"/repertoire/{piece.id}",
        json={"bpm": 80},
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["title"] == "Original Title"
    assert data["bpm"] == 80
    assert data["time_signature_numerator"] == 4


def test_patch_replaces_existing_notes(
    client: TestClient,
    db_session: Session,
):
    """
    Integration Test: Uploading a new note list should completely replace
    the previous sequence.
    """

    piece = RepertoirePiece(
        title="Replacement Test",
        bpm=60,
        time_signature_numerator=4,
        total_duration=3.0,
    )

    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    db_session.add_all(
        [
            RepertoireNote(piece_id=piece.id, note="A4", time=0, duration=1),
            RepertoireNote(piece_id=piece.id, note="B4", time=1, duration=1),
            RepertoireNote(piece_id=piece.id, note="C5", time=2, duration=1),
        ]
    )

    db_session.commit()

    payload = {
        "notes": [
            {
                "note": "G4",
                "time": 0,
                "duration": 1,
            }
        ]
    }

    response = client.patch(f"/repertoire/{piece.id}", json=payload)

    assert response.status_code == status.HTTP_200_OK

    notes = (
        db_session.query(RepertoireNote)
        .filter(RepertoireNote.piece_id == piece.id)
        .all()
    )

    assert len(notes) == 1
    assert notes[0].note == "G4"


def test_create_piece_uses_default_values(client: TestClient):
    """
    Integration Test: Creating a piece with only a title should populate
    all default values.
    """

    response = client.post(
        "/repertoire",
        json={
            "title": "Default Piece",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["title"] == "Default Piece"
    assert data["bpm"] == 120
    assert data["time_signature_numerator"] == 4
    assert data["total_duration"] == 0.0
    assert data["notes"] == []
