import time
import json
import uuid
import numpy as np
from multiprocessing import Queue
from threading import Thread

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
            "t_segment": 0.0,
            "t_process": 0.0,
            "t_websocket": 0.0,
        }

    def complete_trace(self, trace: TelemetryMeta):
        """Called right before the websocket payload is pushed out."""
        t_end = time.perf_counter()

        # Calculate individual intervals relative to the initial start time
        # This keeps math accurate even if stages happen instantly
        ingest_ms = (trace["t_ingest"] - trace["t_start"]) * 1000.0
        segment_ms = (trace["t_segment"] - trace["t_ingest"]) * 1000.0
        process_ms = (trace["t_process"] - trace["t_segment"]) * 1000.0
        ws_ms = (t_end - trace["t_process"]) * 1000.0
        total_ms = (t_end - trace["t_start"]) * 1000.0

        try:
            self.metrics_queue.put_nowait(
                (trace["id"], ingest_ms, segment_ms, process_ms, ws_ms, total_ms)
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

    def stop_session(self, export_path: str = "docs/v1.8.2_pipeline_baseline.json"):
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
        data = np.array(self.trace_history)

        excursions = int(np.sum(data[:, 3] > self.allocated_window_ms))

        report = {
            "telemetry_version": "1.8.2-pipeline",
            "environment": {
                "sample_rate_hz": self.sample_rate,
                "buffer_size_samples": self.buffer_size,
                "allocated_frame_window_ms": round(self.allocated_window_ms, 3),
            },
            "pipeline_analysis_ms": {
                "total_frames": len(data),
                "deadline_excursions": excursions,
                "stages": {
                    "1_audio_ingestion": {
                        "mean": round(float(np.mean(data[:, 0])), 3),
                        "p95": round(float(np.percentile(data[:, 0], 95)), 3),
                    },
                    "2_pitch_detection_dsp": {
                        "mean": round(float(np.mean(data[:, 1])), 3),
                        "p95": round(float(np.percentile(data[:, 1], 95)), 3),
                    },
                    "3_greedy_alignment": {
                        "mean": round(float(np.mean(data[:, 2])), 3),
                        "p95": round(float(np.percentile(data[:, 2], 95)), 3),
                    },
                    "4_websocket_broadcast": {
                        "mean": round(float(np.mean(data[:, 3])), 3),
                        "p95": round(float(np.percentile(data[:, 3], 95)), 3),
                    },
                    "total_pipeline_lifecycle": {
                        "mean": round(float(np.mean(data[:, 4])), 3),
                        "p95": round(float(np.percentile(data[:, 3], 95)), 3),
                        "max": round(float(np.max(data[:, 4])), 3),
                    },
                },
            },
        }

        with open(export_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Full pipeline telemetry report exported to {export_path}")
