import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.pipeline.ingestion import AudioIngestionStream
from tests.utils.audio_harness import AudioStreamTestHarness


def test_emits_rest_when_silent(
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that an audio frame below the noise floor defaults to REST."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 0.1
    silence = np.zeros((1024, 1), dtype=np.float32)
    harness.feed([(0.00, silence), (0.03, silence)])

    event = stream.inbound_queue.get_nowait()
    assert event["note"] == "REST"
    assert event["frequency"] == 0.0


@patch("app.pipeline.ingestion.freq_to_note")
@patch("app.pipeline.ingestion.estimate_frequency")
def test_emits_pitch_when_audio_present(
    mock_estimate: MagicMock,
    mock_freq_to_note: MagicMock,
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that a strong signal gets analyzed by the pitch extraction engine."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 0.1
    signal = np.ones((1024, 1), dtype=np.float32) * 0.5
    mock_estimate.return_value = 440.0
    mock_freq_to_note.return_value = "A4"

    harness.feed([(0.00, signal)])
    event = stream.inbound_queue.get_nowait()
    assert event["note"] == "A4"
    assert event["frequency"] == 440.0


@patch("app.pipeline.ingestion.freq_to_note")
@patch("app.pipeline.ingestion.estimate_frequency")
def test_rms_threshold_blocks_signal(
    mock_estimate: MagicMock,
    mock_freq_to_note: MagicMock,
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that signals below high threshold boundaries are safely rejected."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 1.0
    quiet_signal = np.full((1024, 1), 0.01, dtype=np.float32)

    harness.feed([(0.00, quiet_signal), (0.03, quiet_signal)])
    event = stream.inbound_queue.get_nowait()
    assert event["note"] == "REST"
    mock_estimate.assert_not_called()
    mock_freq_to_note.assert_not_called()


def test_timestamp_is_passed_through(
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that hardware clock boundaries align smoothly to output payloads."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 0.1
    silence = np.zeros((1024, 1), dtype=np.float32)

    harness.feed([(0.00, silence), (0.15, silence)])
    first_event = stream.inbound_queue.get_nowait()
    second_event = stream.inbound_queue.get_nowait()

    actual_delta = second_event["timestamp"] - first_event["timestamp"]
    assert actual_delta == pytest.approx(0.15, abs=1e-2)


@patch("app.pipeline.ingestion.freq_to_note")
@patch("app.pipeline.ingestion.estimate_frequency")
def test_out_of_bounds_violin_frequencies_are_ignored(
    mock_estimate: MagicMock,
    mock_freq_to_note: MagicMock,
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that frequencies outside the violin range (190Hz-3000Hz) are rejected."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 0.1
    signal = np.ones((1024, 1), dtype=np.float32) * 0.5

    mock_estimate.return_value = 100.0
    mock_freq_to_note.return_value = "G2"
    harness.feed([(0.00, signal)])

    mock_estimate.return_value = 3500.0
    mock_freq_to_note.return_value = "A7"
    harness.feed([(0.05, signal)])

    assert stream.inbound_queue.empty()


def test_callback_returns_early_on_status(
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that the audio callback drops the buffer immediately if hardware status errors occur."""
    _, stream = audio_harness
    with patch("app.pipeline.ingestion.estimate_frequency") as mock_est:
        status = MagicMock()
        status.__bool__.return_value = True
        stream._audio_callback(np.ones((1024, 1), dtype=np.float32), 1024, None, status)  # type: ignore
        mock_est.assert_not_called()


def test_no_event_emitted_for_invalid_state(
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that no output payload is queued when a pitch calculation hits an out-of-bounds error state."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 0.1
    with patch("app.pipeline.ingestion.estimate_frequency", return_value=99999.0):
        loud_signal = np.ones((1024, 1), dtype=np.float32) * 0.5
        harness.feed([(0.0, loud_signal)])
    assert stream.inbound_queue.empty()


def test_rms_calculation_blocks_low_energy_signal(
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies that signals with mathematical RMS volume below the gate floor default straight to REST."""
    harness, stream = audio_harness
    signal = np.full((1024, 1), 0.05, dtype=np.float32)
    stream.ambient_noise_threshold = 0.06
    harness.feed([(0.0, signal)])
    event = stream.inbound_queue.get_nowait()
    assert event["note"] == "REST"


def test_real_pitch_pipeline_integration(
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """Verifies end-to-end processing of a raw mathematical sine wave through the unmocked pitch engine."""
    harness, stream = audio_harness
    stream.ambient_noise_threshold = 0.0
    signal = (
        np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 1024))
        .astype(np.float32)
        .reshape(-1, 1)
    )
    harness.feed([(0.0, signal)])
    event = stream.inbound_queue.get_nowait()
    assert event["note"] is not None
    assert event["frequency"] > 0
