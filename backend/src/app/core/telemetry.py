import time
import json
import uuid
import numpy as np
from multiprocessing import Queue
from threading import Thread
from pathlib import Path

from app.models.telemetry_models import TelemetryMeta


class DistributedTelemetryHarness:
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.allocated_window_ms = (buffer_size / sample_rate) * 1000.0

        self.metrics_queue = Queue()
        self.is_running = False
        self.consumer_thread = None

        # Raw storage for async processing
        self.trace_history = []

        # Reusable timestamps list to minimize object allocation in the audio thread
        # 0: Frame Start, 1: Post-Ingestion, 2: Post-DSP, 3: Post-Alignment / End
        self._timestamps = [0.0] * 4

    def start_session(self):
        self.is_running = True
        self.trace_history = []
        self.consumer_thread = Thread(target=self._drain_queue, daemon=True)
        self.consumer_thread.start()

    def create_trace(self) -> TelemetryMeta:
        """Creates a new tracking context at the very start of ingestion."""
        return {
            "id": str(uuid.uuid4()),
            "t_start": time.perf_counter(),
            "t_ingest": 0.0,
            "t_pitch": 0.0,
            "t_segment": 0.0,
            "t_process": 0.0,
            "t_websocket": 0.0,
        }

    def complete_trace(self, trace: TelemetryMeta):
        """Called right before the websocket payload is pushed out."""
        t_end = time.perf_counter()

        t_start = trace.get("t_start", t_end)
        t_ingest = trace.get("t_ingest", t_start)
        t_pitch = trace.get("t_pitch", t_ingest)
        t_segment = trace.get("t_segment", t_pitch)

        if t_segment == 0.0:
            t_segment = t_pitch

        # If the controller dropped the frame early, t_process will be 0.0
        # Fall back to t_segment so ws_ms doesn't blow up into a massive number
        t_process = trace.get("t_process", 0.0)
        if t_process == 0.0:
            t_process = t_segment

        # Calculate clean intervals
        ingest_ms = (t_ingest - t_start) * 1000.0
        pitch_ms = (
            (t_pitch - t_ingest) * 1000.0 if trace.get("t_pitch", 0.0) != 0.0 else 0.0
        )
        segment_ms = (t_segment - t_pitch) * 1000.0

        # If t_process was skipped, process_ms and ws_ms naturally fall to 0.0
        process_ms = (
            (t_process - t_segment) * 1000.0
            if trace.get("t_process", 0.0) != 0.0
            else 0.0
        )
        ws_ms = (
            (t_end - t_process) * 1000.0 if trace.get("t_process", 0.0) != 0.0 else 0.0
        )
        total_ms = (t_end - t_start) * 1000.0

        try:
            self.metrics_queue.put_nowait(
                (ingest_ms, pitch_ms, segment_ms, process_ms, ws_ms, total_ms)
            )
        except Exception:
            pass

    def discard_trace(self):
        """Explicitly cancels a trace if data is out-of-bounds or an error occurs."""
        try:
            # Pass a "None" or a specific discard signal to tell the background
            # worker to increment a dropped counter or simply ignore it.
            self.metrics_queue.put_nowait(None)
        except Exception:
            pass

    def _drain_queue(self):
        while self.is_running:
            try:
                item = self.metrics_queue.get(timeout=1.0)

                if item is None:
                    continue  # Discard traces for out of bounds notes

                self.trace_history.append(item)
            except Exception:
                continue

    def stop_session(self, export_path: str = "docs/v1.9.0_pipeline_baseline.json"):
        self.is_running = False
        if self.consumer_thread:
            self.consumer_thread.join()

        while not self.metrics_queue.empty():
            self.trace_history.append(self.metrics_queue.get())

        if not self.trace_history:
            print("No telemetry data collected.")
            return

        # Convert history to a structured NumPy array for vector operations
        # Columns: 0=Ingest, 1=DSP, 2=Alignment, 3=WebsocketBroadcast, 4=Total
        metrics_data = np.array(self.trace_history, dtype=np.float64)

        masked_data = metrics_data.copy()
        masked_data[masked_data == 0.0] = np.nan

        excursions = int(np.sum(masked_data[:, 5] > self.allocated_window_ms))

        def safe_stat(column_idx: int, stat_type: str = "mean"):
            column = masked_data[:, column_idx]
            # Strip out NaN values for this specific column's calculations
            valid_data = column[~np.isnan(column)]

            if len(valid_data) == 0:
                return 0.0  # Return 0 if this stage was never executed once

            if stat_type == "mean":
                return round(float(np.mean(valid_data)), 3)
            elif stat_type == "std":
                return round(float(np.std(valid_data)), 3)
            elif stat_type == "p95":
                return round(float(np.percentile(valid_data, 95)), 3)
            elif stat_type == "p99":
                return round(float(np.percentile(valid_data, 99)), 3)

        report = {
            "telemetry_version": "1.8.2-pipeline",
            "environment": {
                "sample_rate_hz": self.sample_rate,
                "buffer_size_samples": self.buffer_size,
                "allocated_frame_window_ms": round(self.allocated_window_ms, 3),
            },
            "pipeline_analysis_ms": {
                "total_frames": len(metrics_data),
                "deadline_excursions": excursions,
                "stages": {
                    "1_audio_ingestion": {
                        "mean": safe_stat(0, "mean"),
                        "std": safe_stat(0, "std"),
                        "p95": safe_stat(0, "p95"),
                        "p99": safe_stat(0, "p99"),
                    },
                    "2_pitch_detection_dsp": {
                        "mean": safe_stat(1, "mean"),
                        "std": safe_stat(1, "std"),
                        "p95": safe_stat(1, "p95"),
                        "p99": safe_stat(1, "p99"),
                    },
                    "3_note_segmenter": {
                        "mean": safe_stat(2, "mean"),
                        "std": safe_stat(2, "std"),
                        "p95": safe_stat(2, "p95"),
                        "p99": safe_stat(2, "p99"),
                    },
                    "4_process_notes": {
                        "mean": safe_stat(3, "mean"),
                        "std": safe_stat(3, "std"),
                        "p95": safe_stat(3, "p95"),
                        "p99": safe_stat(3, "p99"),
                    },
                    "5_websocket_broadcast": {
                        "mean": safe_stat(4, "mean"),
                        "std": safe_stat(4, "std"),
                        "p95": safe_stat(4, "p95"),
                        "p99": safe_stat(4, "p99"),
                    },
                    "total_pipeline_lifecycle": {
                        "mean": round(float(np.mean(metrics_data[:, 5])), 3),
                        "std": round(float(np.std(metrics_data[:, 5])), 3),
                        "p95": round(float(np.percentile(metrics_data[:, 5], 95)), 3),
                        "p99": round(float(np.percentile(metrics_data[:, 5], 99)), 3),
                        "max": round(float(np.max(metrics_data[:, 5])), 3),
                    },
                },
            },
        }

        output_file = Path(export_path)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Full pipeline telemetry report exported to {export_path}")
