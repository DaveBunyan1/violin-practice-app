from app.pipeline.practice_target import PracticeTarget, PracticePiece, ExpectedNote


def test_tuner_mode_returns_static_note():
    # Covers the "tuner" mode branch inside get_expected_note
    target = PracticeTarget(mode="tuner", expected_note="A4")
    assert target.get_expected_note(current_time=5.2) == "A4"


def test_piece_mode_empty_or_missing_piece_returns_none():
    # Covers missing active_piece or empty notes list guard clause
    target_no_piece = PracticeTarget(mode="piece", active_piece=None)
    assert target_no_piece.get_expected_note(current_time=1.0) is None

    empty_piece = PracticePiece(title="Empty", total_duration=30.0, notes=[])
    target_empty_notes = PracticeTarget(mode="piece", active_piece=empty_piece)
    assert target_empty_notes.get_expected_note(current_time=1.0) is None


def test_piece_mode_note_timeline_navigation():
    # Construct a chronological sequence of target notes
    notes = [
        ExpectedNote(note="D4", time=1.0, duration=1.0),  # Valid: 1.0s to 2.0s
        ExpectedNote(note="A4", time=3.0, duration=2.0),  # Valid: 3.0s to 5.0s
    ]
    piece = PracticePiece(title="Scale", total_duration=10.0, notes=notes)
    target = PracticeTarget(mode="piece", active_piece=piece)

    # 1. Test hitting a valid note window exactly
    assert target.get_expected_note(current_time=1.5) == "D4"
    assert target.get_expected_note(current_time=4.0) == "A4"

    # 2. Test falling inside a rest/silence period (returns None)
    assert target.get_expected_note(current_time=2.5) == None

    # 3. Test early break optimization (time is before the first note)
    # This directly triggers the `elif note.time > current_time: break` path
    assert target.get_expected_note(current_time=0.5) is None

    # 4. Test passing a time past the very last note (forces loop finish -> Line 49)
    assert target.get_expected_note(current_time=6.0) is None


def test_get_expected_sequence():
    notes = [ExpectedNote(note="E5", time=0.0, duration=1.0)]
    piece = PracticePiece(title="Solo", total_duration=5.0, notes=notes)

    # Piece mode should return the actual notes array (Line 53)
    target_piece = PracticeTarget(mode="piece", active_piece=piece)
    assert target_piece.get_expected_sequence() == notes

    # Tuner mode should fall through and return an empty list (Line 54)
    target_tuner = PracticeTarget(mode="tuner", expected_note="E5")
    assert target_tuner.get_expected_sequence() == []
