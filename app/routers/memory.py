from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.memory.pattern_detector import detect_pattern, get_full_weekly_pattern
from app.memory.predictor import predict_and_prepare
from app.ai.emotion_model import analyze_emotion, EMOTION_ENVIRONMENT
from app.memory.emotion_store import (
    save_emotion_event, get_user_history, get_memory_stats,
    save_feedback, get_feedback_history, get_correction_accuracy
)
from app.memory.cold_start import apply_cold_start, get_available_templates

router = APIRouter(prefix="/memory", tags=["Emotional Memory"])


class EmotionMemoryRequest(BaseModel):
    user_id:    str
    text:       str
    room:       Optional[str] = "living_room"
    time_of_day:Optional[str] = None


class PredictRequest(BaseModel):
    user_id:             str
    current_emotion:     Optional[str]   = None
    current_confidence:  Optional[float] = 0.0
    room:                Optional[str]   = "living_room"

class FeedbackRequest(BaseModel):
    user_id:           str
    event_id:          str
    original_emotion:  str
    corrected_emotion: str
    corrected_env:     Optional[dict] = None

class ColdStartRequest(BaseModel):
    user_id:      str
    template_key: str


@router.post("/analyze-and-remember")
def analyze_and_remember(req: EmotionMemoryRequest):
    """
    Analyze emotion AND save it to long-term memory.
    This is the main endpoint — replaces /emotion/analyze for Phase 3.
    """
    # Step 1: Detect emotion
    result = analyze_emotion(
        text        = req.text,
        time_of_day = req.time_of_day,
        user_id     = req.user_id,
    )

    # Step 2: Save to memory
    env    = result.get("environment_suggestion", {})
    saved  = save_emotion_event(
        user_id    = req.user_id,
        emotion    = result["detected_emotion"],
        confidence = result["confidence"],
        text       = req.text,
        language   = result["language_detected"],
        environment= env,
        room       = req.room,
    )

    # Step 3: Check if a pattern is already forming
    pattern = detect_pattern(req.user_id)

    # Step 4: Get memory stats
    stats   = get_memory_stats(req.user_id)

    return {
        "emotion_result":  result,
        "memory_saved":    saved["saved"],
        "event_id":        saved["event_id"],
        "pattern_forming": pattern,
        "memory_stats":    stats,
    }


@router.post("/predict")
def predict(req: PredictRequest):
    """
    Predict environment based on patterns + live emotion.
    3-layer decision: live emotion > pattern > default.
    """
    return predict_and_prepare(
        user_id           = req.user_id,
        current_emotion   = req.current_emotion,
        current_confidence= req.current_confidence or 0.0,
        room              = req.room or "living_room",
    )


@router.get("/history/{user_id}")
def get_history(user_id: str, limit: int = 20):
    """Get emotion history for a user."""
    history = get_user_history(user_id, limit)
    return {
        "user_id": user_id,
        "count":   len(history),
        "events": [
            {
                "emotion":   m.get("emotion"),
                "confidence":m.get("confidence"),
                "day":       m.get("day_name"),
                "time":      m.get("time"),
                "room":      m.get("room"),
                "language":  m.get("language"),
            }
            for m, _ in history
        ]
    }


@router.get("/pattern/{user_id}")
def get_pattern(user_id: str):
    """Get current time pattern for a user."""
    return detect_pattern(user_id)


@router.get("/weekly-pattern/{user_id}")
def weekly_pattern(user_id: str):
    """Get full weekly emotion pattern for a user."""
    return get_full_weekly_pattern(user_id)


@router.get("/stats/{user_id}")
def memory_stats(user_id: str):
    """Get memory statistics for a user."""
    return get_memory_stats(user_id)


@router.delete("/clear/{user_id}")
def clear_memory(user_id: str):
    """Clear all memory for a user (incognito mode)."""
    from app.memory.emotion_store import get_collection
    collection = get_collection()
    results    = collection.get(
        where   = {"user_id": user_id},
        include = ["metadatas"],
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
    return {
        "cleared":     True,
        "user_id":     user_id,
        "events_deleted": len(results["ids"])
    }

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """
    User says 'this was wrong — I was actually X not Y'.
    System saves correction and learns from it.
    """
    from app.ai.emotion_model import EMOTION_ENVIRONMENT

    # Get the correct environment for the corrected emotion
    corrected_env = req.corrected_env or EMOTION_ENVIRONMENT.get(
        req.corrected_emotion,
        EMOTION_ENVIRONMENT["neutral"]
    )

    # Save feedback as a positive event for the corrected emotion
    # This directly improves future pattern detection
    save_result = save_feedback(
        user_id           = req.user_id,
        event_id          = req.event_id,
        original_emotion  = req.original_emotion,
        corrected_emotion = req.corrected_emotion,
        original_env      = EMOTION_ENVIRONMENT.get(
            req.original_emotion,
            EMOTION_ENVIRONMENT["neutral"]
        ),
        corrected_env     = corrected_env,
    )

    # Also save as a real emotion event so it affects future patterns
    now = datetime.now()
    save_emotion_event(
        user_id     = req.user_id,
        emotion     = req.corrected_emotion,
        confidence  = 100.0,   # user confirmed = 100% confidence
        text        = f"user_correction: was {req.original_emotion}",
        language    = "correction",
        environment = corrected_env,
        room        = "unknown",
    )

    # Get updated pattern after correction
    updated_pattern = detect_pattern(req.user_id)
    accuracy        = get_correction_accuracy(req.user_id)

    return {
        "feedback_saved":    save_result["feedback_saved"],
        "correction":        save_result["correction"],
        "message":           (
            f"Got it! System was wrong about {req.original_emotion}. "
            f"Saved {req.corrected_emotion} as correct. "
            f"This will improve future predictions."
        ),
        "updated_pattern":   updated_pattern,
        "system_accuracy":   accuracy,
    }


@router.get("/feedback/history/{user_id}")
def feedback_history(user_id: str):
    """Get all corrections made by a user."""
    feedbacks = get_feedback_history(user_id)
    return {
        "user_id":    user_id,
        "count":      len(feedbacks),
        "corrections": [
            {
                "original":   f.get("original_emotion"),
                "corrected":  f.get("corrected_emotion"),
                "day":        f.get("day_name"),
                "timestamp":  f.get("timestamp"),
            }
            for f in feedbacks
        ]
    }


@router.get("/accuracy/{user_id}")
def system_accuracy(user_id: str):
    """How accurate has the system been for this user."""
    return get_correction_accuracy(user_id)

@router.get("/templates")
def list_templates():
    """List all available lifestyle templates for new users."""
    return get_available_templates()


@router.post("/cold-start")
def cold_start(req: ColdStartRequest):
    """
    Apply a lifestyle template for a new user.
    Seeds memory so system works from day 1.
    """
    return apply_cold_start(req.user_id, req.template_key)

