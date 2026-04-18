# ─────────────────────────────────────────
# REVERIE — schemas.py
# Pydantic models for request/response validation
# ─────────────────────────────────────────

from pydantic import BaseModel
from typing import List, Optional


class DreamRequest(BaseModel):
    text: str               # The dream description typed by the user
    user_id: Optional[str] = "demo-user"


class DreamAnalysis(BaseModel):
    emotions: List[str]     # e.g. ["wonder", "anxiety", "excitement"]
    themes: List[str]       # e.g. ["Flying · freedom", "Glass · fragility"]
    summary: str            # One paragraph interpretation


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class ScheduleRequest(BaseModel):
    age: int
    wake_time: str          # "07:00"


class ScheduleResponse(BaseModel):
    bedtime: str
    recommended_hours: int
    tip: str                # Gemini-generated personalized advice


class AudioRequest(BaseModel):
    dream_text: str


class AudioResponse(BaseModel):
    audio_url: str
