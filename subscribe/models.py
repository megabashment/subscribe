from __future__ import annotations

from pydantic import BaseModel


class Word(BaseModel):
    text: str
    start: float
    end: float
    confidence: float = 1.0


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[Word] = []
    is_event: bool = False  # True for non-speech sound events like [Lachen]


class Transcript(BaseModel):
    language: str
    duration: float | None = None
    segments: list[Segment]
