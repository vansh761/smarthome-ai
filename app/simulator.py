import random
from datetime import datetime
from app.models.environment import EnvironmentState
from app.hardware.weather import get_weather_by_place
import random
from datetime import datetime


# Cache weather for 10 minutes to avoid too many API calls
_weather_cache = {"data": None, "timestamp": None, "city": None}

# Rooms in our virtual house
ROOMS = ["bedroom", "living_room", "kitchen", "office"]


OUTSIDE_SOUNDS = [
    {"source": "traffic",         "db": 75, "description": "Vehicles passing"},
    {"source": "construction",    "db": 92, "description": "Nearby construction work"},
    {"source": "rain",            "db": 51, "description": "Rain on windows"},
    {"source": "dog_barking",     "db": 68, "description": "Dog barking outside"},
    {"source": "people_talking",  "db": 58, "description": "Voices from street"},
    {"source": "silence",         "db": 22, "description": "Quiet outside"},
    {"source": "wind",            "db": 45, "description": "Wind blowing"},
    {"source": "market_noise",    "db": 80, "description": "Market or crowd noise"},
    {"source": "vehicle_horn",    "db": 85, "description": "Vehicle horn"},
    {"source": "music_outside",   "db": 70, "description": "Music from neighbours"},
    {"source": "birds",           "db": 40, "description": "Birds chirping"},
    {"source": "temple_prayers",  "db": 72, "description": "Nearby temple prayers"},
    {"source": "train",           "db": 88, "description": "Train passing nearby"},
    {"source": "airplane",        "db": 78, "description": "Airplane overhead"},
    {"source": "generator",       "db": 82, "description": "Generator noise"},
]

SOUND_BY_TIME = {
    "morning":   ["birds", "traffic", "market_noise", "people_talking"],
    "afternoon": ["traffic", "construction", "vehicle_horn", "market_noise"],
    "evening":   ["traffic", "people_talking", "music_outside", "temple_prayers"],
    "night":     ["silence", "wind", "dog_barking", "rain"],
}

def get_current_weather(city: str = "delhi") -> dict:
    from datetime import datetime, timedelta

    now = datetime.now()

    if (
        _weather_cache["data"] is not None and
        _weather_cache["city"] == city and
        _weather_cache["timestamp"] is not None and
        (now - _weather_cache["timestamp"]).seconds < 600
    ):
        return _weather_cache["data"]

    weather = get_weather_by_place(city)

    if "error" not in weather:
        _weather_cache["data"] = weather
        _weather_cache["timestamp"] = now
        _weather_cache["city"] = city

    return weather

def get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

def simulate_room(room: str) -> EnvironmentState:
    """Generate realistic fake sensor data for a room."""
    
    time_of_day = get_time_of_day()
    
    # Try to use real weather data
    weather = get_current_weather("delhi")  # change city as needed
    if "error" not in weather and "indoor_estimate" in weather:
        temperature = weather["indoor_estimate"]["temperature_c"] + random.uniform(-0.5, 0.5)
        real_humidity = weather["indoor_estimate"]["humidity_percent"]
    else:
        base_temp   = {"morning": 22, "afternoon": 28, "evening": 25, "night": 21}
        temperature = base_temp[time_of_day] + random.uniform(-1.5, 1.5)
        real_humidity = None
    
    # Noise varies by room and time
    noise_base = {
        "bedroom": 30, "living_room": 45,
        "kitchen": 50, "office": 35
    }
    noise = noise_base[room] + random.uniform(-5, 10)
    
    # Light varies by time of day
    light_map = {"morning": 70, "afternoon": 90, "evening": 50, "night": 20}
    light_level = light_map[time_of_day] + random.randint(-10, 10)
    light_level = max(0, min(100, light_level))  # clamp between 0-100
    
    # Light color by time
    color_map = {
        "morning": "neutral", "afternoon": "cool",
        "evening": "warm",    "night": "warm"
    }
    
    # Power usage
    ac_on = temperature > 26
    fan_on = temperature > 23 and not ac_on
    base_power = 150
    power = base_power + (1200 if ac_on else 0) + (75 if fan_on else 0)
    power += random.uniform(-20, 20)
    
    # Comfort score (simple formula for now, AI will replace this later)
    # Comfort score — realistic formula
    # Temperature: optimal 22-24°C, penalty increases gradually
    temp_diff = abs(temperature - 23)
    if temp_diff <= 2:
        temp_score = 100
    elif temp_diff <= 5:
        temp_score = 100 - (temp_diff - 2) * 8
    elif temp_diff <= 10:
        temp_score = 76 - (temp_diff - 5) * 6
    else:
        temp_score = max(10, 46 - (temp_diff - 10) * 3)

    # Noise: optimal below 35dB
    noise_diff = max(0, noise - 35)
    noise_score = max(20, 100 - noise_diff * 2.5)

    comfort = round((temp_score * 0.6 + noise_score * 0.4), 1)
    comfort = max(0, min(100, comfort))

    # Outside noise based on time of day
    # Outside noise
    time_of_day  = get_time_of_day()
    likely_sounds= SOUND_BY_TIME.get(time_of_day, ["silence"])
    sound_key    = random.choice(likely_sounds)
    sound_data   = next(
        (s for s in OUTSIDE_SOUNDS if s["source"] == sound_key),
        {"source": "silence", "db": 25, "description": "Quiet outside"}
    )
    outside_db   = round(sound_data["db"] + random.uniform(-5, 5), 1)

    # Impact of outside noise on indoor
    if outside_db > 80:
        noise_impact = "High outside noise — close windows immediately"
    elif outside_db > 65:
        noise_impact = "Moderate outside noise — consider closing windows"
    elif outside_db > 45:
        noise_impact = "Low outside noise — windows can stay open"
    else:
        noise_impact = "Quiet outside — ideal for ventilation"

    return EnvironmentState(
        timestamp            = datetime.now(),
        room                 = room,
        temperature_c        = round(temperature, 1),
        humidity_percent     = round(
            real_humidity if real_humidity else random.uniform(40, 70), 1
        ),
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
    )

def simulate_all_rooms() -> dict:
    """Snapshot of the entire virtual house."""
    return {room: simulate_room(room) for room in ROOMS}
