from typing import List
from pydantic import BaseModel, ConfigDict, Field


class NoteIn(BaseModel):
    note: str = Field(..., min_length=2, max_length=3)
    time: float = Field(..., ge=0.0)
    duration: float = Field(..., gt=0.0)


class NoteOut(BaseModel):
    note: str
    time: float
    duration: float

    model_config = ConfigDict(from_attributes=True)


class PiecePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    bpm: int | None = Field(default=None, gt=0, le=300)
    time_signature_numerator: int | None = Field(default=None, ge=1, le=32)
    notes: list[NoteIn] | None = None


class PieceOut(BaseModel):
    id: int
    title: str
    bpm: int
    time_signature_numerator: int
    total_duration: float
    notes: List[NoteOut]

    model_config = ConfigDict(from_attributes=True)


class PieceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    bpm: int = Field(default=120, gt=0, le=300)
    time_signature_numerator: int = Field(default=4, ge=1, le=32)
