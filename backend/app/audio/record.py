import sounddevice as sd  # type: ignore

import numpy as np
from typing import cast, Tuple

from pitch.autocorrelation import estimate_frequency
from pitch.notes import freq_to_note


SAMPLE_RATE = 44100
AMBIENT_NOISE_THRESHOLD = 0.0001  # Background ambient noise was all less than 1e-05, when playing volume > 0.0001


def record_violin(
    duration: int = 5, sample_rate: int = 44100
) -> Tuple[np.ndarray, int]:
    print(f"Recording for {duration} seconds...")
    audio_data: np.ndarray = cast(
        np.ndarray,
        sd.rec(  # type: ignore
            int(sample_rate * duration),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        ),
    )
    sd.wait()

    audio_data = audio_data.flatten()

    print("Recording complete.")
    return audio_data, sample_rate


def audio_callback(
    indata: np.ndarray, frames: int, time: sd.CallbackFlags, status: sd.CallbackFlags
) -> None:
    if status:
        print(status)

    audio_chunk = indata[:, 0].flatten().astype(np.float32)

    # Remove background noise from mic etc.
    volume = np.linalg.norm(audio_chunk) / len(audio_chunk)

    if volume < AMBIENT_NOISE_THRESHOLD:
        return

    freq = estimate_frequency(audio_chunk, SAMPLE_RATE)
    note = freq_to_note(freq)
    print(f"{freq:.2f} Hz → {note}")
