import pytest
from unittest.mock import MagicMock

from app.pipeline.process_notes import process_notes
from app.models.events import PerformedNoteEvent


class BreakLoopException(Exception):
    """Custom exception used to cleanly break out of the infinite while True loop."""

    pass


def test_process_notes_happy_path():
    # 1. Create mock dependencies
    mock_controller = MagicMock()
    mock_session = MagicMock()

    # Setup controller states
    mock_controller.get_session.return_value = mock_session
    mock_controller.is_active.return_value = True
    mock_session.start_time = 1000.0  # Reference baseline

    # Mock expected note lookup target return value
    mock_controller.target.get_expected_note.return_value = "A4"

    # 2. Prepare mock queues
    inbound_q = MagicMock()
    broadcast_q = MagicMock()

    # Create a realistic incoming note event
    mock_event: PerformedNoteEvent = {
        "note": "A4",
        "frequency": 440.0,
        "start_time": 1002.5,  # 2.5s relative start
        "end_time": 1003.0,  # 3.0s relative end
        "duration": 0.5,
        "avg_pitch_error_cents": 5.0,
    }

    # 🌟 THE TRICK: First call returns the event, second call crashes to break the loop
    inbound_q.get.side_effect = [mock_event, BreakLoopException()]

    # 3. Execute the pipeline block
    with pytest.raises(BreakLoopException):
        process_notes(
            controller=mock_controller,
            inbound_queue=inbound_q,
            websocket_broadcast_queue=broadcast_q,
        )

    # 4. Assertions: Verify everything inside the loop ran perfectly

    # Ensure time was normalized relative to session start (1002.5 - 1000.0)
    mock_session.add_performed_note.assert_called_once_with(
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 2.5,
            "end_time": 3.0,
            "duration": 0.5,
            "avg_pitch_error_cents": 5.0,
        }
    )

    # Verify the target lookup was fired with relative time
    mock_controller.target.get_expected_note.assert_called_once_with(2.5)

    # Verify WebSocket broadcast payload payload structure matches requirements
    broadcast_q.put.assert_called_once_with(
        {
            "type": "pitch",
            "data": {
                "frequency": 440.0,
                "note": "A4",
                "time": 2.5,
                "expected_note": "A4",
                "pitch_cents_error": 5.0,
            },
        }
    )

    # Ensure task_done is always called to clean up the queue item state
    inbound_q.task_done.assert_called_once()


def test_process_notes_skips_if_session_inactive():
    mock_controller = MagicMock()
    mock_controller.is_active.return_value = (
        False  # 🌟 Simulates an inactive session state
    )

    inbound_q = MagicMock()
    broadcast_q = MagicMock()

    mock_event = {
        "note": "A4",
        "frequency": 440.0,
        "start_time": 10.0,
        "end_time": 11.0,
        "duration": 1.0,
    }
    inbound_q.get.side_effect = [mock_event, BreakLoopException()]

    with pytest.raises(BreakLoopException):
        process_notes(mock_controller, inbound_q, broadcast_q)

    # Code should skip addition/broadcast, but cleanly finalize the task state
    mock_controller.target.get_expected_note.assert_not_called()
    broadcast_q.put.assert_not_called()
    inbound_q.task_done.assert_called_once()


def test_process_notes_handles_runtime_error_on_missing_session():
    # 1. Setup a mock controller that crashes when getting a session
    mock_controller = MagicMock()
    mock_controller.get_session.side_effect = RuntimeError(
        "No active session"
    )  # 🌟 Triggers lines 30-32

    inbound_q = MagicMock()
    broadcast_q = MagicMock()

    mock_event = {
        "note": "A4",
        "frequency": 440.0,
        "start_time": 10.0,
        "end_time": 11.0,
        "duration": 1.0,
    }

    # Pass the event, then break the loop
    inbound_q.get.side_effect = [mock_event, BreakLoopException()]

    # 2. Run the loop
    with pytest.raises(BreakLoopException):
        process_notes(
            controller=mock_controller,
            inbound_queue=inbound_q,
            websocket_broadcast_queue=broadcast_q,
        )

    # 3. Verify it skipped downstream processing but cleanly closed out the queue task
    broadcast_q.put.assert_not_called()
    inbound_q.task_done.assert_called_once()
