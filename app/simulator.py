import random
from datetime import datetime
from app.models.environment import EnvironmentState

ROOMS = ["bedroom", "living_room", "kitchen", "office"]

OUTSIDE_SOUNDS = [
    {"source": "traffic",        "db": 75, "description": "Vehicles passing"},
    {"source": "construction",   "db": 92, "description": "Nearby construction"},
    {"source": "rain",           "db": 51, "description": "Rain on windows"},
    {"source": "dog_barking",    "db": 68, "description": "Dog barking outside"},
    {"source": "people_talking", "db": 58, "description": "Voices from street"},
    {"source": "silence",        "db": 22, "description": "Quiet outside"},
    {"source": "wind",           "db": 45, "description": "Wind blowing"},
    {"source": "market_noise",   "db": 80, "description": "Market or crowd noise"},
    {"source": "vehicle_horn",   "db": 85, "description": "Vehicle horn"},
    {"source": "music_outside",  "db": 70, "description": "Music from neighbours"},
    {"source": "birds",          "db": 40, "description": "Birds chirping"},
    {"source": "temple_prayers", "db": 72, "description": "Nearby temple prayers"},
    {"source": "train",          "db": 88, "description": "Train passing nearby"},
    {"source": "airplane",       "db": 78, "description": "Airplane overhead"},
    {"source": "generator",      "db": 82, "description": "Generator noise"},
]

SOUND_BY_TIME = {
    "morning":   ["birds", "traffic", "market_noise", "people_talking"],
    "afternoon": ["traffic", "construction", "vehicle_horn", "market_noise"],
    "evening":   ["traffic", "people_talking", "music_outside", "temple_prayers"],
    "night":     ["silence", "wind", "dog_barking", "rain"],
}


def get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:   return "morning"
    if 12 <= hour < 17:  return "afternoon"
    if 17 <= hour < 21:  return "evening"
    return "night"


def simulate_room(room: str) -> EnvironmentState:
    time_of_day = get_time_of_day()

    # Base temperature by time — no external weather dependency
    base_temp   = {"morning": 24, "afternoon": 32, "evening": 28, "night": 22}
    temperature = base_temp[time_of_day] + random.uniform(-2, 2)

    noise       = random.uniform(30, 65)
    light_map   = {"morning": 70, "afternoon": 90, "evening": 50, "night": 10}
    light_level = light_map[time_of_day] + random.randint(-10, 10)
    light_level = max(0, min(100, light_level))
    color_map   = {"morning": "neutral", "afternoon": "cool",
                   "evening": "warm",    "night": "warm"}
    power       = random.uniform(200, 1800)
    ac_on       = temperature > 26
    fan_on      = temperature > 24 and not ac_on
    humidity    = random.uniform(35, 75)

    # Comfort score
    temp_diff = abs(temperature - 23)
    if temp_diff <= 2:
        temp_score = 100
    elif temp_diff <= 5:
        temp_score = 100 - (temp_diff - 2) * 8
    elif temp_diff <= 10:
        temp_score = 76 - (temp_diff - 5) * 6
    else:
        temp_score = max(10, 46 - (temp_diff - 10) * 3)

    noise_diff  = max(0, noise - 35)
    noise_score = max(20, 100 - noise_diff * 2.5)
    comfort     = round(temp_score * 0.6 + noise_score * 0.4, 1)
    comfort     = max(0, min(100, comfort))

    # Outside noise
    likely_sounds = SOUND_BY_TIME.get(time_of_day, ["silence"])
    sound_key     = random.choice(likely_sounds)
    sound_data    = next(
        (s for s in OUTSIDE_SOUNDS if s["source"] == sound_key),
        {"source": "silence", "db": 25, "description": "Quiet outside"}
    )
    outside_db    = round(sound_data["db"] + random.uniform(-5, 5), 1)

    if outside_db > 80:
        noise_impact = "High outside noise — close windows immediately"
    elif outside_db > 65:
        noise_impact = "Moderate outside noise — consider closing windows"
    elif outside_db > 45:
        noise_impact = "Low outside noise — windows can stay open"
    else:
        noise_impact = "Quiet outside — ideal for ventilation"

    # Comfort suggestions
    comfort_suggestions = []
    if temperature > 26:
        comfort_suggestions.append({
            "action":              "Turn on AC",
            "impact":              "high",
            "expected_score_gain": min(30, round((temperature - 24) * 3)),
        })
    elif temperature > 24:
        comfort_suggestions.append({
            "action":              "Turn on fan",
            "impact":              "medium",
            "expected_score_gain": 10,
        })
    if noise > 50:
        comfort_suggestions.append({
            "action":              "Close windows to reduce noise",
            "impact":              "medium",
            "expected_score_gain": 15,
        })
    if outside_db > 70:
        comfort_suggestions.append({
            "action":              "Close all windows — high outside noise",
            "impact":              "high",
            "expected_score_gain": 20,
        })

    return EnvironmentState(
        timestamp            = datetime.now(),
        room                 = room,
        temperature_c        = round(temperature, 1),
        humidity_percent     = round(humidity, 1),
        light_level          = light_level,
        light_color          = color_map[time_of_day],
        noise_db             = round(noise, 1),
        music_playing        = random.choice([True, False]),
        power_watts          = round(power, 1),
        ac_on                = ac_on,
        fan_on               = fan_on,
        comfort_score        = comfort,
        outside_noise_source = sound_data["source"],
        outside_noise_db     = outside_db,
        outside_noise_desc   = sound_data["description"],
        outside_noise_impact = noise_impact,
        comfort_suggestions  = comfort_suggestions,
    )


def simulate_all_rooms() -> dict:
    return {room: simulate_room(room) for room in ROOMS}
