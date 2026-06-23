import queue
import time
from typing import Optional, Any, Callable
import numpy as np
import sounddevice as sd  # type: ignore

from app.pitch.autocorrelation import estimate_frequency
from app.pitch.notes import calculate_pitch_error, freq_to_note
from app.core.events import PitchObservationEvent

# Domain-specific default configuration parameters
SAMPLE_RATE = 44100
BUFFER_SIZE = 8192  # Samples per chunk
CHANNELS = 1
AMBIENT_NOISE_THRESHOLD = 0.0001


class AudioIngestionStream:
    """
    Manages the real-time microphone stream lifecycle and executes initial
    DSP pitch detection on a high-priority background audio thread.
    """

    def __init__(
        self,
        inbound_queue: queue.Queue[PitchObservationEvent],
        sample_rate: int = SAMPLE_RATE,
        ambient_noise_threshold: float = AMBIENT_NOISE_THRESHOLD,
        clock: Callable[[], float] = time.perf_counter,
    ):
        self.inbound_queue = inbound_queue
        self.sample_rate = sample_rate
        self.ambient_noise_threshold = ambient_noise_threshold
        self._stream: Optional[sd.InputStream] = None
        self._silence_start: float | None = None
        self._is_silent: bool = False
        self.silence_debounce_time = 0.08  # 80ms (good starting point)
        self.clock = clock

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,  # unused but required by API
        status_time: Any,  # unused (we use perf_counter instead)
        status: sd.CallbackFlags,
    ) -> None:
        """Real-time audio buffer processing loop executed by the sounddevice engine."""
        _ = frames
        _ = status_time
        if status:
            return

        # 1. Extract mono channel view without allocating duplicate memory
        audio_chunk = indata[:, 0].astype(np.float32)

        # 2. Vectorized RMS calculation for amplitude gating
        rms_volume = np.sqrt(np.mean(audio_chunk**2))

        # 3. Set timestamp
        current_timestamp = self.clock()

        # 4. Pure instantaneous evaluation (No internal state or accumulation)
        if rms_volume < self.ambient_noise_threshold:
            freq = 0.0
            note = "REST"
            cents_error = None
        else:
            freq = float(estimate_frequency(audio_chunk, self.sample_rate))
            note = freq_to_note(freq)
            cents_error = calculate_pitch_error(freq)

        # 5. Thread-safe dispatch out of the high-priority callback context
        event: PitchObservationEvent = {
            "frequency": freq,
            "note": note,
            "timestamp": current_timestamp,
            "pitch_cents_error": cents_error,
        }
        self.inbound_queue.put(event)

    def start(self) -> None:
        """Instantiates the background sounddevice context loop and maintains lifecycle."""
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=BUFFER_SIZE,
            channels=CHANNELS,
            callback=self._audio_callback,
        )

        with self._stream:
            print("Audio stream context initialized successfully...")
            while self._stream.active:
                sd.sleep(100)
