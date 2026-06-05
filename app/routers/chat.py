from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter(prefix="/chat", tags=["Conversational AI"])


class Message(BaseModel):
    role:    str
    content: str


class ChatRequest(BaseModel):
    messages:        List[Message]
    language:        str   = "Hindi"
    user_emotion:    Optional[str]  = None
    room_conditions: Optional[dict] = None
    user_id:         str   = "default"


LANGUAGE_INSTRUCTIONS = {
    "Hindi":    "Respond in Hindi (Devanagari script). Be warm and friendly like a helpful friend.",
    "Hinglish": "Respond in Hinglish (mix of Hindi and English). Be casual and friendly.",
    "English":  "Respond in English. Be warm and helpful.",
    "Tamil":    "Respond in Tamil. Be warm and friendly.",
    "Telugu":   "Respond in Telugu. Be warm and friendly.",
    "Bengali":  "Respond in Bengali. Be warm and friendly.",
    "Marathi":  "Respond in Marathi. Be warm and friendly.",
    "Gujarati": "Respond in Gujarati. Be warm and friendly.",
    "Kannada":  "Respond in Kannada. Be warm and friendly.",
    "Malayalam":"Respond in Malayalam. Be warm and friendly.",
    "Punjabi":  "Respond in Punjabi. Be warm and friendly.",
}


@router.post("/message")
def chat(req: ChatRequest):
    """
    Conversational AI that talks to the user in their language.
    Uses Anthropic Claude API for natural conversation.
    Knows about user's emotion and room conditions.
    """
    import anthropic

    lang_instruction = LANGUAGE_INSTRUCTIONS.get(
        req.language,
        f"Respond in {req.language}. Be warm and friendly."
    )

    system_prompt = f"""You are a friendly AI smart home assistant. {lang_instruction}

You help users with:
- Understanding their home environment (temperature, noise, comfort)
- Emotional well-being and stress management
- Energy saving tips
- Sleep quality improvement
- Health-based environment suggestions

Keep responses SHORT and CONVERSATIONAL — 2-3 sentences maximum.
Be warm, caring, and supportive like a good friend.
Never be clinical or robotic.

Current context:
- User emotion: {req.user_emotion or 'unknown'}
- Room conditions: {req.room_conditions or 'not available'}
"""

    messages = [
        {"role": m.role, "content": m.content}
        for m in req.messages
    ]

    try:
        client   = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 300,
            system     = system_prompt,
            messages   = messages,
        )
        reply = response.content[0].text

        return {
            "reply":    reply,
            "language": req.language,
            "tokens":   response.usage.output_tokens,
        }

    except Exception as e:
        # Fallback response if API key not set
        fallbacks = {
            "Hindi":    "नमस्ते! मैं आपका स्मार्ट होम असिस्टेंट हूं। आप कैसा महसूस कर रहे हैं?",
            "Hinglish": "Hey! Main aapka smart home assistant hoon. Aap kaisa feel kar rahe ho?",
            "English":  "Hello! I'm your smart home assistant. How are you feeling today?",
            "Tamil":    "வணக்கம்! நான் உங்கள் ஸ்மார்ட் ஹோம் அசிஸ்டன்ட். நீங்கள் எப்படி உணர்கிறீர்கள்?",
        }
        return {
            "reply":    fallbacks.get(req.language, fallbacks["English"]),
            "language": req.language,
            "note":     "API key not configured — using fallback response",
            "error":    str(e),
        }
