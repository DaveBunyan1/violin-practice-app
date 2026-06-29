from typing import Optional

from pydantic import BaseModel

from app.models.events import ScoreResult


class StartSessionPayload(BaseModel):
    piece_id: int
    start_bar: Optional[int] = None  # None means play from the beginning
    end_bar: Optional[int] = None  # None means play to the end


class StartSessionOutput(BaseModel):
    message: str
    session_active: bool


class EndSessionOutput(BaseModel):
    message: str
    database_id: int
    score_result: ScoreResult


class HistoricalSessionOutput(BaseModel):
    id: int
    start_time: str
    end_time: str | None
    total_score: float
    pitch_accuracy: float
    timing_accuracy: float
    notes_hit: int
    notes_total: int
