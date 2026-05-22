import numpy as np
from datetime import datetime, time


# ── Optimal sleep environment constants ───────────────────────────────────
OPTIMAL = {
    "temperature_c": 20.0,    # research: 18–22°C is ideal for sleep
    "noise_db":      30.0,    # library = 40dB, bedroom target = 30dB
    "light_level":   0,       # complete darkness is best
    "sleep_hour":    22,      # ideal sleep time (10 PM)
    "wake_hour":     6,       # ideal wake time (6 AM)
    "sleep_duration": 8,      # ideal hours
}

# Health condition environment adjustments
HEALTH_ADJUSTMENTS = {
    # ── Blood Pressure ─────────────────────────────────────────────────
    "high_bp": {
        "temperature_c": 20.0,
        "light_color":   "warm",
        "noise_db":      25.0,
        "tip": "Cool room (19–21°C) and complete darkness help reduce blood pressure naturally. Avoid stimulating sounds before sleep."
    },
    "low_bp": {
        "temperature_c": 22.0,
        "light_color":   "warm",
        "noise_db":      30.0,
        "tip": "Slightly warmer room (21–23°C) recommended. Avoid sudden standing from bed. Keep room well-lit in the morning."
    },

    # ── Blood Sugar ────────────────────────────────────────────────────
    "high_sugar": {
        "temperature_c": 19.0,
        "light_color":   "warm",
        "noise_db":      25.0,
        "tip": "Cooler room (18–20°C) supports better glucose regulation overnight. Avoid bright light after 9 PM — it disrupts insulin sensitivity. Aim to sleep by 10 PM."
    },
    "low_sugar": {
        "temperature_c": 22.0,
        "light_color":   "warm",
        "noise_db":      30.0,
        "tip": "Slightly warmer environment recommended. Keep a light snack nearby. Avoid very cold rooms which can mask hypoglycemia symptoms during sleep."
    },
    "diabetes": {
        "temperature_c": 19.0,
        "light_color":   "warm",
        "noise_db":      30.0,
        "tip": "Cooler sleep temperature (17–20°C) may improve insulin sensitivity overnight. Maintain consistent sleep schedule — irregular sleep worsens blood sugar control."
    },

    # ── Haemoglobin ────────────────────────────────────────────────────
    "low_haemoglobin": {
        "temperature_c": 23.0,
        "light_color":   "warm",
        "noise_db":      30.0,
        "tip": "Warmer room (22–24°C) helps compensate for poor circulation from low haemoglobin. Bright natural light in the morning (6–8 AM) supports energy recovery. Avoid very cold environments."
    },
    "anaemia": {
        "temperature_c": 23.0,
        "light_color":   "warm",
        "noise_db":      30.0,
        "tip": "Warm comfortable environment (22–24°C) recommended. Morning bright light exposure helps improve alertness when haemoglobin is low. Extra rest recommended."
    },
    "high_haemoglobin": {
        "temperature_c": 19.0,
        "light_color":   "cool",
        "noise_db":      30.0,
        "tip": "Cooler room with good ventilation recommended. Avoid overheating. Keep room temperature 18–21°C. Stay well hydrated — dehydration thickens blood further."
    },

    # ── Heart Rate ─────────────────────────────────────────────────────
    "high_heart_rate": {
        "temperature_c": 20.0,
        "light_color":   "warm",
        "noise_db":      20.0,
        "tip": "Cool, dark, and very quiet environment helps reduce elevated heart rate. Dim warm lights 30 minutes before sleep. Avoid stimulating music or sudden loud sounds. Temperature 19–21°C optimal."
    },
    "tachycardia": {
        "temperature_c": 20.0,
        "light_color":   "warm",
        "noise_db":      20.0,
        "tip": "Complete quiet and dim warm lighting recommended. Cool room (19–21°C) helps calm elevated heart rate. Avoid screens and stimulating content before sleep."
    },
    "low_heart_rate": {
        "temperature_c": 22.0,
        "light_color":   "neutral",
        "noise_db":      35.0,
        "tip": "Moderate temperature (21–23°C) recommended. Bright morning light (7–9 AM) helps stimulate heart rate naturally on waking. Avoid very cold rooms."
    },
    "bradycardia": {
        "temperature_c": 22.0,
        "light_color":   "neutral",
        "noise_db":      35.0,
        "tip": "Avoid very cold environments which can slow heart rate further. Bright morning light and gentle ambient sounds support natural arousal on waking."
    },

    # ── Existing conditions ────────────────────────────────────────────
    "anxiety": {
        "temperature_c": 20.0,
        "light_color":   "warm",
        "noise_db":      25.0,
        "tip": "Cool, dark, quiet environment significantly reduces anxiety before sleep. Binaural beats or nature sounds at low volume can help calm the nervous system."
    },
    "insomnia": {
        "temperature_c": 19.0,
        "light_color":   "warm",
        "noise_db":      25.0,
        "tip": "Consistent schedule and dark cool room are most effective for insomnia. Keep room for sleep only — avoid screens, work, or eating in bed."
    },
    "asthma": {
        "temperature_c": 21.0,
        "light_color":   "neutral",
        "noise_db":      30.0,
        "tip": "Maintain 40–50% humidity. Avoid AC direct airflow onto face. Keep room dust-free and well-ventilated. Temperature 20–22°C is ideal."
    },

    # ── New conditions ─────────────────────────────────────────────────
    "migraine": {
        "temperature_c": 18.0,
        "light_color":   "warm",
        "noise_db":      15.0,
        "tip": "Complete darkness is essential during migraine. Keep room very cool (17–19°C). Absolute silence — even low sounds can worsen pain. Blackout curtains recommended. No blue or bright light."
    },
    "arthritis": {
        "temperature_c": 23.0,
        "light_color":   "warm",
        "noise_db":      30.0,
        "tip": "Warm room (22–24°C) reduces joint stiffness. Avoid cold drafts directly on joints. Maintain humidity 45–55%. Avoid cold floors — use warm bedding."
    },
    "thyroid_hypo": {
        "temperature_c": 23.0,
        "light_color":   "neutral",
        "noise_db":      30.0,
        "tip": "Hypothyroidism causes sensitivity to cold — keep room warm (22–24°C). Morning bright light therapy (10–15 minutes, 6–8 AM) helps stimulate energy and mood. Consistent sleep schedule critical."
    },
    "thyroid_hyper": {
        "temperature_c": 19.0,
        "light_color":   "warm",
        "noise_db":      20.0,
        "tip": "Hyperthyroidism raises body temperature — keep room cool (18–21°C). Very calm, quiet, dark environment helps reduce overstimulation. Avoid caffeine and stimulating sounds completely."
    },
    "pcod": {
        "temperature_c": 20.0,
        "light_color":   "warm",
        "noise_db":      25.0,
        "tip": "Stress management through environment is important for PCOD. Cool, calm, dark room supports hormonal balance. Consistent sleep-wake schedule is critical — irregular sleep worsens PCOD symptoms."
    },
    "pcos": {
        "temperature_c": 20.0,
        "light_color":   "warm",
        "noise_db":      25.0,
        "tip": "Same as PCOD — calm, cool, dark environment. Consistent 7–9 hours of sleep is one of the most effective lifestyle interventions for PCOS management."
    },
}


def predict_sleep_quality(
    temperature_c:  float,
    noise_db:       float,
    light_level:    int,
    sleep_hour:     int,
    wake_hour:      int,
    light_color:    str   = "warm",
    health_conditions: list = []
) -> dict:

    # ── 1. Temperature score (0–100) ──────────────────────────────────────
    temp_diff    = abs(temperature_c - OPTIMAL["temperature_c"])
    temp_score   = max(0, 100 - (temp_diff * 8))

    # ── 2. Noise score ────────────────────────────────────────────────────
    noise_diff   = max(0, noise_db - OPTIMAL["noise_db"])
    noise_score  = max(0, 100 - (noise_diff * 3))

    # ── 3. Light score ────────────────────────────────────────────────────
    light_score  = max(0, 100 - (light_level * 1.5))

    # ── 4. Sleep duration score ───────────────────────────────────────────
    if wake_hour > sleep_hour:
        duration = wake_hour - sleep_hour
    else:
        duration = (24 - sleep_hour) + wake_hour   # crosses midnight

    duration_diff  = abs(duration - OPTIMAL["sleep_duration"])
    duration_score = max(0, 100 - (duration_diff * 12))

    # ── 5. Sleep timing score (circadian rhythm) ──────────────────────────
    sleep_diff  = abs(sleep_hour - OPTIMAL["sleep_hour"])
    if sleep_diff > 12:
        sleep_diff = 24 - sleep_diff
    timing_score = max(0, 100 - (sleep_diff * 8))

    # ── 6. Light color bonus ──────────────────────────────────────────────
    color_bonus = 10 if light_color == "warm" else 0

    # ── Weighted final score ──────────────────────────────────────────────
    sleep_score = (
        temp_score     * 0.30 +
        noise_score    * 0.25 +
        light_score    * 0.20 +
        duration_score * 0.15 +
        timing_score   * 0.10 +
        color_bonus
    )
    sleep_score = round(min(100, max(0, sleep_score)), 1)

    # ── Quality label ─────────────────────────────────────────────────────
    if sleep_score >= 85:
        quality = "Excellent"
    elif sleep_score >= 70:
        quality = "Good"
    elif sleep_score >= 50:
        quality = "Fair"
    else:
        quality = "Poor"

    # ── Recommendations ───────────────────────────────────────────────────
    recommendations = []

    if temp_score < 70:
        direction = "lower" if temperature_c > OPTIMAL["temperature_c"] else "raise"
        recommendations.append({
            "issue":      "Temperature not optimal for sleep",
            "current":    f"{temperature_c}°C",
            "target":     f"{OPTIMAL['temperature_c']}°C",
            "action":     f"{direction.capitalize()} room temperature to 20°C",
            "impact":     "high"
        })

    if noise_score < 70:
        recommendations.append({
            "issue":   "Room is too noisy",
            "current": f"{noise_db} dB",
            "target":  f"{OPTIMAL['noise_db']} dB",
            "action":  "Close windows, use fan white noise, or earplugs",
            "impact":  "high"
        })

    if light_score < 70:
        recommendations.append({
            "issue":   "Too much light in room",
            "current": f"Light level {light_level}%",
            "target":  "0% (complete darkness)",
            "action":  "Use blackout curtains or eye mask",
            "impact":  "medium"
        })

    if duration_score < 70:
        if duration < 7:
            recommendations.append({
                "issue":   "Not enough sleep",
                "current": f"{duration} hours",
                "target":  "8 hours",
                "action":  f"Sleep {8 - duration} hour(s) earlier or wake up later",
                "impact":  "high"
            })
        else:
            recommendations.append({
                "issue":   "Oversleeping detected",
                "current": f"{duration} hours",
                "target":  "8 hours",
                "action":  "Oversleeping can cause grogginess — aim for 7–8 hours",
                "impact":  "low"
            })

    if timing_score < 70:
        recommendations.append({
            "issue":   "Sleep time misaligned with natural rhythm",
            "current": f"Sleeping at {sleep_hour}:00",
            "target":  "10 PM – 6 AM",
            "action":  "Shift sleep 30 min earlier each week toward 10 PM",
            "impact":  "medium"
        })

    if light_color != "warm":
        recommendations.append({
            "issue":   "Light color affects melatonin",
            "current": f"{light_color} light",
            "target":  "Warm light",
            "action":  "Switch to warm/dim light 1 hour before sleep",
            "impact":  "medium"
        })

    # ── Health condition adjustments ──────────────────────────────────────
    health_tips = []
    optimal_adjustments = {}

    for condition in health_conditions:
        condition = condition.lower().replace(" ", "_")
        if condition in HEALTH_ADJUSTMENTS:
            adj = HEALTH_ADJUSTMENTS[condition]
            health_tips.append({
                "condition": condition.replace("_", " ").title(),
                "tip":       adj["tip"],
                "suggested_temp":  adj["temperature_c"],
                "suggested_noise": adj["noise_db"],
            })
            # Use strictest temperature recommendation
            if "temperature_c" not in optimal_adjustments:
                optimal_adjustments["temperature_c"] = adj["temperature_c"]
            else:
                optimal_adjustments["temperature_c"] = min(
                    optimal_adjustments["temperature_c"],
                    adj["temperature_c"]
                )

    # ── Ideal environment summary ─────────────────────────────────────────
    ideal_temp = optimal_adjustments.get("temperature_c", OPTIMAL["temperature_c"])
    ideal_env  = {
        "temperature_c": ideal_temp,
        "light_level":   0,
        "light_color":   "warm",
        "noise_db":      25.0 if health_conditions else 30.0,
        "recommended_sleep_time": "22:00",
        "recommended_wake_time":  "06:00",
    }

    return {
        "sleep_score":       sleep_score,
        "quality":           quality,
        "duration_hours":    duration,
        "score_breakdown": {
            "temperature":  round(temp_score, 1),
            "noise":        round(noise_score, 1),
            "light":        round(light_score, 1),
            "duration":     round(duration_score, 1),
            "timing":       round(timing_score, 1),
        },
        "recommendations":   recommendations,
        "health_tips":       health_tips,
        "ideal_environment": ideal_env,
    }