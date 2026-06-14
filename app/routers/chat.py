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
    language:        str  = "Hindi"
    user_emotion:    Optional[str]  = None
    room_conditions: Optional[dict] = None
    user_id:         str  = "default"


LANGUAGE_INSTRUCTIONS = {
    "Hindi":    "Respond in Hindi (Devanagari script). Be warm and friendly like a helpful friend. Use simple everyday Hindi.",
    "Hinglish": "Respond in Hinglish — natural mix of Hindi and English like young Indians speak. Be casual and friendly.",
    "English":  "Respond in English. Be warm, helpful and friendly.",
    "Tamil":    "Respond in Tamil. Be warm and friendly.",
    "Telugu":   "Respond in Telugu. Be warm and friendly.",
    "Bengali":  "Respond in Bengali. Be warm and friendly.",
    "Marathi":  "Respond in Marathi. Be warm and friendly.",
    "Gujarati": "Respond in Gujarati. Be warm and friendly.",
    "Kannada":  "Respond in Kannada. Be warm and friendly.",
    "Malayalam":"Respond in Malayalam. Be warm and friendly.",
    "Punjabi":  "Respond in Punjabi. Be warm and friendly.",
    "Sanskrit": "Respond in simple Sanskrit. Be respectful and wise.",
}

# Fallback responses when API not available
FALLBACK_RESPONSES = {
    "Hindi":    "नमस्ते! मैं आपका स्मार्ट होम असिस्टेंट हूं। आप कैसा महसूस कर रहे हैं? मैं आपके घर को आपके अनुसार बेहतर बनाने में मदद करूंगा।",
    "Hinglish": "Hey! Main aapka smart home assistant hoon. Aap kaisa feel kar rahe ho? Batao, main help karunga!",
    "English":  "Hello! I am your smart home assistant. How are you feeling today? I can help adjust your environment for better comfort.",
    "Tamil":    "வணக்கம்! நான் உங்கள் ஸ்மார்ட் ஹோம் உதவியாளர். நீங்கள் எப்படி உணர்கிறீர்கள்?",
    "Telugu":   "నమస్కారం! నేను మీ స్మార్ట్ హోమ్ అసిస్టెంట్. మీరు ఎలా అనుభవిస్తున్నారు?",
    "Bengali":  "নমস্কার! আমি আপনার স্মার্ট হোম অ্যাসিস্ট্যান্ট। আপনি কেমন অনুভব করছেন?",
    "Marathi":  "नमस्कार! मी तुमचा स्मार्ट होम असिस्टंट आहे। तुम्ही कसे वाटत आहे?",
    "Gujarati": "નમસ્તે! હું તમારો સ્માર્ટ હોમ આસિસ્ટન્ટ છું. તમે કેવું અનુભવો છો?",
    "Kannada":  "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಹೋಮ್ ಅಸಿಸ್ಟೆಂಟ್. ನೀವು ಹೇಗಿದ್ದೀರಿ?",
    "Malayalam":"നമസ്കാരം! ഞാൻ നിങ്ങളുടെ സ്മാർട്ട് ഹോം അസിസ്റ്റന്റ് ആണ്. നിങ്ങൾക്ക് എങ്ങനെ തോന്നുന്നു?",
    "Punjabi":  "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਸਮਾਰਟ ਹੋਮ ਅਸਿਸਟੈਂਟ ਹਾਂ। ਤੁਸੀਂ ਕਿਵੇਂ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ?",
}


def get_groq_response(messages: list, system_prompt: str) -> str:
    """Try Groq API first — free and fast."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model    = "llama-3.1-8b-instant",
            messages = [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            max_tokens  = 300,
            temperature = 0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return None


def get_gemini_response(messages: list, system_prompt: str) -> str:
    """Try Gemini API as backup — also free."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name    = "gemini-1.5-flash",
            system_instruction = system_prompt,
        )
        # Convert messages to Gemini format
        history = []
        for msg in messages[:-1]:
            history.append({
                "role":  "user"  if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            })
        chat    = model.start_chat(history=history)
        last    = messages[-1]["content"] if messages else "Hello"
        response= chat.send_message(last)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


@router.post("/message")
def chat(req: ChatRequest):
    """
    Conversational AI in user's language.
    Uses Groq (free) → Gemini (free) → fallback response.
    """
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(
        req.language,
        f"Respond in {req.language}. Be warm and friendly."
    )

    system_prompt = f"""You are a friendly AI smart home assistant for Indian families. {lang_instruction}

You help users with:
- Home comfort (temperature, noise, light adjustments)
- Emotional well-being and stress relief
- Energy saving tips in simple language
- Sleep quality improvement
- Health-based environment suggestions
- Indian home remedies (gharelu upay) for common conditions

Keep responses SHORT — 2-3 sentences only.
Be warm and caring like a good family friend (dost/bhai/didi).
Use simple everyday language, not technical terms.
If suggesting adjustments, be specific: "AC ko 22°C par set karo" not just "cool the room".

Current context:
- User emotion: {req.user_emotion or 'not detected yet'}
- Room conditions: {req.room_conditions or 'not available'}
- Language preference: {req.language}
"""

    messages = [
        {"role": m.role, "content": m.content}
        for m in req.messages
    ]

    # Try Groq first
    reply = get_groq_response(messages, system_prompt)
    source = "groq"

    # Try Gemini as backup
    if not reply:
        reply  = get_gemini_response(messages, system_prompt)
        source = "gemini"

    # Use fallback if both fail
    if not reply:
        reply  = FALLBACK_RESPONSES.get(req.language, FALLBACK_RESPONSES["English"])
        source = "fallback"

    return {
        "reply":    reply,
        "language": req.language,
        "source":   source,
    }


@router.get("/languages")
def supported_languages():
    return {
        "languages": list(LANGUAGE_INSTRUCTIONS.keys()),
        "total":     len(LANGUAGE_INSTRUCTIONS),
    }
