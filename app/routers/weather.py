from fastapi import APIRouter
from app.hardware.weather import get_weather, get_weather_by_place, geocode_place

router = APIRouter(prefix="/weather", tags=["Weather & Environment"])


@router.get("/place")
def weather_by_place(name: str):
    """
    Get weather for ANY place in India or world.
    Works for cities, districts, villages, colonies, landmarks.

    Examples:
      /weather/place?name=Lajpat Nagar, Delhi
      /weather/place?name=Koramangala, Bangalore
      /weather/place?name=Dharavi, Mumbai
      /weather/place?name=Sector 17, Chandigarh
      /weather/place?name=Rampur, Himachal Pradesh
      /weather/place?name=my colony name, city name
    """
    return get_weather_by_place(name)


@router.get("/coordinates")
def weather_by_coordinates(lat: float, lon: float):
    """Get weather for exact GPS coordinates."""
    return get_weather(lat, lon)


@router.get("/search")
def search_place(name: str):
    """
    Search for a place and get its coordinates.
    Shows all matching results so user can pick the right one.
    """
    return geocode_place(name)


@router.get("/sleep-conditions")
def sleep_conditions(name: str):
    """
    Get tonight's sleep conditions for any place.
    Combines real weather with sleep quality prediction.
    """
    weather = get_weather_by_place(name)
    if "error" in weather:
        return weather

    indoor  = weather.get("indoor_estimate", {})
    outdoor = weather.get("outdoor", {})

    from app.ai.sleep_model import predict_sleep_quality
    sleep = predict_sleep_quality(
        temperature_c     = indoor.get("temperature_c", 25),
        noise_db          = indoor.get("noise_db_estimate", 40),
        light_level       = 5 if not outdoor.get("is_day") else 40,
        sleep_hour        = 23,
        wake_hour         = 7,
        light_color       = "warm",
        health_conditions = [],
    )

    return {
        "place":    weather.get("location", {}).get("name", name),
        "weather":  weather,
        "sleep":    sleep,
        "summary":  (
            f"Tonight in {weather.get('location',{}).get('name',name)}: "
            f"{outdoor.get('temperature_c')}°C, "
            f"{outdoor.get('condition')}. "
            f"Sleep score: {sleep['sleep_score']}/100 ({sleep['quality']})"
        ),
    }