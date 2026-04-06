import sounddevice as sd  # type: ignore
from scipy.io.wavfile import write
import numpy as np
from typing import cast


def record_violin(file_name: str, duration: int = 5, sample_rate: int = 44100):
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

    write(file_name, sample_rate, audio_data)
    print(f"Recording saved to {file_name}")
