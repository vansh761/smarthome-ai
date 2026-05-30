from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EnvironmentState(BaseModel):
    timestamp:             datetime
    room:                  str

    # Climate
    temperature_c:         float
    humidity_percent:      float

    # Lighting
    light_level:           int
    light_color:           str

    # Sound
    noise_db:              float
    music_playing:         bool

    # Power
    power_watts:           float
    ac_on:                 bool
    fan_on:                bool

    # Comfort
    comfort_score:         Optional[float] = None
    comfort_suggestions:   Optional[list] = None
    
    # Outside noise — new
    outside_noise_source:  Optional[str]   = None
    outside_noise_db:      Optional[float] = None
    outside_noise_desc:    Optional[str]   = None
    outside_noise_impact:  Optional[str]   = None
    
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
