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

@router.get("/by-coordinates")
def weather_by_exact_coordinates(lat: float, lon: float, name: str = ""):
    """
    Get weather for exact coordinates.
    Use this after searching to pick the correct location from alternatives.
    """
    weather = get_weather(lat, lon)
    if name:
        weather["location"] = {"name": name, "lat": lat, "lon": lon}
    return weather

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

@router.get("/gps")
def weather_by_gps(lat: float, lon: float):
    import requests as req
    from app.hardware.weather import get_weather

    weather = get_weather(lat, lon)

    try:
        nom = req.get(
            "https://nominatim.openstreetmap.org/reverse",
            params  = {
                "lat":    lat,
                "lon":    lon,
                "format": "json",
                "zoom":   16,
                "addressdetails": 1,
            },
            headers = {"User-Agent": "SmartHomeAI/1.0"},
            timeout = 8,
        ).json()

        addr     = nom.get("address", {})
        suburb   = (addr.get("suburb") or addr.get("neighbourhood") or
                    addr.get("hamlet") or addr.get("quarter") or "")
        city     = (addr.get("city") or addr.get("town") or
                    addr.get("village") or addr.get("municipality") or "")
        district = addr.get("county") or addr.get("district") or ""
        state    = addr.get("state", "")
        country  = addr.get("country", "")
        postcode = addr.get("postcode", "")

        # Build readable name — most specific first
        if suburb and city:
            display_name = f"{suburb}, {city}"
        elif suburb:
            display_name = suburb
        elif city:
            display_name = city
        elif district:
            display_name = district
        else:
            display_name = nom.get("display_name", "").split(",")[0]

        full_address = ", ".join(filter(None, [suburb, city, district, state, country]))

        weather["location"] = {
            "name":         display_name,
            "full":         full_address,
            "suburb":       suburb,
            "city":         city,
            "district":     district,
            "state":        state,
            "country":      country,
            "postcode":     postcode,
            "lat":          lat,
            "lon":          lon,
            "detected_by":  "GPS + OpenStreetMap",
        }

    except Exception as e:
        weather["location"] = {
            "name":        "Your Location",
            "full":        f"{lat:.4f}°N, {lon:.4f}°E",
            "lat":         lat,
            "lon":         lon,
            "detected_by": "GPS",
        }

    return weather
