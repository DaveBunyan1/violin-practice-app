import queue
import threading
import time
from typing import Optional, Any, Callable
import numpy as np
import sounddevice as sd  # type: ignore

from app.pitch.autocorrelation import estimate_frequency
from app.pitch.notes import calculate_pitch_error, freq_to_note
from app.models.events import PitchObservationEvent
from app.core.logging import logger
from app.core.config import settings
from app.core.telemetry import generate_event_id


class AudioIngestionStream:
    """
    Manages the real-time microphone stream lifecycle and executes initial
    DSP pitch detection on a high-priority background audio thread.
    """

    def __init__(
        self,
        inbound_queue: queue.Queue[PitchObservationEvent],
        sample_rate: int = settings.SAMPLE_RATE,
        ambient_noise_threshold: float = settings.AMBIENT_NOISE_THRESHOLD,
        clock: Callable[[], float] = time.perf_counter,
    ):
        self.inbound_queue = inbound_queue
        self.sample_rate = sample_rate
        self.ambient_noise_threshold = ambient_noise_threshold
        self._stream: Optional[sd.InputStream] = None
        self.silence_debounce_time = 0.08  # 80ms
        self.clock = clock
        self._running: bool = False
        self._lock = threading.Lock()

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
        event_id = generate_event_id()
        created_at = self.clock()

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

        if note != "REST" and freq < 190.0 or freq > 3000.0:
            return

        # 5. Thread-safe dispatch out of the high-priority callback context
        event: PitchObservationEvent = {
            "frequency": freq,
            "note": note,
            "timestamp": current_timestamp,
            "pitch_cents_error": cents_error,
            "telemetry": {
                "event_id": event_id,
                "created_at": created_at,
            },
        }

        self.inbound_queue.put_nowait(event)

    def start(self) -> None:
        """Instantiates the background sounddevice context loop and maintains lifecycle."""
        with self._lock:
            if self._running:
                return  # Prevent spinning up duplicate streams concurrently
            self._running = True

            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    blocksize=settings.BUFFER_SIZE,
                    channels=settings.CHANNELS,
                    callback=self._audio_callback,
                )
                self._stream.start()
                logger.info(
                    "Audio stream context initialized and started successfully."
                )
            except Exception as e:
                logger.error(
                    f"Failed to start audio ingestion stream: {e}", exc_info=True
                )
                self._running = False
                self._stream = None
                raise

    def stop(self) -> None:
        """Tears down the hardware stream layer gracefully."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        if self._stream:
            try:
                if self._stream.active:
                    self._stream.stop()
            except (sd.PortAudioError, AttributeError) as e:
                logger.warning(f"Ignored expected stream shutdown exception: {e}")

            try:
                self._stream.close()
                logger.info("Audio ingestion stream torn down successfully.")
            except (sd.PortAudioError, AttributeError) as e:
                logger.warning(f"Ignored expected stream close exception: {e}")
            finally:
                self._stream = None
