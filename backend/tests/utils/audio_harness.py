import numpy as np
from typing import List, Tuple
import sounddevice as sd  # type: ignore

from app.audio.ingestion import AudioIngestionStream

AudioFrame = Tuple[float, np.ndarray]  # (timestamp_offset, audio_chunk)


class FakeStatus:
    def __init__(self, t: float):
        self.inputBufferAdcTime = t


class AudioStreamTestHarness:
    """
    Simulates a real-time audio stream by feeding timestamped frames
    into the AudioIngestionStream callback.
    """

    def __init__(self, stream: AudioIngestionStream):
        self.stream = stream
        self.start_time = 1000.0

        # override clock
        self.stream.clock = lambda: self.t

    def feed(self, frames: List[AudioFrame]) -> None:
        """
        frames: list of (time_offset_seconds, audio_chunk)
        """
        clean_status_flags = sd.CallbackFlags()

        for dt, audio in frames:
            self.t = 1000.0 + dt
            self.stream._audio_callback(
                indata=audio,
                frames=1024,
                status_time=None,
                status=clean_status_flags,
            )
