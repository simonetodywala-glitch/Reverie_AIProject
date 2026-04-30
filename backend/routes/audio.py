import os
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
import json
from backend.models.schemas import (
    AudioRequest, AudioResponse, SoundscapeRequest,
    SoundscapeMenuRequest, SoundscapeMenuResponse,
)
from backend.auth import verify_token

router = APIRouter()

GROQ_URL          = "https://api.groq.com/openai/v1/chat/completions"
GROQ_WHISPER_URL  = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL        = "llama-3.3-70b-versatile"

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
async def generate_story(req: AudioRequest, _=Depends(verify_token)):
    try:
        story_text = await dream_to_story(req.dream_text)
        return AudioResponse(audio_url=f"STORY_TEXT:{story_text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), _=Depends(verify_token)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    audio_data = await file.read()
    filename = file.filename or "dream.webm"
    content_type = file.content_type or "audio/webm"

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            GROQ_WHISPER_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, audio_data, content_type)},
            data={"model": "whisper-large-v3"},
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Whisper error {res.status_code}: {res.text}")
        return {"text": res.json().get("text", "")}


EMOTION_SOUNDS = {
    "anxiety":     "tense atmospheric hum, low unsettling tones, still and uneasy",
    "fear":        "dark ambient drone, low rumbling, distant hollow echoes",
    "wonder":      "ethereal floating pads, soft crystalline tones, vast and spacious",
    "peaceful":    "gentle rain on leaves, soft wind, distant water, calm and still",
    "joy":         "warm bright ambient tones, light breeze, soft natural textures",
    "sadness":     "melancholic slow pads, quiet and still, soft distant rain",
    "excitement":  "rising ambient energy, open air, subtle pulse and movement",
    "nostalgia":   "warm hazy ambient, soft vintage texture, gentle distant tone",
    "confusion":   "layered shifting tones, overlapping soft textures, slowly drifting",
    "awe":         "vast expansive soundscape, deep reverb, celestial resonance",
    "dread":       "slow building ominous drone, deep bass, cold still air",
    "longing":     "haunting open space, soft resonance, quiet and searching",
    "grief":       "quiet, heavy ambient, very slow movement, deep stillness",
    "hope":        "gentle rising tones, warm pads, soft light texture",
    "tenderness":  "soft warm ambient, intimate and close, gentle and quiet",
    "restlessness":"shifting layered tones, subtle unease, never quite settling",
    "relief":      "slow exhale of sound, warmth returning, open and soft",
    "awe":         "vast reverberant space, deep and slow, celestial and open",
    "pride":       "full warm tones, grounded and steady, quietly expansive",
    "shame":       "withdrawn ambient, quiet and inward, low and soft",
}


def _build_soundscape_prompt(emotions: list, themes: list) -> str:
    descriptors = [EMOTION_SOUNDS[e.lower()] for e in emotions[:3] if e.lower() in EMOTION_SOUNDS]
    if not descriptors:
        descriptors = ["dreamlike ambient atmosphere, soft and immersive"]
    prompt = f"Ambient dreamscape soundscape: {'; '.join(descriptors)}. Atmospheric, immersive, seamlessly loopable, no sudden changes, no melody, pure texture."
    return prompt


@router.post("/soundscape-menu", response_model=SoundscapeMenuResponse)
async def get_soundscape_menu(req: SoundscapeMenuRequest, _=Depends(verify_token)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    if req.custom_prompt:
        prompt = f"""Generate one ambient sleep soundscape for this description: "{req.custom_prompt}"

Return JSON with this exact structure:
{{
  "soundscapes": [
    {{
      "name": "poetic 2-4 word name (specific, not generic)",
      "description": "one atmospheric sentence capturing the feeling",
      "emoji": "single relevant emoji",
      "base": "one of: rain, ocean, forest, fire, space, storm, cafe",
      "params": {{
        "filter_freq": <200-8000, controls brightness>,
        "lfo_rate": <0.03-0.5, controls movement speed>,
        "lfo_depth": <0.05-0.35, controls variation>,
        "gain": <0.15-0.75>
      }}
    }}
  ]
}}"""
    else:
        emotions_str = ", ".join(req.emotions[:5]) if req.emotions else "calm, reflective"
        themes_str = ", ".join(req.themes[:3]) if req.themes else "rest"
        prompt = f"""Generate 6 ambient sleep soundscapes for someone whose dream had these emotions: {emotions_str}, and themes: {themes_str}.

Rules:
- Names must be poetic and specific — think ambient album titles, not generic labels
- Descriptions are one sentence, sensory, atmospheric
- Vary the base types across the 6
- Params should reflect the name's character (dark = low filter_freq, bright = high)

Return JSON:
{{
  "soundscapes": [
    {{
      "name": "poetic 2-4 word title",
      "description": "one atmospheric sentence",
      "emoji": "single emoji",
      "base": "rain|ocean|forest|fire|space|storm|cafe",
      "params": {{
        "filter_freq": <200-8000>,
        "lfo_rate": <0.03-0.5>,
        "lfo_depth": <0.05-0.35>,
        "gain": <0.15-0.75>
      }}
    }}
  ]
}}"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "response_format": {"type": "json_object"},
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq error {res.status_code}")
        data = json.loads(res.json()["choices"][0]["message"]["content"])

    soundscapes = data.get("soundscapes", [])
    if not soundscapes:
        raise HTTPException(status_code=500, detail="No soundscapes returned")

    return SoundscapeMenuResponse(soundscapes=[
        {"name": s.get("name",""), "description": s.get("description",""),
         "emoji": s.get("emoji","🎵"), "base": s.get("base","rain"),
         "params": s.get("params",{})}
        for s in soundscapes
    ])


@router.post("/soundscape")
async def generate_soundscape(req: SoundscapeRequest, _=Depends(verify_token)):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")

    prompt = _build_soundscape_prompt(req.emotions, req.themes)

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={"text": prompt, "duration_seconds": 22, "prompt_influence": 0.4},
        )
        if res.status_code != 200:
            print(f"ElevenLabs {res.status_code}: {res.text}")
            try:
                detail = res.json()
            except Exception:
                detail = res.text
            raise HTTPException(status_code=500, detail=f"ElevenLabs error {res.status_code}: {detail}")

        audio_bytes = res.content

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=soundscape.mp3"}
    )
