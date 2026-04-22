# ─────────────────────────────────────────
# REVERIE — routes/schedule.py
# Sleep schedule calculator (rule-based + Gemini tip)
# ─────────────────────────────────────────

import os
import google.generativeai as genai
from fastapi import APIRouter
from backend.models.schemas import ScheduleRequest, ScheduleResponse

router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")


def _fmt(t: str | None) -> str:
    """Convert 24-h 'HH:MM' to '10:30 PM' for the prompt, or return 'N/A'."""
    if not t:
        return "N/A"
    try:
        h, m = map(int, t.split(":"))
        ampm = "AM" if h < 12 else "PM"
        return f"{h % 12 or 12}:{m:02d} {ampm}"
    except Exception:
        return t


@router.post("/calculate", response_model=ScheduleResponse)
async def calculate_schedule(req: ScheduleRequest):
    """
    Generates a personalised Gemini tip based on the full sleep profile
    already calculated by the client-side sleep engine.
    """
    factors_text = "\n".join(f"- {note}" for note in req.adjustments) if req.adjustments else "- No special factors detected"

    age_line = f"Age: {req.age}" if req.age else "Age: not provided"
    chronotype_map = {"early": "early bird", "night": "night owl", "middle": "neutral"}
    chronotype_line = f"Chronotype: {chronotype_map.get(req.chronotype or '', 'unknown')}"

    extra_context = []
    if req.caffeine_last_cup:
        extra_context.append(f"last caffeine at {_fmt(req.caffeine_last_cup)}")
    if req.last_meal_time:
        extra_context.append(f"last meal at {_fmt(req.last_meal_time)}")
    if req.exercise_timing and req.exercise_timing != "none":
        extra_context.append(f"{req.exercise_timing} exercise today")
    if req.stress_level and req.stress_level >= 4:
        extra_context.append(f"high stress (level {req.stress_level}/5)")
    if req.alcohol_nightly:
        extra_context.append("drinks alcohol most nights")
    if req.shift_work:
        extra_context.append("shift worker / irregular schedule")

    context_line = (", ".join(extra_context)) if extra_context else "no additional lifestyle factors noted"

    prompt = f"""You are a warm, knowledgeable sleep coach writing a personalised bedtime tip for a Reverie app user.

User profile:
- {age_line}
- {chronotype_line}
- Wake time: {_fmt(req.wake_time)}
- Recommended bedtime: {_fmt(req.bedtime)}
- Target sleep: {req.target_hours} hours
- Lifestyle: {context_line}

Factors that adjusted their bedtime tonight:
{factors_text}

Write ONE concise tip (2–3 sentences max) that is:
1. Specific to THEIR bedtime ({_fmt(req.bedtime)}) and the factors above — not generic advice
2. Actionable tonight, not a long-term habit
3. Warm and encouraging, not clinical

Respond with only the tip text, no labels or preamble."""

    try:
        response = model.generate_content(prompt)
        tip = response.text.strip()
    except Exception:
        tip = f"Tonight, start winding down at {_fmt(req.bedtime)} — dim your lights, put your phone face-down, and give yourself 20 minutes of quiet before sleep."

    return ScheduleResponse(tip=tip)
