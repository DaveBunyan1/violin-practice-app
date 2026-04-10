import sounddevice as sd  # type: ignore
import numpy as np
from typing import Any


from pitch.autocorrelation import estimate_frequency
from pitch.notes import freq_to_note


SAMPLE_RATE = 44100
BUFFER_SIZE = 8192  # number of samples per chunk
CHANNELS = 1
AMBIENT_NOISE_THRESHOLD = 0.0001  # Background ambient noise was all less than 1e-05, when playing volume > 0.0001

on_note_detected = None


def audio_callback(
    indata: np.ndarray,
    frames: int,
    time: Any,
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

    global on_note_detected
    if on_note_detected:
        on_note_detected(freq, note)


def start_audio_stream() -> None:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BUFFER_SIZE,
        channels=CHANNELS,
        callback=audio_callback,
    ):
        print("Audio stream started...")
        while True:
            pass  # keep stream alive
