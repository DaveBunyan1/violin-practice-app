from sqlalchemy.orm import Session

from app.database.models import RepertoirePiece
from app.models.repertoire_models import NoteIn, PiecePatch
from app.services.repertoire_service import update_piece


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
