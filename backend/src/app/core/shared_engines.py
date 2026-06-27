import queue

from app.models.events import (
    PerformedNoteEvent,
    PitchObservationEvent,
    WebSocketBroadcastEvent,
)
from app.pipeline.practice_target import PracticeTarget
from app.controllers.session_controller import SessionController
from app.scoring.scoring_engine import ScoreEngine
from app.pipeline.note_segmenter import NoteSegmenter

pitch_queue: queue.Queue[PitchObservationEvent] = queue.Queue()
segmented_queue: queue.Queue[PerformedNoteEvent] = queue.Queue()
broadcast_queue: queue.Queue[WebSocketBroadcastEvent] = queue.Queue()

target = PracticeTarget(mode="piece", active_piece=None)

segmenter = NoteSegmenter()

session_controller = SessionController(target, segmenter)
score_engine = ScoreEngine(session_controller)
