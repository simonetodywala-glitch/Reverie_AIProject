# ─────────────────────────────────────────
# REVERIE — routes/schedule.py
# Sleep schedule calculator (rule-based + Gemini tip)
# ─────────────────────────────────────────

import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ScheduleRequest, ScheduleResponse

router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def calculate_bedtime(age: int, wake_time: str) -> tuple[int, str]:
    """Rule-based bedtime calculation. No AI needed here."""
    # Recommended sleep hours by age
    if age <= 13:
        recommended = 10
    elif age <= 17:
        recommended = 9
    elif age <= 64:
        recommended = 8
    else:
        recommended = 7

    # Parse wake time and subtract recommended hours
    wake_h, wake_m = map(int, wake_time.split(":"))
    bed_h = (wake_h - recommended) % 24

    # Format as readable time
    period = "AM" if bed_h < 12 else "PM"
    display_h = bed_h % 12 or 12
    bedtime_str = f"{display_h}:{str(wake_m).zfill(2)} {period}"

    return recommended, bedtime_str


@router.post("/calculate", response_model=ScheduleResponse)
async def calculate_schedule(req: ScheduleRequest):
    """
    Calculates optimal bedtime from age + wake time.
    Then asks Gemini for one personalized tip.
    """
    recommended_hours, bedtime = calculate_bedtime(req.age, req.wake_time)

    # Ask Gemini for a personalized tip
    prompt = f"""
A {req.age}-year-old needs to wake up at {req.wake_time} and should get {recommended_hours} hours of sleep.
Their recommended bedtime is {bedtime}.

Give them ONE practical, specific tip (1-2 sentences) to help them actually fall asleep at that time.
Be warm and direct. No generic advice like "avoid caffeine" — make it specific to their schedule.
"""

    try:
        response = model.generate_content(prompt)
        tip = response.text.strip()
    except Exception:
        tip = f"Try starting your wind-down routine at {bedtime.replace('PM','').replace('AM','').strip()} — dim your lights and put your phone face-down 20 minutes before your target bedtime."

    return ScheduleResponse(
        bedtime=bedtime,
        recommended_hours=recommended_hours,
        tip=tip
    )
