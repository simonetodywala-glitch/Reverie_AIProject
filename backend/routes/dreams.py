# ─────────────────────────────────────────
# REVERIE — routes/dreams.py
# Dream CRUD + Groq AI emotion/theme analysis
# ─────────────────────────────────────────

import os
import json
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import DreamRequest, DreamAnalysis

router = APIRouter()

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_DREAM_CHARS = 4000


async def _call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in backend/.env")
    async with httpx.AsyncClient(timeout=30.0) as client:
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


@router.post("/analyze", response_model=DreamAnalysis)
async def analyze_dream(req: DreamRequest):
    dream_text = req.text[:MAX_DREAM_CHARS]

    prompt = f"""You are a warm, psychologically-informed dream analyst for an app called Reverie. Your role is to help users understand themselves through their dreams — not to diagnose, but to gently illuminate patterns, emotions, and meanings.

Analyze the dream journal entry below with depth and care. Look for:
- The full emotional texture (not just surface feelings, but underlying currents)
- Recurring symbols, archetypes, and narrative patterns
- Connections between dream imagery and common psychological themes (loss, control, identity, relationships, transitions, fear, desire)
- What the dreamer's subconscious may be processing

Dream entry:
\"\"\"
{dream_text}
\"\"\"

Respond ONLY with a valid JSON object — no markdown fences, no extra text.

Return this exact structure:
{{
  "emotions": ["word1", "word2", "word3"],
  "themes": ["Symbol or situation · what it may represent in this dream", "Symbol or situation · what it may represent"],
  "summary": "2-3 warm sentences interpreting the dream as a whole. Weave the symbols and emotions together into a coherent narrative. Speak directly to the dreamer using 'you'.",
  "interpretation": "1-2 paragraphs exploring the deeper psychological or emotional undercurrent. What might the dreamer be working through in waking life? Reference specific imagery from the dream to ground your interpretation. Avoid generic statements — make it specific to this dream.",
  "reflections": [
    "An introspective question tied to a specific image or moment in this dream?",
    "A question that connects the dream's emotional core to the dreamer's waking life?",
    "A question that invites the dreamer to sit with an unresolved tension from the dream?"
  ]
}}

Emotion words: wonder, anxiety, joy, fear, sadness, excitement, nostalgia, peaceful, confusion, hope, longing, dread, awe, grief, frustration, tenderness, shame, pride, restlessness, relief.
Use 2-5 emotions that genuinely fit this dream.
Themes should reference actual elements from the dream — not generic labels."""

    try:
        raw  = await _call_groq(prompt)
        data = json.loads(raw)
        return DreamAnalysis(**data)
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{user_id}")
async def get_dreams(user_id: str):
    return {"dreams": [], "count": 0}
