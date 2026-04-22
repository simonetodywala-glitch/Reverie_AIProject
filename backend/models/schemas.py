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
    emotions: List[str]           # e.g. ["wonder", "anxiety", "excitement"]
    themes: List[str]             # e.g. ["Flying · freedom or desire for escape"]
    summary: str                  # 2-3 sentence warm interpretation
    interpretation: str           # Deeper psychological/emotional undercurrent
    reflections: List[str]        # 2-3 introspective questions tied to this dream


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class ScheduleRequest(BaseModel):
    wake_time: str                          # "07:00"
    bedtime: str                            # already-calculated bedtime from sleepEngine
    target_hours: float                     # e.g. 8.5
    age: Optional[int] = None
    caffeine_last_cup: Optional[str] = None  # "HH:MM" or null
    last_meal_time: Optional[str] = None
    exercise_timing: Optional[str] = "none"
    stress_level: Optional[int] = 2
    alcohol_nightly: Optional[bool] = False
    shift_work: Optional[bool] = False
    chronotype: Optional[str] = None
    adjustments: Optional[List[str]] = []   # human-readable factor notes


class ScheduleResponse(BaseModel):
    tip: str                                # Gemini-generated personalized advice


class AudioRequest(BaseModel):
    dream_text: str


class AudioResponse(BaseModel):
    audio_url: str
