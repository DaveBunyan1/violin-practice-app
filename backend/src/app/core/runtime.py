from dataclasses import dataclass
import queue

from app.core.event_bus import EventBus
from app.models.events import (
    PitchObservationEvent,
    PerformedNoteEvent,
)

from app.pipeline.note_segmenter import NoteSegmenter
from app.controllers.session_controller import SessionController
from app.scoring.scoring_engine import ScoreEngine


@dataclass
class RuntimeGraph:
    # queues
    pitch_queue: queue.Queue[PitchObservationEvent]
    segmented_queue: queue.Queue[PerformedNoteEvent]

    retry_queue: queue.Queue[PerformedNoteEvent]
    dead_letter_queue: queue.Queue[PerformedNoteEvent]

    event_bus: EventBus

    # core components
    segmenter: NoteSegmenter
    session_controller: SessionController
    score_engine: ScoreEngine
