import sounddevice as sd  # type: ignore

import numpy as np
from typing import cast, Tuple


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
