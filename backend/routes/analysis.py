import os
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse

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
async def chat(req: ChatRequest):
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


@router.get("/patterns/{user_id}")
async def get_patterns(user_id: str):
    return {
        "unlocked": False,
        "dreams_needed": 2,
        "message": "Log 2 more dreams to unlock your pattern report."
    }
