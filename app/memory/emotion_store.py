import chromadb
from chromadb.config import Settings
from datetime import datetime
from pathlib import Path
import json

# ── ChromaDB setup — stored locally, no cloud ─────────────────────────────
DB_PATH = str(Path("memory_db").absolute())

_client     = None
_collection = None

def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=DB_PATH)
    return _client

def get_collection():
    global _collection
    if _collection is None:
        client      = get_client()
        _collection = client.get_or_create_collection(
            name     = "emotion_memory",
            metadata = {"description": "User emotional state history"}
        )
    return _collection


# ── Save an emotion event ─────────────────────────────────────────────────
def save_emotion_event(
    user_id:     str,
    emotion:     str,
    confidence:  float,
    text:        str,
    language:    str,
    environment: dict,
    room:        str = "living_room",
) -> dict:
    """Save one emotion event to long-term memory."""
    collection = get_collection()
    now        = datetime.now()

    # Unique ID for this event
    event_id = f"{user_id}_{now.strftime('%Y%m%d_%H%M%S_%f')}"

    # Metadata — what we store about this event
    metadata = {
        "user_id":        user_id,
        "emotion":        emotion,
        "confidence":     confidence,
        "language":       language,
        "room":           room,
        "hour":           now.hour,
        "day_of_week":    now.weekday(),       # 0=Monday, 6=Sunday
        "day_name":       now.strftime("%A"),
        "date":           now.strftime("%Y-%m-%d"),
        "time":           now.strftime("%H:%M"),
        "month":          now.month,
        "is_weekend":     int(now.weekday() >= 5),
        "temperature_c":  environment.get("temperature_c", 23),
        "light_level":    environment.get("light_level", 60),
        "light_color":    environment.get("light_color", "neutral"),
        "music":          environment.get("music", "none"),
        "timestamp":      now.isoformat(),
    }

    # Document = text that describes this event (used for semantic search)
    document = (
        f"User {user_id} felt {emotion} on {metadata['day_name']} "
        f"at {metadata['time']} in {room}. "
        f"Said: {text[:100] if text else 'no text'}. "
        f"Environment: {environment.get('light_color')} light, "
        f"{environment.get('temperature_c')}C, "
        f"music: {environment.get('music', 'none')}."
    )

    collection.add(
        ids        = [event_id],
        documents  = [document],
        metadatas  = [metadata],
    )

    return {"saved": True, "event_id": event_id, "metadata": metadata}


# ── Get emotion history for a user ────────────────────────────────────────
def get_user_history(
    user_id: str,
    limit:   int = 50
) -> list:
    """Get recent emotion history for a user."""
    collection = get_collection()
    results    = collection.get(
        where          = {"user_id": {"$eq": user_id}},
        include        = ["metadatas", "documents"],
    )
    if not results["metadatas"]:
        return []

    # Sort by timestamp descending
    events = list(zip(results["metadatas"], results["documents"]))
    events.sort(key=lambda x: x[0].get("timestamp",""), reverse=True)
    return events[:limit]


# ── Get events for specific time pattern ──────────────────────────────────
def get_pattern_events(
    user_id:     str,
    day_of_week: int,
    hour:        int,
    hour_range:  int = 2,
) -> list:
    """
    Get all events for a user at a specific day + time window.
    e.g. Monday (0) at 9 PM (21) ± 2 hours
    """
    collection = get_collection()
    results    = collection.get(
        where   = {"user_id": {"$eq": user_id}},
        include = ["metadatas"],
    )
    if not results["metadatas"]:
        return []

    # Filter by day and hour range
    matching = []
    for meta in results["metadatas"]:
        if meta.get("day_of_week") != day_of_week:
            continue
        event_hour = meta.get("hour", 0)
        if abs(event_hour - hour) <= hour_range:
            matching.append(meta)

    return matching


# ── Get memory stats ──────────────────────────────────────────────────────
def get_memory_stats(user_id: str) -> dict:
    """How much has the system learned about this user."""
    collection = get_collection()
    results    = collection.get(
        where   = {"user_id": {"$eq": user_id}},
        include = ["metadatas"],
    )
    if not results["metadatas"]:
        return {
            "total_events":     0,
            "learning_status":  "cold start — no data yet",
            "days_tracked":     0,
            "most_common_emotion": None,
        }

    metas  = results["metadatas"]
    total  = len(metas)
    dates  = set(m.get("date","") for m in metas)
    emotions = [m.get("emotion","") for m in metas]
    most_common = max(set(emotions), key=emotions.count)

    if total < 10:
        status = f"learning — {total} events recorded, need 10+ for patterns"
    elif total < 30:
        status = "building patterns — getting smarter"
    else:
        status = "mature — strong pattern recognition active"

    return {
        "total_events":        total,
        "days_tracked":        len(dates),
        "most_common_emotion": most_common,
        "learning_status":     status,
        "emotions_breakdown":  {
            e: emotions.count(e)
            for e in set(emotions)
        }
    }

def save_feedback(
    user_id:          str,
    event_id:         str,
    original_emotion: str,
    corrected_emotion: str,
    original_env:     dict,
    corrected_env:    dict = None,
) -> dict:
    """
    Save user correction.
    When user says 'this was wrong', we store what was correct.
    """
    collection = get_collection()
    now        = datetime.now()
    feedback_id = f"feedback_{user_id}_{now.strftime('%Y%m%d_%H%M%S_%f')}"

    metadata = {
        "user_id":           user_id,
        "type":              "feedback",
        "event_id":          event_id,
        "original_emotion":  original_emotion,
        "corrected_emotion": corrected_emotion,
        "timestamp":         now.isoformat(),
        "hour":              now.hour,
        "day_of_week":       now.weekday(),
        "day_name":          now.strftime("%A"),
        "temperature_c":     corrected_env.get("temperature_c", 23) if corrected_env else original_env.get("temperature_c", 23),
        "light_level":       corrected_env.get("light_level", 60)   if corrected_env else original_env.get("light_level", 60),
        "light_color":       corrected_env.get("light_color","neutral") if corrected_env else original_env.get("light_color","neutral"),
        "music":             corrected_env.get("music","none")       if corrected_env else original_env.get("music","none"),
        "emotion":           corrected_emotion,
    }

    document = (
        f"User {user_id} corrected {original_emotion} to "
        f"{corrected_emotion} on {metadata['day_name']} "
        f"at {now.strftime('%H:%M')}."
    )

    collection.add(
        ids       = [feedback_id],
        documents = [document],
        metadatas = [metadata],
    )

    return {
        "feedback_saved": True,
        "feedback_id":    feedback_id,
        "correction":     f"{original_emotion} → {corrected_emotion}",
    }


def get_feedback_history(user_id: str) -> list:
    """Get all feedback corrections for a user."""
    collection = get_collection()
    results    = collection.get(
        where   = {
            "$and": [
                {"user_id": {"$eq": user_id}},
                {"type":    {"$eq": "feedback"}},
            ]
        },
        include = ["metadatas"],
    )
    if not results["metadatas"]:
        return []
    return sorted(
        results["metadatas"],
        key=lambda x: x.get("timestamp",""),
        reverse=True
    )


def get_correction_accuracy(user_id: str) -> dict:
    collection = get_collection()

    # Total emotion events
    all_events = collection.get(
        where   = {"user_id": {"$eq": user_id}},
        include = ["metadatas"],
    )
    total = len([
        m for m in all_events["metadatas"]
        if m.get("type") != "feedback"
    ])

    # Feedback events
    feedbacks = get_feedback_history(user_id)
    corrections = len(feedbacks)

    if total == 0:
        return {"accuracy": 0, "total": 0, "corrections": 0}

    accuracy = round(((total - corrections) / total) * 100, 1)

    # Most common correction
    if feedbacks:
        from collections import Counter
        corrections_list = [
            f"{f['original_emotion']}→{f['corrected_emotion']}"
            for f in feedbacks
        ]
        most_common = Counter(corrections_list).most_common(1)[0][0]
    else:
        most_common = None

    return {
        "accuracy":            accuracy,
        "total_detections":    total,
        "total_corrections":   corrections,
        "correction_rate":     round((corrections / total) * 100, 1),
        "most_common_mistake": most_common,
        "grade": (
            "Excellent" if accuracy >= 90 else
            "Good"      if accuracy >= 75 else
            "Learning"  if accuracy >= 60 else
            "Needs improvement"
        )
    }