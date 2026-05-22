from datetime import datetime
from app.memory.emotion_store import save_emotion_event, get_memory_stats

# ── Lifestyle templates ────────────────────────────────────────────────────
LIFESTYLE_TEMPLATES = {
    "student": {
        "label":       "Student",
        "description": "College/school student with exams, assignments, late nights",
        "schedule": [
            # (day_of_week, hour, emotion, confidence)
            # Weekday mornings — focused for class
            (0, 9,  "focused",  75),
            (1, 9,  "focused",  75),
            (2, 9,  "focused",  75),
            (3, 9,  "focused",  75),
            (4, 9,  "focused",  75),
            # Weekday evenings — stressed from assignments
            (0, 20, "stressed", 70),
            (1, 20, "stressed", 70),
            (2, 20, "stressed", 70),
            (3, 20, "stressed", 70),
            # Weekend afternoons — happy/relaxed
            (5, 14, "happy",    70),
            (6, 14, "happy",    70),
            # Late nights — tired
            (0, 23, "tired",    75),
            (1, 23, "tired",    75),
            (4, 23, "tired",    75),
        ],
        "default_env": {
            "morning":   {"temperature_c": 22, "light_level": 85, "light_color": "cool",    "music": "focus music"},
            "afternoon": {"temperature_c": 23, "light_level": 70, "light_color": "neutral", "music": "background ambient"},
            "evening":   {"temperature_c": 22, "light_level": 40, "light_color": "warm",    "music": "lo-fi / calm instrumental"},
            "night":     {"temperature_c": 21, "light_level": 20, "light_color": "warm",    "music": "soft ambient"},
        }
    },

    "working_professional": {
        "label":       "Working Professional",
        "description": "9-to-5 job, meetings, deadlines, work from home or office",
        "schedule": [
            # Weekday mornings — focused/stressed
            (0, 9,  "focused",  75),
            (1, 9,  "focused",  75),
            (2, 9,  "focused",  75),
            (3, 9,  "focused",  75),
            (4, 9,  "focused",  75),
            # Weekday afternoons — stressed
            (0, 14, "stressed", 70),
            (1, 14, "stressed", 70),
            (2, 14, "stressed", 70),
            (3, 14, "stressed", 70),
            # Friday evening — happy
            (4, 18, "happy",    75),
            # Weekday evenings — tired
            (0, 19, "tired",    70),
            (1, 19, "tired",    70),
            (2, 19, "tired",    70),
            (3, 19, "tired",    70),
            # Weekend — happy and relaxed
            (5, 11, "happy",    75),
            (6, 11, "happy",    75),
            (5, 15, "happy",    70),
            (6, 15, "happy",    70),
        ],
        "default_env": {
            "morning":   {"temperature_c": 21, "light_level": 90, "light_color": "cool",    "music": "focus music / white noise"},
            "afternoon": {"temperature_c": 22, "light_level": 80, "light_color": "cool",    "music": "background ambient"},
            "evening":   {"temperature_c": 23, "light_level": 40, "light_color": "warm",    "music": "soft ambient / nature sounds"},
            "night":     {"temperature_c": 20, "light_level": 10, "light_color": "warm",    "music": "silence / white noise"},
        }
    },

    "night_owl": {
        "label":       "Night Owl",
        "description": "Active late at night, sleeps late, works or creates after midnight",
        "schedule": [
            # Late mornings — tired
            (0, 10, "tired",    75),
            (1, 10, "tired",    75),
            (2, 10, "tired",    75),
            # Afternoons — neutral/focused
            (0, 14, "focused",  70),
            (1, 14, "focused",  70),
            (2, 14, "focused",  70),
            # Evenings — happy/energetic
            (0, 20, "happy",    70),
            (1, 20, "happy",    70),
            (2, 20, "happy",    70),
            # Late nights — focused (peak hours)
            (0, 23, "focused",  75),
            (1, 23, "focused",  75),
            (2, 23, "focused",  75),
            (4, 23, "focused",  75),
            (5, 23, "focused",  75),
        ],
        "default_env": {
            "morning":   {"temperature_c": 23, "light_level": 30, "light_color": "warm",    "music": "soft ambient"},
            "afternoon": {"temperature_c": 22, "light_level": 60, "light_color": "neutral", "music": "background ambient"},
            "evening":   {"temperature_c": 22, "light_level": 70, "light_color": "neutral", "music": "upbeat / energetic"},
            "night":     {"temperature_c": 21, "light_level": 80, "light_color": "cool",    "music": "focus music / white noise"},
        }
    },

    "homemaker": {
        "label":       "Homemaker",
        "description": "Manages household, cooking, family, flexible schedule",
        "schedule": [
            # Morning — focused/busy
            (0, 8,  "focused",  70),
            (1, 8,  "focused",  70),
            (2, 8,  "focused",  70),
            (3, 8,  "focused",  70),
            (4, 8,  "focused",  70),
            # Midday — neutral/happy
            (0, 12, "happy",    70),
            (1, 12, "happy",    70),
            (2, 12, "happy",    70),
            # Afternoons — tired
            (0, 15, "tired",    70),
            (1, 15, "tired",    70),
            (2, 15, "tired",    70),
            # Evenings — happy (family time)
            (0, 19, "happy",    72),
            (1, 19, "happy",    72),
            (4, 19, "happy",    72),
            (5, 19, "happy",    75),
            (6, 19, "happy",    75),
        ],
        "default_env": {
            "morning":   {"temperature_c": 23, "light_level": 80, "light_color": "neutral", "music": "background ambient"},
            "afternoon": {"temperature_c": 24, "light_level": 60, "light_color": "neutral", "music": "soft ambient"},
            "evening":   {"temperature_c": 23, "light_level": 70, "light_color": "warm",    "music": "upbeat / energetic"},
            "night":     {"temperature_c": 21, "light_level": 10, "light_color": "warm",    "music": "silence / white noise"},
        }
    },

    "retired": {
        "label":       "Retired",
        "description": "Relaxed schedule, leisure activities, early to bed",
        "schedule": [
            # Mornings — happy
            (0, 7,  "happy",    72),
            (1, 7,  "happy",    72),
            (2, 7,  "happy",    72),
            (3, 7,  "happy",    72),
            (4, 7,  "happy",    72),
            (5, 7,  "happy",    72),
            (6, 7,  "happy",    72),
            # Afternoons — focused (reading, hobbies)
            (0, 14, "focused",  70),
            (1, 14, "focused",  70),
            (2, 14, "focused",  70),
            # Evenings — tired
            (0, 18, "tired",    70),
            (1, 18, "tired",    70),
            (2, 18, "tired",    70),
            (3, 18, "tired",    70),
            (4, 18, "tired",    70),
        ],
        "default_env": {
            "morning":   {"temperature_c": 23, "light_level": 75, "light_color": "neutral", "music": "background ambient"},
            "afternoon": {"temperature_c": 24, "light_level": 65, "light_color": "neutral", "music": "soft ambient"},
            "evening":   {"temperature_c": 22, "light_level": 35, "light_color": "warm",    "music": "soft comforting music"},
            "night":     {"temperature_c": 20, "light_level": 0,  "light_color": "warm",    "music": "silence / white noise"},
        }
    },
}


def apply_cold_start(user_id: str, template_key: str) -> dict:
    """
    Apply a lifestyle template for a new user.
    Seeds the memory with template events so system
    works from day 1 without real data.
    """
    if template_key not in LIFESTYLE_TEMPLATES:
        return {
            "success": False,
            "error":   f"Unknown template. Choose from: {list(LIFESTYLE_TEMPLATES.keys())}"
        }

    template  = LIFESTYLE_TEMPLATES[template_key]
    stats     = get_memory_stats(user_id)

    # Don't overwrite if user already has real data (10+ events)
    if stats["total_events"] >= 10:
        return {
            "success":  False,
            "error":    "User already has enough real data — cold start not needed.",
            "events":   stats["total_events"],
        }

    saved_count = 0
    now         = datetime.now()

    for day_of_week, hour, emotion, confidence in template["schedule"]:
        # Get time-of-day for environment selection
        if 5 <= hour < 12:   tod = "morning"
        elif 12 <= hour < 17: tod = "afternoon"
        elif 17 <= hour < 21: tod = "evening"
        else:                  tod = "night"

        env = template["default_env"][tod]

        # Create a backdated timestamp for this template event
        # So decay doesn't immediately kill it
        days_back = (now.weekday() - day_of_week) % 7
        if days_back == 0:
            days_back = 7
        event_time = now.replace(hour=hour, minute=0, second=0) - \
                     __import__('datetime').timedelta(days=days_back + 3)

        result = save_emotion_event(
            user_id    = user_id,
            emotion    = emotion,
            confidence = confidence,
            text       = f"cold_start_template:{template_key}",
            language   = "template",
            environment= env,
            room       = "home",
        )
        saved_count += 1

    return {
        "success":        True,
        "template":       template["label"],
        "description":    template["description"],
        "events_seeded":  saved_count,
        "message": (
            f"Cold start complete! System is ready with {template['label']} "
            f"defaults. As you use the system, real data will gradually "
            f"replace these templates over 7-14 days."
        ),
        "next_step":      "Use /memory/analyze-and-remember to start building real patterns",
    }


def get_available_templates() -> dict:
    """List all available lifestyle templates."""
    return {
        key: {
            "label":       t["label"],
            "description": t["description"],
            "events":      len(t["schedule"]),
        }
        for key, t in LIFESTYLE_TEMPLATES.items()
    }