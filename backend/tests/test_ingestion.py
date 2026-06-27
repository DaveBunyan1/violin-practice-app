import numpy as np
import queue
from unittest.mock import patch, MagicMock
from app.pipeline.ingestion import AudioIngestionStream
from tests.utils.audio_harness import AudioStreamTestHarness


class FakeStatus:
    inputBufferAdcTime = 1.0


def test_emits_rest_when_silent():
    """Verifies that an audio frame below the noise floor defaults to REST."""
    q = queue.Queue()
    stream = AudioIngestionStream(inbound_queue=q, ambient_noise_threshold=0.1)
    harness = AudioStreamTestHarness(stream)

    silence = np.zeros((1024, 1), dtype=np.float32)

    harness.feed(
        [
            (0.00, silence),
            (0.03, silence),
        ]
    )

    event = q.get_nowait()
    assert event["note"] == "REST"
    assert event["frequency"] == 0.0


@patch("app.audio.ingestion.freq_to_note")
@patch("app.audio.ingestion.estimate_frequency")
def test_emits_pitch_when_audio_present(
    mock_estimate: MagicMock, mock_freq_to_note: MagicMock
):
    """Verifies that a strong signal gets analyzed by the pitch extraction engine."""
    q = queue.Queue()
    stream = AudioIngestionStream(inbound_queue=q, ambient_noise_threshold=0.1)
    harness = AudioStreamTestHarness(stream)

    # Signal loud enough to break through the 0.1 noise threshold
    signal = np.ones((1024, 1), dtype=np.float32) * 0.5

    # We must patch these because the signal bypasses the noise gate!
    mock_estimate.return_value = 440.0
    mock_freq_to_note.return_value = "A4"

    harness.feed([(0.00, signal)])

    event = q.get_nowait()
    assert event["note"] == "A4"
    assert event["frequency"] == 440.0

    mock_estimate.assert_called_once()
    mock_freq_to_note.assert_called_once()


@patch("app.audio.ingestion.freq_to_note")
@patch("app.audio.ingestion.estimate_frequency")
def test_rms_threshold_blocks_signal(
    mock_estimate: MagicMock, mock_freq_to_note: MagicMock
):
    """Verifies that signals below high threshold boundaries are safely rejected."""
    q = queue.Queue()
    # Set an incredibly high threshold so even standard signals are rejected
    stream = AudioIngestionStream(inbound_queue=q, ambient_noise_threshold=1.0)
    harness = AudioStreamTestHarness(stream)

    quiet_signal = np.full((1024, 1), 0.01, dtype=np.float32)

    harness.feed(
        [
            (0.00, quiet_signal),
            (0.03, quiet_signal),
        ]
    )

    event = q.get_nowait()
    assert event["note"] == "REST"

    # We patch them to prove that they are NEVER executed when blocked by the gate
    mock_estimate.assert_not_called()
    mock_freq_to_note.assert_not_called()


def test_timestamp_is_passed_through():
    """Verifies that hardware clock boundaries align smoothly to output payloads."""
    q = queue.Queue()
    stream = AudioIngestionStream(inbound_queue=q)
    harness = AudioStreamTestHarness(stream)

    silence = np.zeros((1024, 1), dtype=np.float32)

    # We feed two frames at known time offsets relative to the harness baseline (1000.0)
    harness.feed(
        [
            (0.00, silence),
            (0.15, silence),
        ]
    )

    first_event = q.get_nowait()
    second_event = q.get_nowait()

    # Calculate the elapsed delta between the two frames
    actual_delta = second_event["timestamp"] - first_event["timestamp"]

    # Assert the delta matches our 0.15s interval within a tight margin of error
    # (Using pytest.approx accounts for microsecond processing delay between iterations)
    import pytest

    assert actual_delta == pytest.approx(0.15, abs=1e-2)
