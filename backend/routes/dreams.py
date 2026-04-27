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


def _build_user_context(req: DreamRequest) -> tuple[str, str]:
    """Returns (profile_block, waking_block) to inject into the prompt."""
    profile_parts = []

    if req.eye_dominance and req.eye_dominance != "unsure":
        if req.eye_dominance == "left":
            style = "left-eye dominant — tends toward right-hemisphere processing (holistic, spatial, metaphorical, emotionally intuitive)"
        else:
            style = "right-eye dominant — tends toward left-hemisphere processing (analytical, sequential, detail-oriented, logical)"

        cross = (
            req.handedness in ("right", "left") and
            req.eye_dominance in ("left", "right") and
            req.eye_dominance != req.handedness[0]  # e.g. right-handed + left-eye
        )
        if cross:
            style += ". CROSS-DOMINANT: opposite hand/eye dominance — research links this to more flexible hemispheric communication and often more vivid or unconventional dream imagery"

        profile_parts.append(f"Cognitive style: {style}")

    if req.handedness:
        profile_parts.append(f"Handedness: {req.handedness}")

    profile_block = "\n".join(profile_parts)
    waking_block  = req.waking_context.strip() if req.waking_context else ""
    return profile_block, waking_block


@router.post("/analyze", response_model=DreamAnalysis)
async def analyze_dream(req: DreamRequest):
    dream_text = req.text[:MAX_DREAM_CHARS]
    profile_block, waking_block = _build_user_context(req)

    context_section = ""
    if profile_block:
        context_section += f"\nUser cognitive profile:\n{profile_block}\n"
    if waking_block:
        context_section += f"\nWhat's on the user's mind today (waking life context):\n\"{waking_block}\"\n"

    waking_instructions = ""
    if waking_block:
        waking_instructions = """
  "waking_connections": "1-2 specific sentences directly connecting imagery or emotions in THIS dream to the waking life context the user shared. Be concrete — name the dream element and the life situation. Do not be generic.","""

    mind_instructions = ""
    if profile_block:
        mind_instructions = """
  "mind_note": "1 sentence about how the user's cognitive processing style (eye dominance / cross-dominance) may relate to the character or emotional texture of this specific dream.","""

    prompt = f"""You are a warm, psychologically-informed dream analyst for Reverie. Help users understand themselves through their dreams — not to diagnose, but to gently illuminate patterns, emotions, and meanings.
{context_section}
Dream entry:
\"\"\"
{dream_text}
\"\"\"

Analyze with depth and care:
- Full emotional texture (underlying currents, not just surface feelings)
- Symbols, archetypes, narrative patterns — referenced from actual dream imagery
- What the subconscious may be processing
- If waking life context was provided, how the dream may connect to it
- If a cognitive profile was provided, how it may shape the dream's character

Respond ONLY with a valid JSON object — no markdown, no extra text.

{{
  "emotions": ["word1", "word2"],
  "themes": ["Dream element · what it may represent", "Dream element · what it may represent"],
  "summary": "2-3 warm sentences interpreting the dream as a whole. Speak directly to the dreamer using 'you'. Weave symbols and emotions into a coherent narrative.",
  "interpretation": "1-2 paragraphs on the deeper psychological/emotional undercurrent. Reference specific imagery. Avoid generic statements.",
  "reflections": [
    "Introspective question tied to a specific image or moment in this dream?",
    "Question connecting the dream's emotional core to waking life?",
    "Question inviting the dreamer to sit with an unresolved tension?"
  ]{waking_instructions}{mind_instructions}
}}

Emotion words: wonder, anxiety, joy, fear, sadness, excitement, nostalgia, peaceful, confusion, hope, longing, dread, awe, grief, frustration, tenderness, shame, pride, restlessness, relief.
Use 2-5 emotions. Themes must reference actual dream elements."""

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
