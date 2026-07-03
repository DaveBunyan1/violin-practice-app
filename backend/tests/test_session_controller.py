import pytest
from unittest.mock import MagicMock, patch
from app.controllers.session_controller import SessionController


@pytest.fixture
def mock_dependencies():
    target = MagicMock()
    segmenter = MagicMock()
    db_session = MagicMock()

    # 1. Create a mock piece with real note items to satisfy line 113->110
    note_inside = MagicMock()
    note_inside.time = 2.0
    note_inside.duration = 1.0
    note_inside.note = "A4"

    note_outside = MagicMock()
    note_outside.time = 500.0  # Way outside our bar offsets
    note_outside.duration = 1.0
    note_outside.note = "E5"

    mock_piece = MagicMock()
    mock_piece.title = "Violin Partita"
    mock_piece.bpm = 120
    mock_piece.time_signature_numerator = 4
    mock_piece.total_duration = 60.0
    mock_piece.notes = [note_inside, note_outside]

    return target, segmenter, db_session, mock_piece


def test_end_session_no_active_session_error(mock_dependencies: MagicMock):
    """Hits lines 126-127 by ending a session that hasn't started yet."""
    target, segmenter, _, _ = mock_dependencies
    controller = SessionController(target, segmenter)

    with pytest.raises(RuntimeError, match="No session to end"):
        controller.end_session()


def test_reset_session_execution_lifecycle(mock_dependencies: MagicMock):
    """Hits lines 146-150 by executing the reset controller wrapper function."""
    target, segmenter, db, mock_piece = mock_dependencies
    controller = SessionController(target, segmenter)

    with patch(
        "app.controllers.session_controller.get_piece_by_id", return_value=mock_piece
    ):
        # Trigger the reset method directly
        controller.reset_session(db, piece_id=1, start_bar=1, end_bar=4)

        # Verify that it successfully ran through reset and re-activated the session state
        assert controller.is_active() is True
        assert controller.get_session().piece_id == 1


def test_session_controller_happy_path_and_loops(mock_dependencies: MagicMock):
    """Hits line 113->110 (loop filtering) and line 172 (elapsed calculation)."""
    target, segmenter, db, mock_piece = mock_dependencies
    controller = SessionController(target, segmenter)

    with patch(
        "app.controllers.session_controller.get_piece_by_id", return_value=mock_piece
    ):
        # Starts successfully and processes notes inside/outside bounds
        controller.start_session(db, piece_id=1, start_bar=1, end_bar=4)
        assert controller.is_active() is True

        # Verify get_session works on an active session
        session = controller.get_session()
        assert session.piece_id == 1

        # Hits line 172 (Verifies calculation path when session is actively running)
        elapsed = controller.get_elapsed_time()
        assert isinstance(elapsed, float)


def test_get_session_not_started_error(mock_dependencies: MagicMock):
    """Hits lines 157-159 by asserting the RuntimeError on an inactive session."""
    target, segmenter, _, _ = mock_dependencies
    controller = SessionController(target, segmenter)

    with pytest.raises(RuntimeError, match="Session not started"):
        controller.get_session()


def test_start_session_piece_not_found(mock_dependencies: MagicMock):
    """Verifies the fallback exception when get_piece_by_id returns None."""
    target, segmenter, db, _ = mock_dependencies
    controller = SessionController(target, segmenter)

    with patch("app.controllers.session_controller.get_piece_by_id", return_value=None):
        with pytest.raises(ValueError, match="Repertoire piece with ID 999 not found."):
            controller.start_session(db, piece_id=999)


def test_get_elapsed_time_no_session(mock_dependencies: MagicMock):
    """Hits lines 165-171 by checking elapsed time when no session is initialized."""
    target, segmenter, _, _ = mock_dependencies
    controller = SessionController(target, segmenter)
    assert controller.get_elapsed_time() == 0.0
