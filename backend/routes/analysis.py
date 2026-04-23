import os
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


async def _call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
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
            detail = res.json().get("error", {}).get("message", f"Groq error {res.status_code}")
            raise HTTPException(status_code=500, detail=detail)
        return res.json()["choices"][0]["message"]["content"].strip()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    dream_context = """
    User's recent dreams:
    - Apr 16: Flying over a glass city, kept falling through buildings. Emotions: wonder, anxiety.
    - Apr 14: Swimming in a bioluminescent ocean. Emotions: peaceful, wonder.
    - Apr 12: Being chased through a forest. Emotions: anxiety, fear.
    """

    prompt = f"""You are Reverie, a warm and insightful AI sleep and dream companion.
You have access to this user's dream journal:

{dream_context}

The user asks: "{req.message}"

Respond in 2-3 sentences. Be warm, personal, and reference their specific dreams when relevant.
Don't be clinical. Don't make up information not in their journal."""

    reply = await _call_groq(prompt)
    return ChatResponse(reply=reply)


@router.get("/patterns/{user_id}")
async def get_patterns(user_id: str):
    return {
        "unlocked": False,
        "dreams_needed": 2,
        "message": "Log 2 more dreams to unlock your pattern report."
    }
