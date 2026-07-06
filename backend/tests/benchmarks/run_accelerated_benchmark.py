import queue
import time
from typing import Optional
import numpy as np
import scipy.io.wavfile as wavfile
import threading


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Import your actual runtime components
from app.controllers.session_controller import SessionController
from app.core.pipeline import run_segmentation_pipeline
from app.core.runtime import RuntimeGraph
from app.core.telemetry import DistributedTelemetryHarness
from app.database.connection import Base
from app.database.models import RepertoireNote, RepertoirePiece
from app.models.events import PerformedNoteEvent, PitchObservationEvent
from app.models.telemetry_models import TelemetryMeta
from app.pipeline.note_segmenter import NoteSegmenter
from app.pipeline.practice_target import PracticeTarget
from app.pipeline.note_processing_worker import NoteProcessingWorker

from app.pitch.autocorrelation import estimate_frequency
from app.pitch.notes import calculate_pitch_error, freq_to_note
from app.scoring.scoring_engine import ScoreEngine
from app.core.config import settings


def load_and_normalize_wav(
    wav_path: str, target_sr: int = settings.SAMPLE_RATE
) -> np.ndarray:
    """Loads a WAV file, converts it to mono float32 normalized, and verifies sample rate."""
    sr, data = wavfile.read(wav_path)
    if sr != target_sr:
        raise ValueError(
            f"WAV file sample rate ({sr}Hz) must match pipeline expectations ({target_sr}Hz)"
        )

    # Normalize to float32 between -1.0 and 1.0 if it's integer based
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0

    # If stereo, grab the first channel
    if len(data.shape) > 1:
        data = data[:, 0]

    return data


def execute_accelerated_run(
    audio_data: np.ndarray, sample_rate: int, max_frames: int
) -> float:
    """Instantiates a clean runtime graph and pumps frames through at maximum CPU speed."""
    # 1. Initialize production runtime components
    engine = create_engine(
        settings.DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionBenchmark = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionBenchmark()

    try:
        piece = RepertoirePiece(
            title="Open Strings Horizon",
            total_duration=5.0,
            bpm=80,
            time_signature_numerator=4,
        )

        db.add(piece)
        db.flush()

        notes = [
            RepertoireNote(piece_id=piece.id, note="G3", time=0.0, duration=9000.0),
            RepertoireNote(piece_id=piece.id, note="D4", time=9000.0, duration=18000.0),
            RepertoireNote(
                piece_id=piece.id, note="A4", time=18000.0, duration=27000.0
            ),
            RepertoireNote(
                piece_id=piece.id, note="E5", time=27000.0, duration=36000.0
            ),
        ]
        db.add_all(notes)
    finally:
        pass

    telemetry = DistributedTelemetryHarness()
    telemetry.start_session()

    pitch_queue = queue.Queue()
    segmented_queue = queue.Queue()
    broadcast_queue = queue.Queue()
    retry_queue = queue.Queue()
    dead_letter_queue = queue.Queue()

    target = PracticeTarget(mode="piece", active_piece=None)
    segmenter = NoteSegmenter(telemetry=telemetry)

    session_controller = SessionController(target, segmenter)
    score_engine = ScoreEngine(session_controller)

    runtime = RuntimeGraph(
        pitch_queue=pitch_queue,
        segmented_queue=segmented_queue,
        broadcast_queue=broadcast_queue,
        retry_queue=retry_queue,
        dead_letter_queue=dead_letter_queue,
        target=target,
        segmenter=segmenter,
        session_controller=session_controller,
        score_engine=score_engine,
        telemetry=telemetry,
    )

    runtime.session_controller.start_session(db=db, piece_id=1, countdownSeconds=0.0)

    def on_segmented(note: PerformedNoteEvent, trace: Optional[TelemetryMeta]):
        runtime.segmented_queue.put((note, trace))

    runtime.segmenter.set_callback(on_segmented)

    threading.Thread(
        target=run_segmentation_pipeline,
        args=(runtime.pitch_queue, runtime.segmenter),
        daemon=True,
    ).start()

    worker = NoteProcessingWorker(
        controller=runtime.session_controller,
        inbound_queue=runtime.segmented_queue,
        broadcast_queue=runtime.broadcast_queue,
        retry_queue=runtime.retry_queue,
        dead_letter_queue=runtime.dead_letter_queue,
        telemetry=runtime.telemetry,
    )

    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()

    print("Initialized threads. Beginning acceleration loop...")
    wall_start = time.perf_counter()

    synthetic_time = 0.0
    frames_sent = 0
    chunk_duration = settings.BUFFER_SIZE / sample_rate  # ~0.04644 seconds

    total_chunks = len(audio_data) // settings.BUFFER_SIZE
    if max_frames:
        total_chunks = min(total_chunks, max_frames)

    audio_indices = list(range(0, len(audio_data), settings.BUFFER_SIZE))[:total_chunks]

    for i in tqdm(audio_indices, desc="Processing Audio Frames", unit="frame"):
        if runtime.telemetry:
            trace = runtime.telemetry.create_trace()
        else:
            trace = None

        # Stop early if a maximum capture frame constraint was explicitly passed
        if max_frames and frames_sent >= max_frames:
            break

        audio_chunk = audio_data[i : i + settings.BUFFER_SIZE]
        if len(audio_chunk) < settings.BUFFER_SIZE:
            break

        if trace:
            trace["t_ingest"] = time.perf_counter()

        # Bypass the physical microphone callback loop and push straight to the queue!
        rms_volume = np.sqrt(np.mean(audio_chunk**2))
        current_timestamp = synthetic_time

        if rms_volume < settings.AMBIENT_NOISE_THRESHOLD:
            freq = 0.0
            note = "REST"
            cents_error = None
        else:
            freq = float(estimate_frequency(audio_chunk, settings.SAMPLE_RATE))
            note = freq_to_note(freq)
            cents_error = calculate_pitch_error(freq)

        if note != "REST" and (freq < 190.0 or freq > 3000.0):
            if trace and runtime.telemetry:
                runtime.telemetry.discard_trace()
            synthetic_time += chunk_duration
            continue

        event: PitchObservationEvent = {
            "frequency": freq,
            "note": note,
            "timestamp": current_timestamp,
            "pitch_cents_error": cents_error,
        }

        if trace:
            trace["t_pitch"] = time.perf_counter()

        runtime.pitch_queue.put((event, trace))

        # Advance virtual clock and iteration counter
        synthetic_time += chunk_duration
        frames_sent += 1

    print(
        f"📥 Dispatched {frames_sent} frames. Waiting for queues to drain completely..."
    )

    # Block until all concurrent mathematical processing has cleared out
    runtime.pitch_queue.join()
    runtime.segmented_queue.join()

    print("🛑 Signaling background worker to stop...")
    worker.stop()

    worker_thread.join(timeout=5.0)

    elapsed_wall_time = time.perf_counter() - wall_start
    print(f"✨ Emulation completed in {elapsed_wall_time:.2f} seconds.")

    # Save the file name dynamically based on total processed frames
    filename = f"docs/{settings.VERSION}/{settings.VERSION}_{frames_sent}_frames_{settings.BUFFER_SIZE}_buffer_size.json"
    runtime.telemetry.stop_session(filename)
    print(f"💾 Exchanged data saved to {filename}")

    return elapsed_wall_time


if __name__ == "__main__":
    PATH_TO_WAV = "tests/benchmarks/continuous_practice_recording.wav"

    print("📋 Loading audio data into memory...")
    base_raw_audio = load_and_normalize_wav(PATH_TO_WAV)

    FRAME_TARGETS = [50000, 100000, 1000000]

    for target_frames in FRAME_TARGETS:
        # 1. Reset to the original audio baseline for each loop iteration
        raw_audio = base_raw_audio

        # 2. Calculate exactly how many samples this specific frame count demands
        required_samples = target_frames * settings.BUFFER_SIZE

        # 3. Dynamically scale the audio array up to match the requirement
        if len(raw_audio) < required_samples:
            print(
                f"\n🔄 Lengthening audio file to hit {target_frames} frames ({required_samples} samples)..."
            )
            repeats_needed = int(np.ceil(required_samples / len(raw_audio)))
            raw_audio = np.tile(raw_audio, repeats_needed)

        # 4. Truncate array back down to exactly required_samples
        # (This avoids extra ceiling padding from np.ceil inflating the array size)
        raw_audio = raw_audio[:required_samples]

        # 5. Run the target execution
        print(f"\n--- 🚀 Starting Test: {target_frames:,} Frames ---")
        execute_accelerated_run(
            raw_audio, sample_rate=settings.SAMPLE_RATE, max_frames=target_frames
        )
