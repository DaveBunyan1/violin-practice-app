from dataclasses import dataclass
import queue
from typing import Optional, Tuple
from app.core.telemetry import DistributedTelemetryHarness
from app.models.events import (
    PerformedNoteEvent,
    PitchObservationEvent,
    WebSocketBroadcastEvent,
)
from app.models.telemetry_models import TelemetryMeta
from app.pipeline.note_segmenter import NoteSegmenter
from app.controllers.session_controller import SessionController
from app.pipeline.practice_target import PracticeTarget
from app.scoring.scoring_engine import ScoreEngine


@dataclass
class RuntimeGraph:
    def shutdown(
        self, export_target: str = "docs/v1.9.0_baseline_metrics.json"
    ) -> None:
        """
        Production-grade teardown sequence. Handles systematic flushing of
        in-memory buffers and state tracking engines at application exit.
        """
        print("\n🛑 Initiating performance telemetry teardown sequence...")

        try:
            # Command the telemetry engine to serialize safely
            self.telemetry.stop_session(export_path=export_target)
            print("✨ Performance benchmarking complete.")
        except Exception as e:
            # Production apps handle cleanup failures gracefully so they don't hang the OS
            print(f"❌ Critical error during telemetry shutdown: {e}")

    pitch_queue: queue.Queue[Tuple[PitchObservationEvent, Optional[TelemetryMeta]]]
    segmented_queue: queue.Queue[Tuple[PerformedNoteEvent, Optional[TelemetryMeta]]]
    broadcast_queue: queue.Queue[
        Tuple[WebSocketBroadcastEvent, Optional[TelemetryMeta]]
    ]

    target: PracticeTarget
    segmenter: NoteSegmenter
    session_controller: SessionController
    score_engine: ScoreEngine
    telemetry: DistributedTelemetryHarness
