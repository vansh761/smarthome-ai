from datetime import datetime, timedelta
from app.memory.pattern_detector import detect_pattern
from app.memory.emotion_store import get_memory_stats
from app.ai.emotion_model import EMOTION_ENVIRONMENT, EMOTION_PRIORITY

def detect_context_anomaly(
    user_id: str,
    current_emotion: str,
) -> dict:
    """
    Detect if user is in an unusual context:
    travel, sick, holiday, exam period etc.
    
    Signs of anomaly:
    - Emotion very different from usual pattern
    - Unusual time of day activity
    - Multiple consecutive unusual emotions
    """
    from app.memory.emotion_store import get_user_history
    history = get_user_history(user_id, limit=10)

    if len(history) < 3:
        return {"anomaly": False, "reason": "not enough history"}

    # Get last 3 emotions
    recent_emotions = [meta.get("emotion") for meta, _ in history[:3]]

    # Check if all recent emotions are the same unusual pattern
    if len(set(recent_emotions)) == 1 and recent_emotions[0] != current_emotion:
        return {
            "anomaly":       True,
            "type":          "sudden_change",
            "recent_pattern":recent_emotions[0],
            "current":       current_emotion,
            "action":        "pattern paused — sudden change detected",
        }

    # Check for sick pattern (tired + sad combination)
    if set(recent_emotions) <= {"tired", "sad", "neutral"}:
        return {
            "anomaly": True,
            "type":    "possible_sick_or_low",
            "action":  "gentle mode activated — patterns paused",
        }

    return {"anomaly": False}

def predict_and_prepare(
    user_id:          str,
    current_emotion:  str   = None,
    current_confidence: float = 0.0,
    room:             str   = "living_room",
    minutes_ahead:    int   = 30,
) -> dict:
    """
    3-layer decision system:
    Layer 1: Live emotion (highest priority)
    Layer 2: Pattern prediction (medium priority)
    Layer 3: Default environment (lowest priority)

    current_emotion = None means no live reading yet
    """
    now          = datetime.now()
    future_time  = now + timedelta(minutes=minutes_ahead)

    # ── Layer 2: Check pattern for current time ───────────────────────────
    pattern = detect_pattern(
        user_id     = user_id,
        day_of_week = now.weekday(),
        hour        = now.hour,
    )

    # ── Layer 1: Live emotion overrides everything ────────────────────────
    if current_emotion and current_confidence >= 50:

        live_env    = EMOTION_ENVIRONMENT.get(
            current_emotion, EMOTION_ENVIRONMENT["neutral"]
        )
        live_priority    = EMOTION_PRIORITY.get(current_emotion, 99)
        pattern_priority = EMOTION_PRIORITY.get(
            pattern.get("predicted_emotion","neutral"), 99
        ) if pattern.get("pattern_found") else 99

        # ── Smart decision: live vs pattern ───────────────────────────────
        # Rule 1: High confidence live emotion always wins
        if current_confidence >= 70:
            return {
                "decision":           "live_emotion_wins",
                "active_emotion":     current_emotion,
                "active_env":         live_env,
                "confidence":         current_confidence,
                "pattern_overridden": pattern.get("pattern_found", False),
                "explanation": (
                    f"Live emotion ({current_emotion}) detected with "
                    f"{current_confidence}% confidence — high confidence "
                    f"live reading always takes priority. "
                    f"Activating {current_emotion} environment."
                ),
                "pattern_info": pattern,
            }

        # Rule 2: Medium confidence live (50-69%)
        # Live wins if same or higher priority than pattern
        if live_priority <= pattern_priority:
            return {
                "decision":           "live_emotion_wins",
                "active_emotion":     current_emotion,
                "active_env":         live_env,
                "confidence":         current_confidence,
                "pattern_overridden": pattern.get("pattern_found", False),
                "explanation": (
                    f"Live emotion ({current_emotion}) wins — "
                    f"same or higher priority than pattern. "
                    f"Activating {current_emotion} environment."
                ),
                "pattern_info": pattern,
            }

        # Rule 3: Pattern has higher priority AND pattern stronger than live
        pattern_strength = pattern.get("pattern_strength", 0)
        if pattern_strength > current_confidence:
            return {
                "decision":       "pattern_priority_wins",
                "active_emotion": pattern["predicted_emotion"],
                "active_env":     pattern["recommended_env"],
                "confidence":     pattern_strength,
                "live_emotion":   current_emotion,
                "explanation": (
                    f"Pattern ({pattern['predicted_emotion']} at "
                    f"{pattern_strength}% strength) is more certain than "
                    f"live emotion ({current_emotion} at "
                    f"{current_confidence}% confidence). "
                    f"Monitoring — will switch if live emotion strengthens."
                ),
                "pattern_info": pattern,
            }

        # Rule 4: Live wins by default
        return {
            "decision":           "live_emotion_wins",
            "active_emotion":     current_emotion,
            "active_env":         live_env,
            "confidence":         current_confidence,
            "pattern_overridden": True,
            "explanation": (
                f"Live emotion ({current_emotion}, {current_confidence}%) "
                f"overrides pattern. Activating live environment."
            ),
            "pattern_info": pattern,
        }

    # ── No live emotion — use pattern if strong enough ────────────────────
    if pattern.get("pattern_found"):
        strength  = pattern["pattern_strength"]
        pred_em   = pattern["predicted_emotion"]
        pred_env  = pattern["recommended_env"]

        if strength >= 75:
            # Strong pattern → full activation
            return {
                "decision":       "pattern_full_activation",
                "active_emotion": pred_em,
                "active_env":     pred_env,
                "confidence":     strength,
                "explanation": (
                    f"Strong pattern detected: you are usually {pred_em} "
                    f"on {pattern['day']} at {pattern['hour']} "
                    f"({strength}% of the time). "
                    f"Activating {pred_em} environment."
                ),
                "pattern_info":   pattern,
            }

        elif strength >= 60:
            # Moderate pattern → gentle pre-warm (50% strength)
            gentle_env = {
                "temperature_c": pred_env["temperature_c"],
                "light_level":   round(pred_env["light_level"] * 0.5),
                "light_color":   pred_env["light_color"],
                "music":         "soft background ambient",
            }
            return {
                "decision":       "pattern_gentle_preparation",
                "active_emotion": pred_em,
                "active_env":     gentle_env,
                "full_env":       pred_env,
                "confidence":     strength,
                "explanation": (
                    f"Moderate pattern: you are often {pred_em} at this time "
                    f"({strength}% strength). "
                    f"Gently preparing environment. "
                    f"Will activate fully when confirmed."
                ),
                "pattern_info":   pattern,
            }

        else:
            # Weak pattern → prepare only, don't change environment
            return {
                "decision":       "pattern_standby",
                "active_emotion": "neutral",
                "active_env":     EMOTION_ENVIRONMENT["neutral"],
                "confidence":     strength,
                "explanation": (
                    f"Weak pattern ({strength}%) — monitoring but "
                    f"not acting yet. Staying neutral."
                ),
                "pattern_info":   pattern,
            }

    # ── No pattern and no live emotion → check memory stats ──────────────
    stats = get_memory_stats(user_id)
    return {
        "decision":       "no_pattern_yet",
        "active_emotion": "neutral",
        "active_env":     EMOTION_ENVIRONMENT["neutral"],
        "confidence":     0,
        "explanation":    (
            f"No pattern detected yet. {stats['learning_status']}. "
            f"Keep using the system and patterns will emerge."
        ),
        "memory_stats":   stats,
    }