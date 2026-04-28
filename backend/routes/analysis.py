import os
import json
import httpx
from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import ChatRequest, ChatResponse, PatternRequest, PatternReport
from backend.auth import verify_token

router = APIRouter()

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


async def _call_groq_messages(messages: list) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.7},
        )
        if res.status_code != 200:
            detail = res.json().get("error", {}).get("message", f"Groq error {res.status_code}")
            raise HTTPException(status_code=500, detail=detail)
        return res.json()["choices"][0]["message"]["content"].strip()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, _=Depends(verify_token)):
    if req.dream_context:
        system = f"""You are Reverie, a warm and curious dream companion. The user is exploring a specific dream with you.

Dream they're exploring:
{req.dream_context}

Your role: help them go deeper — unpack symbols, sit with emotions, find connections to their waking life. Be warm and specific to this dream. Never clinical. Never invent details they haven't shared. Keep responses to 2-4 sentences unless they ask for more depth."""
    else:
        system = """You are Reverie, a warm and insightful AI dream companion. Help the user explore and understand their dreams. Be warm, curious, and specific. Never clinical. 2-4 sentences per reply."""

    messages = [
        {"role": "system", "content": system},
        *[{"role": m.role, "content": m.content} for m in (req.history or [])],
        {"role": "user", "content": req.message},
    ]

    reply = await _call_groq_messages(messages)
    return ChatResponse(reply=reply)


async def _call_groq_json(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    async with httpx.AsyncClient(timeout=45.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
        )
        if res.status_code != 200:
            detail = res.json().get("error", {}).get("message", f"Groq error {res.status_code}")
            raise HTTPException(status_code=500, detail=detail)
        return res.json()["choices"][0]["message"]["content"]


@router.post("/patterns", response_model=PatternReport)
async def get_patterns(req: PatternRequest, _=Depends(verify_token)):
    if len(req.dreams) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 dreams for pattern analysis")

    dream_lines = []
    for i, d in enumerate(req.dreams, 1):
        emotions_str = ", ".join(d.emotions) if d.emotions else "none"
        themes_str   = " | ".join(d.themes[:4]) if d.themes else "none"
        dream_lines.append(
            f"Dream {i} ({d.date or 'unknown'}):\n"
            f"  Emotions: {emotions_str}\n"
            f"  Themes: {themes_str}\n"
            f"  Summary: {d.summary}"
        )

    prompt = f"""You are Reverie, a warm dream analyst. Analyze these {len(req.dreams)} dream entries and find the patterns that reveal what the dreamer's subconscious is working through over time.

{chr(10).join(dream_lines)}

Look for emotions that recur most often, symbols or settings that appear across multiple dreams, and any evolution or shift in the dreamer's inner world over time.

Respond ONLY with valid JSON — no markdown, no extra text:

{{
  "top_emotions": ["top 3-4 emotions that appear most across these dreams"],
  "recurring_themes": ["3-4 pattern descriptions like 'being chased or pursued', 'loss of control in familiar places'"],
  "narrative": "2-3 warm sentences about what this collection of dreams reveals about the dreamer's inner world right now. Speak directly using 'you'. Be specific to actual patterns in the data — not generic.",
  "insight": "1 sentence — the single most striking pattern or shift you noticed across these dreams.",
  "reflections": [
    "A question about a pattern you noticed recurring across multiple dreams?",
    "A question about what the dreamer might be carrying or working through?",
    "A question that invites them to notice a shift or evolution in their inner world?"
  ]
}}"""

    try:
        raw  = await _call_groq_json(prompt)
        data = json.loads(raw)
        return PatternReport(**data)
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")
