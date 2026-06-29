from typing import List, Optional

from pydantic import BaseModel


class NoteIn(BaseModel):
    note: str
    time: float
    duration: float


class NoteOut(BaseModel):
    note: str
    time: float
    duration: float

    class Config:
        from_attributes = True


class PiecePatch(BaseModel):
    title: Optional[str] = None
    bpm: Optional[int] = None
    time_signature_numerator: Optional[int] = None
    notes: Optional[List[NoteIn]] = None


class PieceOut(BaseModel):
    id: int
    title: str
    total_duration: float
    notes: List[NoteOut]

    class Config:
        from_attributes = True


class PieceCreate(BaseModel):
    title: str
    bpm: int = 120
    time_signature_numerator: int = 4
