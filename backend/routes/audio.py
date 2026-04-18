# ─────────────────────────────────────────
# REVERIE — routes/audio.py
# ElevenLabs TTS (bedtime stories) + soundscapes
# To be fully implemented in Week 5
# ─────────────────────────────────────────

import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from backend.models.schemas import AudioRequest, AudioResponse

router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


async def dream_to_story(dream_text: str) -> str:
    """Use Gemini to rewrite a dream as a calming bedtime story."""
    prompt = f"""
Rewrite this dream as a slow, peaceful, third-person bedtime story (150-200 words).
Soften any anxious or scary elements into something calming and beautiful.
Use gentle, flowing language. End with the character falling peacefully asleep.

Dream: "{dream_text}"
"""
    response = model.generate_content(prompt)
    return response.text.strip()


@router.post("/story", response_model=AudioResponse)
async def generate_story(req: AudioRequest):
    """
    Step 1: Gemini rewrites dream as bedtime story.
    Step 2: ElevenLabs converts to audio.
    TODO Week 5: Connect ElevenLabs API and save audio to Firebase Storage.
    """
    try:
        story_text = await dream_to_story(req.dream_text)
        # TODO Week 5: Send story_text to ElevenLabs TTS API
        # For now, return the story text so the frontend knows it works
        return AudioResponse(audio_url=f"STORY_TEXT:{story_text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/soundscape/{mood}")
async def get_soundscape(mood: str):
    """
    Returns a soundscape audio URL for the given mood.
    TODO Week 5: Generate via ElevenLabs and cache in Firebase Storage.
    """
    # Placeholder until ElevenLabs is connected
    return {
        "mood": mood,
        "audio_url": None,
        "message": "ElevenLabs soundscape generation coming in Week 5"
    }
