import os
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import AudioRequest, AudioResponse

router = APIRouter()

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


async def dream_to_story(dream_text: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    prompt = f"""Rewrite this dream as a slow, peaceful, third-person bedtime story (150-200 words).
Soften any anxious or scary elements into something calming and beautiful.
Use gentle, flowing language. End with the character falling peacefully asleep.

Dream: "{dream_text}"
"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq error {res.status_code}")
        return res.json()["choices"][0]["message"]["content"].strip()


@router.post("/story", response_model=AudioResponse)
async def generate_story(req: AudioRequest):
    try:
        story_text = await dream_to_story(req.dream_text)
        return AudioResponse(audio_url=f"STORY_TEXT:{story_text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/soundscape/{mood}")
async def get_soundscape(mood: str):
    return {
        "mood": mood,
        "audio_url": None,
        "message": "ElevenLabs soundscape generation coming soon"
    }
