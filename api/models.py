from __future__ import annotations
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    device: str
    version: str


class TranscribeMetadata(BaseModel):
    language: str
    segments: int
    duration: float | None
    filename: str
