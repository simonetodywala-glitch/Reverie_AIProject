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
model = genai.GenerativeModel("gemini-1.5-flash")  # free tier model


@router.post("/analyze", response_model=DreamAnalysis)
async def analyze_dream(req: DreamRequest):
    """
    Takes a dream description and returns emotions, themes, and a summary.
    Powered by Google Gemini.
    """
    prompt = f"""
You are a warm, insightful dream analysis assistant for an app called Reverie.

Analyze this dream journal entry and respond ONLY with a JSON object (no markdown, no extra text):

Dream: "{req.text}"

Return this exact JSON structure:
{{
  "emotions": ["emotion1", "emotion2", "emotion3"],
  "themes": ["Theme · brief explanation", "Theme · brief explanation"],
  "summary": "One paragraph interpretation in warm, non-clinical language."
}}

Emotions should be single words from: wonder, anxiety, joy, fear, sadness, excitement, nostalgia, peaceful, confusion, hope.
Themes should be concrete symbols or situations from the dream.
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        return DreamAnalysis(**data)

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
