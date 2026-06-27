from typing import List

from pydantic import BaseModel


class NoteOut(BaseModel):
    note: str
    time: float
    duration: float

    class Config:
        from_attributes = True


class PieceOut(BaseModel):
    id: int
    title: str
    total_duration: float
    notes: List[NoteOut]

    class Config:
        from_attributes = True
