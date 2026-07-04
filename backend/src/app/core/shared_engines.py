import queue
from typing import Optional, Tuple

from app.models.events import (
    PerformedNoteEvent,
    PitchObservationEvent,
    WebSocketBroadcastEvent,
)
from app.models.telemetry_models import TelemetryMeta
from app.pipeline.practice_target import PracticeTarget
from app.controllers.session_controller import SessionController
from app.scoring.scoring_engine import ScoreEngine
from app.pipeline.note_segmenter import NoteSegmenter

pitch_queue: queue.Queue[Tuple[PitchObservationEvent, TelemetryMeta]] = queue.Queue()
segmented_queue: queue.Queue[Tuple[PerformedNoteEvent, Optional[TelemetryMeta]]] = (
    queue.Queue()
)
broadcast_queue: queue.Queue[
    Tuple[WebSocketBroadcastEvent, Optional[TelemetryMeta]]
] = queue.Queue()


target = PracticeTarget(mode="piece", active_piece=None)

segmenter = NoteSegmenter()

session_controller = SessionController(target, segmenter)
score_engine = ScoreEngine(session_controller)
