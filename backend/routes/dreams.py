# ─────────────────────────────────────────
# REVERIE — routes/dreams.py
# Dream CRUD + Gemini emotion/theme analysis
# ─────────────────────────────────────────

import os
import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from backend.models.schemas import DreamRequest, DreamAnalysis

router = APIRouter()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

MAX_DREAM_CHARS = 4000


@router.post("/analyze", response_model=DreamAnalysis)
async def analyze_dream(req: DreamRequest):
    """
    Takes a dream description and returns a rich multi-field analysis.
    Powered by Google Gemini 2.0 Flash.
    """
    dream_text = req.text[:MAX_DREAM_CHARS]

    prompt = f"""
You are a warm, psychologically-informed dream analyst for an app called Reverie. Your role is to help users understand themselves through their dreams — not to diagnose, but to gently illuminate patterns, emotions, and meanings.

Analyze the dream journal entry below with depth and care. Look for:
- The full emotional texture (not just surface feelings, but underlying currents)
- Recurring symbols, archetypes, and narrative patterns
- Connections between dream imagery and common psychological themes (loss, control, identity, relationships, transitions, fear, desire)
- What the dreamer's subconscious may be processing

Dream entry:
\"\"\"
{dream_text}
\"\"\"

Respond ONLY with a valid JSON object — no markdown fences, no extra text, no explanations outside the JSON.

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

Emotion words should capture the full range: wonder, anxiety, joy, fear, sadness, excitement, nostalgia, peaceful, confusion, hope, longing, dread, awe, grief, frustration, tenderness, shame, pride, restlessness, relief.
Use 2-5 emotions that genuinely fit this dream.
Themes should reference actual elements from the dream (people, places, objects, actions) — not generic labels.
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        return DreamAnalysis(**data)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Gemini returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini analysis failed: {str(e)}")


@router.get("/{user_id}")
async def get_dreams(user_id: str):
    """
    Get all dream entries for a user.
    TODO Week 3: Replace with real Firebase Firestore query.
    """
    # Placeholder response until Firebase is connected
    return {
        "dreams": [
            {
                "id": "1",
                "date": "2026-04-16",
                "text": "Flying over a glass city...",
                "emotions": ["wonder", "anxiety"],
                "themes": ["Flying · freedom", "Glass · fragility"],
                "summary": "A dream about navigating beauty and instability."
            }
        ],
        "count": 1
    }
