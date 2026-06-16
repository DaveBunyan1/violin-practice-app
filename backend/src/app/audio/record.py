import time
from typing import Any, Callable, Optional
import numpy as np
import sounddevice as sd  # type: ignore

from pitch.autocorrelation import estimate_frequency
from pitch.notes import freq_to_note
from core.events import NoteEvent

SAMPLE_RATE = 44100
BUFFER_SIZE = 8192  # number of samples per chunk
CHANNELS = 1
AMBIENT_NOISE_THRESHOLD = 0.0001  # Background ambient noise was all less than 1e-05, when playing volume > 0.0001

# Type-hint the callback target clearly
on_note_detected: Optional[Callable[[NoteEvent], None]] = None


def audio_callback(
    indata: np.ndarray,
    frames: int,
    status_time: Any,
    status: sd.CallbackFlags,
) -> None:

    if status:
        return

    audio_chunk = indata[:, 0].flatten().astype(np.float32)

    # Remove background noise from mic etc.
    volume = np.linalg.norm(audio_chunk) / len(audio_chunk)

    if volume < AMBIENT_NOISE_THRESHOLD:
        return

    freq = estimate_frequency(audio_chunk, SAMPLE_RATE)
    note = freq_to_note(freq)

    current_timestamp = time.time()

    global on_note_detected
    if on_note_detected:
        event: NoteEvent = {
            "frequency": freq,
            "note": note,
            "timestamp": current_timestamp,
        }
        on_note_detected(event)


def start_audio_stream() -> None:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BUFFER_SIZE,
        channels=CHANNELS,
        callback=audio_callback,
    ):
        print("Audio stream started...")

        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("Stopping audio stream...")
