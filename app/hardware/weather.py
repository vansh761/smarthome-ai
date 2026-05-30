import requests
from datetime import datetime
from typing import Optional


def geocode_place(place_name: str, country: str = "IN") -> dict:
    """
    Convert any place name to coordinates using Open-Meteo geocoding.
    Works for cities, districts, villages, colonies, landmarks.
    Free, no API key required.
    """
    url    = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name":     place_name,
        "count":    10,
        "language": "en",
        "format":   "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data     = response.json()

        if not data.get("results"):
            return {
                "found": False,
                "error": f"No location found for '{place_name}'",
                "tip":   "Try adding state or district name. Example: 'Chandni Chowk, Delhi'",
            }

        results = []
        for r in data["results"]:
            results.append({
                "name":       r.get("name", ""),
                "state":      r.get("admin1", ""),
                "district":   r.get("admin2", ""),
                "country":    r.get("country", ""),
                "lat":        r["latitude"],
                "lon":        r["longitude"],
                "elevation":  r.get("elevation", 0),
                "population": r.get("population", 0),
                "timezone":   r.get("timezone", "Asia/Kolkata"),
            })

        # Return best match (first result) and all alternatives
        best   = results[0]
        others = results[1:]

        return {
            "found":        True,
            "best_match":   best,
            "alternatives": others,
            "search_query": place_name,
        }

    except requests.exceptions.Timeout:
        return {"found": False, "error": "Geocoding API timeout"}
    except Exception as e:
        return {"found": False, "error": str(e)}


def get_weather(lat: float, lon: float, timezone: str = "Asia/Kolkata") -> dict:
    """
    Fetch current weather from Open-Meteo API for any coordinates.
    Works for any location on earth.
    """
    url    = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
            "cloud_cover",
            "pressure_msl",
            "surface_pressure",
            "visibility",
            "uv_index",
            "is_day",
        ],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "wind_speed_10m",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "sunrise",
            "sunset",
            "uv_index_max",
            "precipitation_sum",
            "precipitation_probability_max",
        ],
        "timezone":      timezone,
        "forecast_days": 3,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data    = response.json()
        current = data["current"]
        daily   = data.get("daily", {})

        temp        = current["temperature_2m"]
        humidity    = current["relative_humidity_2m"]
        feels_like  = current["apparent_temperature"]
        wind_speed  = current["wind_speed_10m"]
        wind_dir    = current.get("wind_direction_10m", 0)
        rain        = current["precipitation"]
        cloud_cover = current["cloud_cover"]
        is_day      = current["is_day"]
        pressure    = current["pressure_msl"]
        uv_index    = current.get("uv_index", 0)
        visibility  = current.get("visibility", 10000)
        weather_code= current["weather_code"]

        # Indoor estimates
        month = datetime.now().month
        if month in (3, 4, 5, 6, 7, 8):
            indoor_temp = round(temp + 1.5, 1)
        elif month in (11, 12, 1, 2):
            indoor_temp = round(temp - 1.0, 1)
        else:
            indoor_temp = round(temp + 0.5, 1)

        indoor_humidity = round(min(95, humidity * 0.85), 1)

        if wind_speed > 30:
            base_noise = 50.0
        elif wind_speed > 15:
            base_noise = 42.0
        elif rain > 0:
            base_noise = 38.0
        else:
            base_noise = 33.0

        # 3-day forecast
        forecast = []
        if daily.get("temperature_2m_max"):
            for i in range(min(3, len(daily["temperature_2m_max"]))):
                forecast.append({
                    "date":             daily["time"][i] if "time" in daily else "",
                    "max_temp":         daily["temperature_2m_max"][i],
                    "min_temp":         daily["temperature_2m_min"][i],
                    "sunrise":          daily["sunrise"][i] if "sunrise" in daily else "",
                    "sunset":           daily["sunset"][i] if "sunset" in daily else "",
                    "rain_mm":          daily["precipitation_sum"][i] if "precipitation_sum" in daily else 0,
                    "rain_probability": daily["precipitation_probability_max"][i] if "precipitation_probability_max" in daily else 0,
                    "uv_max":           daily["uv_index_max"][i] if "uv_index_max" in daily else 0,
                })

        return {
            "source":    "open-meteo",
            "timestamp": current["time"],
            "outdoor": {
                "temperature_c":    temp,
                "feels_like_c":     feels_like,
                "humidity_percent": humidity,
                "wind_speed_kmh":   wind_speed,
                "wind_direction":   wind_direction_label(wind_dir),
                "precipitation_mm": rain,
                "cloud_cover_pct":  cloud_cover,
                "pressure_hpa":     pressure,
                "uv_index":         uv_index,
                "visibility_m":     visibility,
                "is_day":           bool(is_day),
                "condition":        get_weather_description(weather_code),
                "weather_code":     weather_code,
            },
            "indoor_estimate": {
                "temperature_c":    indoor_temp,
                "humidity_percent": indoor_humidity,
                "noise_db_estimate":base_noise,
                "note": "Estimated from outdoor — use physical sensor for accuracy",
            },
            "forecast_3day":   forecast,
            "sleep_impact":    assess_sleep_impact(temp, humidity, rain, wind_speed, is_day),
            "recommendations": get_weather_recommendations(temp, humidity, rain, wind_speed, indoor_temp),
        }

    except requests.exceptions.Timeout:
        return {"error": "Weather API timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach weather API"}
    except Exception as e:
        return {"error": str(e)}


def get_weather_by_place(place_name: str) -> dict:
    geo = geocode_place(place_name)

    if not geo.get("found"):
        return {
            "error":        geo.get("error"),
            "search_query": place_name,
            "tip":          geo.get("tip", "Try adding state or country. Example: 'Ambala Cantt, Haryana'"),
        }

    best    = geo["best_match"]
    weather = get_weather(best["lat"], best["lon"], best.get("timezone", "Asia/Kolkata"))

    if "error" in weather:
        return weather

    weather["location"] = {
        "name":        best["name"],
        "state":       best["state"],
        "district":    best["district"],
        "country":     best["country"],
        "lat":         best["lat"],
        "lon":         best["lon"],
        "elevation_m": best["elevation"],
        "search_query":place_name,
    }

    # Show all alternatives so user can pick the right one
    if geo["alternatives"]:
        weather["other_matches"] = [
            {
                "name":    f"{r['name']}, {r['state']}, {r['country']}",
                "lat":     r["lat"],
                "lon":     r["lon"],
            }
            for r in geo["alternatives"]
        ]

    return weather

def wind_direction_label(degrees: float) -> str:
    directions = ["N","NE","E","SE","S","SW","W","NW"]
    index      = round(degrees / 45) % 8
    return directions[index]


def get_weather_description(code: int) -> str:
    descriptions = {
        0:  "Clear sky",
        1:  "Mainly clear",
        2:  "Partly cloudy",
        3:  "Overcast",
        45: "Foggy",
        48: "Icy fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",
        85: "Light snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, f"Weather code {code}")


def assess_sleep_impact(
    temp: float, humidity: float,
    rain: float, wind_speed: float, is_day: int
) -> dict:
    impacts = []
    score   = 100

    if temp > 38:
        score -= 40
        impacts.append("Extreme heat — AC is essential, sleep will be severely affected without it")
    elif temp > 33:
        score -= 30
        impacts.append("Very hot night — AC strongly recommended")
    elif temp > 30:
        score -= 20
        impacts.append("Hot night — AC or fan strongly recommended")
    elif temp > 26:
        score -= 10
        impacts.append("Warm night — fan recommended")
    elif temp < 15:
        score -= 10
        impacts.append("Cold night — extra blanket recommended")
    elif 18 <= temp <= 22:
        score += 5
        impacts.append("Ideal outdoor temperature for sleep")

    if humidity > 80:
        score -= 15
        impacts.append("Very humid — AC dry mode or dehumidifier recommended")
    elif humidity > 70:
        score -= 8
        impacts.append("Humid — ensure ventilation")
    elif 40 <= humidity <= 60:
        score += 5
        impacts.append("Ideal humidity for sleep")

    if wind_speed > 30:
        score -= 10
        impacts.append("Strong winds — close windows to reduce noise")
    elif wind_speed > 15:
        score -= 5
        impacts.append("Moderate wind noise expected")

    if rain > 0:
        score += 5
        impacts.append("Rain — natural white noise, good for sleep")

    return {
        "sleep_weather_score": min(100, max(0, score)),
        "impacts":  impacts,
        "overall":  (
            "Excellent for sleep" if score >= 90 else
            "Good for sleep"      if score >= 75 else
            "Fair for sleep"      if score >= 60 else
            "Challenging — adjustments needed"
        ),
    }


def get_weather_recommendations(
    temp: float, humidity: float,
    rain: float, wind_speed: float, indoor_temp: float
) -> list:
    recs = []
    if indoor_temp > 28:
        recs.append("Turn on AC — indoor temperature will be high")
    elif indoor_temp > 25:
        recs.append("Use fan — indoor temperature moderately warm")
    elif indoor_temp < 18:
        recs.append("Keep room warm — cold outdoor weather")
    if humidity > 75:
        recs.append("High humidity — keep windows closed, use AC dry mode")
    if rain > 5:
        recs.append("Heavy rain — close windows to prevent dampness")
    elif rain > 0:
        recs.append("Light rain — good for relaxation and sleep")
    if wind_speed > 25:
        recs.append("Strong winds — close windows to reduce noise and dust")
    if not recs:
        recs.append("Good conditions — natural ventilation suitable")
    return recs
