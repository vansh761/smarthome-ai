from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.ai.sleep_model import predict_sleep_quality

router = APIRouter(prefix="/sleep", tags=["Sleep Engine"])


class SleepRequest(BaseModel):
    # Current room environment
    temperature_c:     float = 24.0
    noise_db:          float = 40.0
    light_level:       int   = 10      # 0–100
    light_color:       str   = "warm"  # warm / cool / neutral

    # Sleep schedule
    sleep_hour:        int   = 23      # hour you sleep (23 = 11 PM)
    wake_hour:         int   = 7       # hour you wake

    # Optional health conditions
    health_conditions: List[str] = []  # e.g. ["high_bp", "anxiety"]


@router.post("/predict")
def predict_sleep(req: SleepRequest):
    """
    Predict sleep quality score and get personalized recommendations.
    Supports health conditions for tailored suggestions.
    """
    return predict_sleep_quality(
        temperature_c     = req.temperature_c,
        noise_db          = req.noise_db,
        light_level       = req.light_level,
        sleep_hour        = req.sleep_hour,
        wake_hour         = req.wake_hour,
        light_color       = req.light_color,
        health_conditions = req.health_conditions,
    )


@router.get("/conditions")
def list_health_conditions():
    """List all supported health conditions with descriptions."""
    return {
        "supported_conditions": {
            "blood_pressure": ["high_bp", "low_bp"],
            "blood_sugar":    ["high_sugar", "low_sugar", "diabetes"],
            "haemoglobin":    ["low_haemoglobin", "anaemia", "high_haemoglobin"],
            "heart_rate":     ["high_heart_rate", "tachycardia", "low_heart_rate", "bradycardia"],
            "mental_health":  ["anxiety", "insomnia"],
            "respiratory":    ["asthma"],
            "neurological":   ["migraine"],
            "joints":         ["arthritis"],
            "hormonal":       ["thyroid_hypo", "thyroid_hyper", "pcod", "pcos"],
        },
        "total_conditions": 20,
        "usage": "Pass any condition key in health_conditions array",
        "example": {
            "temperature_c": 26,
            "noise_db": 40,
            "light_level": 20,
            "light_color": "cool",
            "sleep_hour": 23,
            "wake_hour": 7,
            "health_conditions": ["high_bp", "high_heart_rate"]
        },
        "note": "No medicine names are ever suggested — environment adjustments only"
    }


@router.get("/optimal")
def optimal_environment():
    """Get the research-backed optimal sleep environment."""
    return {
        "temperature_c":  "18–22°C (ideal: 20°C)",
        "noise_db":       "Under 30 dB",
        "light_level":    "0% (complete darkness)",
        "light_color":    "Warm light 1 hour before sleep",
        "duration":       "7–9 hours (ideal: 8 hours)",
        "sleep_time":     "10 PM – 11 PM",
        "wake_time":      "6 AM – 7 AM",
        "sources":        "Based on sleep science research (NIH, Sleep Foundation)"
    }