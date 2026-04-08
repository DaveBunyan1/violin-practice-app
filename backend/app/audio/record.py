import sounddevice as sd  # type: ignore

import numpy as np
from typing import cast, Tuple, Any, Optional
import queue

from pitch.autocorrelation import estimate_frequency
from pitch.notes import freq_to_note


SAMPLE_RATE = 44100
BUFFER_SIZE = 2048  # number of samples per chunk
CHANNELS = 1
AMBIENT_NOISE_THRESHOLD = 0.0001  # Background ambient noise was all less than 1e-05, when playing volume > 0.0001

last_note: Optional[str] = None
note_queue: queue.Queue[Tuple[float, str]] = queue.Queue()


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
    indata: np.ndarray,
    frames: int,
    time: Any,
    status: sd.CallbackFlags,
) -> None:
    global last_note
    if status:
        print(status)

    audio_chunk = indata[:, 0].flatten().astype(np.float32)

    # Remove background noise from mic etc.
    volume = np.linalg.norm(audio_chunk) / len(audio_chunk)
    print(f"Volume: {volume}")

    if volume < AMBIENT_NOISE_THRESHOLD:
        return

    freq = estimate_frequency(audio_chunk, SAMPLE_RATE)
    note = freq_to_note(freq)

    if note != last_note:
        note_queue.put((freq, note))
        last_note = note
