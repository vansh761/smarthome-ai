from datetime import datetime, timedelta
from app.memory.emotion_store import get_pattern_events, get_user_history
from collections import Counter


EMOTION_PRIORITY = {
    "sleeping": 0, "anxious": 1, "stressed": 2,
    "angry":    3, "sad":     4, "tired":    5,
    "neutral":  6, "focused": 7, "happy":    8,
}


def get_decay_weight(event_timestamp: str) -> float:
    """
    Calculate weight of an event based on how old it is.
    Recent events matter more than old ones.
    
    Age        Weight
    0-7 days   1.0  (full weight)
    8-14 days  0.8
    15-30 days 0.5
    31-60 days 0.2
    60+ days   0.0  (ignored)
    """
    try:
        event_time = datetime.fromisoformat(event_timestamp)
    except:
        return 0.5  # unknown age → medium weight

    age_days = (datetime.now() - event_time).days

    if age_days <= 7:   return 1.0
    if age_days <= 14:  return 0.8
    if age_days <= 30:  return 0.5
    if age_days <= 60:  return 0.2
    return 0.0


def detect_pattern(
    user_id:     str,
    day_of_week: int = None,
    hour:        int = None,
) -> dict:
    """
    Detect recurring emotion pattern with adaptive decay.
    Recent events count more than old ones.
    """
    now          = datetime.now()
    day_of_week  = day_of_week if day_of_week is not None else now.weekday()
    hour         = hour        if hour        is not None else now.hour

    events = get_pattern_events(
        user_id     = user_id,
        day_of_week = day_of_week,
        hour        = hour,
        hour_range  = 1,
    )

    if len(events) < 3:
        return {
            "pattern_found":   False,
            "reason":          f"only {len(events)} events at this time — need 3+",
            "events_analyzed": len(events),
        }

    # ── Apply decay weights ───────────────────────────────────────────────
    weighted_scores = {}   # emotion → total weight
    total_weight    = 0.0
    active_events   = 0

    for event in events:
        timestamp = event.get("timestamp", "")
        weight    = get_decay_weight(timestamp)

        if weight == 0.0:
            continue  # too old — ignore completely

        emotion = event.get("emotion", "neutral")
        weighted_scores[emotion] = weighted_scores.get(emotion, 0.0) + weight
        total_weight  += weight
        active_events += 1

    if total_weight == 0 or active_events < 2:
        return {
            "pattern_found": False,
            "reason":        "all events too old — pattern has decayed",
            "events_analyzed": len(events),
            "decay_info":    "pattern expired, system will relearn",
        }

    # ── Find dominant emotion by weighted score ───────────────────────────
    top_emotion      = max(weighted_scores, key=weighted_scores.get)
    top_weight       = weighted_scores[top_emotion]
    pattern_strength = round((top_weight / total_weight) * 100, 1)

    if pattern_strength < 50:
        return {
            "pattern_found":   False,
            "reason":          "weighted emotions too varied — no clear pattern",
            "events_analyzed": active_events,
            "weighted_scores": {k: round(v, 2) for k, v in weighted_scores.items()},
            "decay_applied":   True,
        }

    # ── Best environment for this pattern ─────────────────────────────────
    matching_envs = []
    for event in events:
        if event.get("emotion") != top_emotion:
            continue
        weight = get_decay_weight(event.get("timestamp",""))
        if weight == 0:
            continue
        matching_envs.append({
            "temperature_c": event.get("temperature_c", 23),
            "light_level":   event.get("light_level",   60),
            "light_color":   event.get("light_color",   "neutral"),
            "music":         event.get("music",         "none"),
            "weight":        weight,
        })

    if not matching_envs:
        return {
            "pattern_found": False,
            "reason":        "no valid environments found after decay",
        }

    # Weighted average environment
    total_env_weight = sum(e["weight"] for e in matching_envs)
    avg_env = {
        "temperature_c": round(
            sum(e["temperature_c"] * e["weight"] for e in matching_envs)
            / total_env_weight, 1
        ),
        "light_level": round(
            sum(e["light_level"] * e["weight"] for e in matching_envs)
            / total_env_weight
        ),
        "light_color": Counter(
            e["light_color"] for e in matching_envs
        ).most_common(1)[0][0],
        "music": Counter(
            e["music"] for e in matching_envs
        ).most_common(1)[0][0],
    }

    day_names = [
        "Monday","Tuesday","Wednesday","Thursday",
        "Friday","Saturday","Sunday"
    ]

    # ── Decay summary ─────────────────────────────────────────────────────
    decay_summary = {
        "total_events":   len(events),
        "active_events":  active_events,
        "ignored_events": len(events) - active_events,
        "total_weight":   round(total_weight, 2),
        "decay_applied":  active_events < len(events),
    }

    return {
        "pattern_found":     True,
        "predicted_emotion": top_emotion,
        "pattern_strength":  pattern_strength,
        "events_analyzed":   active_events,
        "top_weight":        round(top_weight, 2),
        "day":               day_names[day_of_week],
        "hour":              f"{hour:02d}:00",
        "weighted_scores":   {k: round(v, 2) for k, v in weighted_scores.items()},
        "recommended_env":   avg_env,
        "confidence_label": (
            "strong"   if pattern_strength >= 75 else
            "moderate" if pattern_strength >= 60 else
            "weak"
        ),
        "decay_info":        decay_summary,
    }


def get_full_weekly_pattern(user_id: str) -> dict:
    """Get emotion patterns for all days with decay applied."""
    history = get_user_history(user_id, limit=200)

    if len(history) < 5:
        return {
            "status":  "not enough data",
            "message": f"need 5+ events, have {len(history)}"
        }

    day_names = [
        "Monday","Tuesday","Wednesday",
        "Thursday","Friday","Saturday","Sunday"
    ]
    patterns = {}

    for day_idx, day_name in enumerate(day_names):
        day_events = [
            meta for meta, _ in history
            if meta.get("day_of_week") == day_idx
        ]
        if not day_events:
            continue

        # Apply decay
        weighted = {}
        for e in day_events:
            weight  = get_decay_weight(e.get("timestamp",""))
            emotion = e.get("emotion","neutral")
            weighted[emotion] = weighted.get(emotion, 0.0) + weight

        if not weighted:
            continue

        total_w  = sum(weighted.values())
        top_em   = max(weighted, key=weighted.get)
        strength = round((weighted[top_em] / total_w) * 100, 1)

        patterns[day_name] = {
            "dominant_emotion": top_em,
            "pattern_strength": strength,
            "total_events":     len(day_events),
            "weighted_scores":  {k: round(v, 2) for k, v in weighted.items()},
        }

    return {
        "status":          "ready",
        "total_events":    len(history),
        "weekly_patterns": patterns,
        "decay_note":      "events older than 60 days are ignored",
    }