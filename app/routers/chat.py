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
    "Hindi":     "Respond in Hindi (Devanagari script). Be warm and friendly like a helpful dost.",
    "Hinglish":  "Respond in Hinglish — natural mix of Hindi and English. Be casual and friendly yaar.",
    "English":   "Respond in English. Be warm and helpful.",
    "Bengali":   "Respond in Bengali (বাংলা). Be warm and friendly like a helpful bondhu.",
    "Telugu":    "Respond in Telugu (తెలుగు). Be warm and friendly.",
    "Marathi":   "Respond in Marathi (मराठी). Be warm and friendly like a helpful mitra.",
    "Tamil":     "Respond in Tamil (தமிழ்). Be warm and friendly like a helpful nanban.",
    "Gujarati":  "Respond in Gujarati (ગુજરાતી). Be warm and friendly like a helpful mitra.",
    "Kannada":   "Respond in Kannada (ಕನ್ನಡ). Be warm and friendly like a helpful geleya.",
    "Odia":      "Respond in Odia (ଓଡ଼ିଆ). Be warm and friendly.",
    "Malayalam": "Respond in Malayalam (മലയാളം). Be warm and friendly like a helpful kootukaran.",
    "Punjabi":   "Respond in Punjabi (ਪੰਜਾਬੀ). Be warm and friendly like a helpful yaar.",
    "Assamese":  "Respond in Assamese (অসমীয়া). Be warm and friendly like a helpful bhaai.",
    "Maithili":  "Respond in Maithili (मैथिली). Be warm and friendly.",
    "Sanskrit":  "Respond in simple conversational Sanskrit. Be wise and respectful.",
    "Urdu":      "Respond in Urdu (اردو script). Be warm and friendly like a helpful dost.",
    "Kashmiri":  "Respond in Kashmiri. Be warm and friendly.",
    "Konkani":   "Respond in Konkani. Be warm and friendly like a helpful dost.",
    "Sindhi":    "Respond in Sindhi. Be warm and friendly.",
    "Dogri":     "Respond in Dogri. Be warm and friendly.",
    "Manipuri":  "Respond in Manipuri (Meitei). Be warm and friendly.",
    "Bodo":      "Respond in Bodo. Be warm and friendly.",
    "Nepali":    "Respond in Nepali (नेपाली). Be warm and friendly like a helpful saathi.",
}
# Fallback responses when API not available
FALLBACK_RESPONSES = {
    "Hindi":     "नमस्ते! मैं आपका स्मार्ट होम असिस्टेंट हूं। आप कैसा महसूस कर रहे हैं?",
    "Hinglish":  "Hey yaar! Main aapka smart home assistant hoon. Kaisa feel kar rahe ho?",
    "English":   "Hello! I am your smart home assistant. How are you feeling today?",
    "Bengali":   "নমস্কার! আমি আপনার স্মার্ট হোম অ্যাসিস্ট্যান্ট। আপনি কেমন আছেন?",
    "Telugu":    "నమస్కారం! నేను మీ స్మార్ట్ హోమ్ అసిస్టెంట్. మీరు ఎలా ఉన్నారు?",
    "Marathi":   "नमस्कार! मी तुमचा स्मार्ट होम असिस्टंट आहे. तुम्ही कसे आहात?",
    "Tamil":     "வணக்கம்! நான் உங்கள் ஸ்மார்ட் ஹோம் உதவியாளர். நீங்கள் எப்படி இருக்கீங்க?",
    "Gujarati":  "નમસ્તે! હું તમારો સ્માર્ટ હોમ આસિસ્ટન્ટ છું. તમે કેમ છો?",
    "Kannada":   "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಹೋಮ್ ಅಸಿಸ್ಟೆಂಟ್. ನೀವು ಹೇಗಿದ್ದೀರಿ?",
    "Odia":      "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କ ସ୍ମାର୍ଟ ହୋମ ଆସିଷ୍ଟାଣ୍ଟ। ଆପଣ କେମିତି ଅଛନ୍ତି?",
    "Malayalam": "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ സ്മാർട്ട് ഹോം അസിസ്റ്റന്റ് ആണ്. സുഖമാണോ?",
    "Punjabi":   "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਸਮਾਰਟ ਹੋਮ ਅਸਿਸਟੈਂਟ ਹਾਂ। ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?",
    "Assamese":  "নমস্কাৰ! মই আপোনাৰ স্মাৰ্ট হোম এছিষ্টেণ্ট। আপুনি কেনে আছে?",
    "Maithili":  "प्रणाम! हम अहाँक स्मार्ट होम असिस्टेंट छी। अहाँ कोना छी?",
    "Sanskrit":  "नमस्ते! अहम् भवतः स्मार्ट गृह सहायकः अस्मि। भवान् कथम् अस्ति?",
    "Urdu":      "سلام! میں آپ کا سمارٹ ہوم اسسٹنٹ ہوں۔ آپ کیسے ہیں؟",
    "Kashmiri":  "آداب! مے تہوند سمارٹ ہوم اسسٹنٹ چھس۔",
    "Konkani":   "नमस्कार! हांव तुमचो स्मार्ट होम असिस्टंट आसा। तुमी कसे आसात?",
    "Sindhi":    "نمस्ते! مان توهانجو سمارٽ هوم اسسٽنٽ آهيان.",
    "Dogri":     "नमस्कार! मैं तुहाडा स्मार्ट होम असिस्टेंट आं। तुसी किस्से हो?",
    "Manipuri":  "নমস্কার! ꯑꯩ ꯑꯃꯥꯒꯤ ꯌꯥꯏꯐꯝ ꯑꯁꯤꯁ꯭ꯇꯦꯟꯇ ꯑꯣꯏꯔꯤ।",
    "Bodo":      "नमस्कार! आं नङौ स्मार्ट होम एसिस्टेन्ट।",
    "Nepali":    "नमस्ते! म तपाईंको स्मार्ट होम असिस्टेन्ट हुँ। तपाईं कस्तो हुनुहुन्छ?",
}


def get_groq_response(messages: list, system_prompt: str) -> str:
    """Try Groq API first — free and fast."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        print("GROQ_API_KEY not set in environment")
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
        print(f"Groq API error: {type(e).__name__}: {e}")
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
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(
        req.language, f"Respond in {req.language}. Be warm and friendly."
    )

    system_prompt = f"""You are a friendly AI smart home assistant for Indian families. {lang_instruction}

You help users with home comfort, emotional well-being, energy saving, sleep quality,
and health-based suggestions including Indian home remedies (gharelu upay).

Keep responses SHORT — 2-3 sentences only. Be warm like a good friend.
Respond specifically to what the user just said — do not repeat a generic greeting.

Current context:
- User emotion: {req.user_emotion or 'not detected yet'}
- Room conditions: {req.room_conditions or 'not available'}
"""

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    reply  = get_groq_response(messages, system_prompt)
    source = "groq"

    if not reply:
        reply  = get_gemini_response(messages, system_prompt)
        source = "gemini"

    if not reply:
        reply  = FALLBACK_RESPONSES.get(req.language, FALLBACK_RESPONSES["English"])
        source = "fallback"

    return {"reply": reply, "language": req.language, "source": source}

@router.get("/languages")
def supported_languages():
    return {
        "languages": list(LANGUAGE_INSTRUCTIONS.keys()),
        "total":     len(LANGUAGE_INSTRUCTIONS),
    }
