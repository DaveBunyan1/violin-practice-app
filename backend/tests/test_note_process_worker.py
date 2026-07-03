from unittest.mock import MagicMock

from app.pipeline.note_processing_worker import NoteProcessingWorker
from app.models.events import PerformedNoteEvent


def test_process_single_event_happy_path():
    # ----------------------------
    # Arrange
    # ----------------------------
    controller = MagicMock()
    session = MagicMock()
    broadcast_q = MagicMock()
    broadcast_q.put = MagicMock()

    controller.is_active.return_value = True
    controller.get_session.return_value = session
    controller.target.get_expected_note.return_value = "A4"

    session.start_time = 1000.0

    worker = NoteProcessingWorker(
        controller=controller,
        inbound_queue=MagicMock(),
        websocket_broadcast_queue=MagicMock(),
        retry_queue=MagicMock(),
        dead_letter_queue=MagicMock(),
    )

    worker.websocket_broadcast_queue = broadcast_q
    event: PerformedNoteEvent = {
        "note": "A4",
        "frequency": 440.0,
        "start_time": 1002.5,
        "end_time": 1003.0,
        "duration": 0.5,
        "avg_pitch_error_cents": 5.0,
        "retry_count": 0,
    }

    # ----------------------------
    # Act
    # ----------------------------
    result = worker._process_single_event(event)  # type: ignore

    # ----------------------------
    # Assert
    # ----------------------------
    assert result.name == "OK"

    session.add_performed_note.assert_called_once_with(
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 2.5,
            "end_time": 3.0,
            "duration": 0.5,
            "avg_pitch_error_cents": 5.0,
        }
    )

    controller.target.get_expected_note.assert_called_once_with(2.5)

    worker.websocket_broadcast_queue.put.assert_called_once()


def test_inactive_session_drops_event():
    controller = MagicMock()
    controller.is_active.return_value = False

    worker = NoteProcessingWorker(
        controller=controller,
        inbound_queue=MagicMock(),
        websocket_broadcast_queue=MagicMock(),
        retry_queue=MagicMock(),
        dead_letter_queue=MagicMock(),
    )

    event = {
        "note": "A4",
        "frequency": 440.0,
        "start_time": 0.0,
        "end_time": 1.0,
        "duration": 1.0,
    }

    result = worker._process_single_event(event)  # type: ignore

    assert result.name == "DROP"


def test_session_error_returns_retry():
    controller = MagicMock()
    controller.get_session.side_effect = RuntimeError("boom")

    worker = NoteProcessingWorker(
        controller=controller,
        inbound_queue=MagicMock(),
        websocket_broadcast_queue=MagicMock(),
        retry_queue=MagicMock(),
        dead_letter_queue=MagicMock(),
    )

    event = {
        "note": "A4",
        "frequency": 440.0,
        "start_time": 0.0,
        "end_time": 1.0,
        "duration": 1.0,
    }

    result = worker._process_single_event(event)  # type: ignore

    assert result.name == "RETRY"
