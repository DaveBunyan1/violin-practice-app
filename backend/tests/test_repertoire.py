from fastapi.testclient import TestClient
from fastapi import status

from app.database.models import RepertoirePiece, RepertoireNote
from app.models.repertoire_models import PiecePatch, NoteIn
from app.services.repertoire_service import update_piece
from sqlalchemy.orm import Session


def test_metronome_duration_calibration(db_session: Session):
    """
    Unit Test: Verifies that 4 bars at 60 BPM evaluates to exactly 16.0 seconds.
    This asserts our timeline includes the duration of the final note correctly.
    """
    # 1. Arrange: Seed a fresh test piece into our isolated database transaction
    test_piece = RepertoirePiece(
        title="Stopwatch Calibration Test",
        bpm=60,
        time_signature_numerator=4,
        total_duration=0.0,
    )
    db_session.add(test_piece)
    db_session.commit()
    db_session.refresh(test_piece)

    # 2. Act: Simulate entering 4 bars of sequential notes (16 beats total)
    # At 60 BPM, 1 beat = 1.0 second.
    # Note 1 starts at 0.0s, Note 16 starts at 15.0s. Each lasts 1.0s.
    mock_notes = []
    for i in range(16):
        mock_notes.append(NoteIn(note="A4", time=float(i), duration=1.0))

    payload = PiecePatch(notes=mock_notes)
    updated_piece = update_piece(db_session, piece_id=test_piece.id, payload=payload)

    # 3. Assert: The math must equal exactly 16.0 seconds (Time + Duration of final note)
    assert updated_piece is not None
    assert updated_piece.total_duration == 16.0


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


def test_duration_calculation_with_irregular_note_lengths(db_session: Session):
    """
    Unit Test: Total duration should equal the end of the final sounding note,
    regardless of note lengths.
    """

    piece = RepertoirePiece(
        title="Irregular Duration Test",
        bpm=120,
        time_signature_numerator=4,
        total_duration=0.0,
    )

    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    payload = PiecePatch(
        notes=[
            NoteIn(note="A4", time=0.0, duration=0.5),
            NoteIn(note="B4", time=0.5, duration=2.0),
            NoteIn(note="C5", time=2.5, duration=0.25),
        ]
    )

    updated = update_piece(db_session, piece.id, payload)

    assert updated is not None
    assert updated.total_duration == 2.75


def test_duration_calculation_with_unsorted_notes(db_session: Session):
    """
    Unit Test: Duration should be calculated from the latest note end, not
    the final note in the supplied array.
    """

    piece = RepertoirePiece(
        title="Ordering Test",
        bpm=120,
        time_signature_numerator=4,
        total_duration=0.0,
    )

    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    payload = PiecePatch(
        notes=[
            NoteIn(note="A4", time=5.0, duration=0.5),
            NoteIn(note="B4", time=0.0, duration=1.0),
            NoteIn(note="C5", time=3.0, duration=2.0),
        ]
    )

    updated = update_piece(db_session, piece.id, payload)

    assert updated is not None
    assert updated.total_duration == 5.5


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


def test_total_duration_uses_last_note_end(db_session: Session):
    notes = [
        NoteIn(note="A4", time=0.0, duration=1.0),  # ends at 1.0
        NoteIn(note="B4", time=10.0, duration=0.5),  # ends at 10.5 (latest)
        NoteIn(note="C5", time=3.0, duration=2.0),  # ends at 5.0
    ]

    piece = RepertoirePiece(title="Test Piece")
    db_session.add(piece)
    db_session.commit()
    db_session.refresh(piece)

    patch = PiecePatch(notes=notes)

    updated_piece = update_piece(db_session, piece.id, patch)

    assert updated_piece is not None
    assert updated_piece.total_duration == 10.5
