# ─────────────────────────────────────────
# REVERIE — routes/analysis.py
# AI chatbot + dream pattern analysis
# ─────────────────────────────────────────

import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Personal sleep chatbot. Uses Gemini with the user's dream history as context.
    TODO Week 5: Pull real dream history from Firebase Firestore.
    """
    # Placeholder dream context — will come from Firebase in Week 5
    dream_context = """
    User's recent dreams:
    - Apr 16: Flying over a glass city, kept falling through buildings. Emotions: wonder, anxiety.
    - Apr 14: Swimming in a bioluminescent ocean. Emotions: peaceful, wonder.
    - Apr 12: Being chased through a forest. Emotions: anxiety, fear.
    """

    prompt = f"""
You are Reverie, a warm and insightful AI sleep and dream companion.
You have access to this user's dream journal:

{dream_context}

The user asks: "{req.message}"

Respond in 2-3 sentences. Be warm, personal, and reference their specific dreams when relevant.
Don't be clinical. Don't make up information not in their journal.
"""

    try:
        response = model.generate_content(prompt)
        return ChatResponse(reply=response.text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/patterns/{user_id}")
async def get_patterns(user_id: str):
    """
    Analyze patterns across all of a user's dreams.
    Requires 5+ dreams. TODO Week 5: Connect to real Firebase data.
    """
    # Placeholder until Firebase + 5-dream threshold is implemented
    return {
        "unlocked": False,
        "dreams_needed": 2,
        "message": "Log 2 more dreams to unlock your pattern report."
    }
