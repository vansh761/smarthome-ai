from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EnvironmentState(BaseModel):
    timestamp: datetime
    room: str

    # Climate
    temperature_c: float       # e.g. 24.5°C
    humidity_percent: float    # e.g. 60.0%

    # Lighting
    light_level: int           # 0 (off) to 100 (full brightness)
    light_color: str           # "warm", "cool", "neutral"

    # Sound
    noise_db: float            # e.g. 35.0 dB (quiet room)
    music_playing: bool

    # Power
    power_watts: float         # total power consumption
    ac_on: bool
    fan_on: bool

    # Computed comfort score (0-100)
    comfort_score: Optional[float] = None