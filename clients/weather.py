import logging
from typing import Any

from clients.http import CityNotFoundError, InvalidResponseError, get_json

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Коды погоды WMO из документации Open-Meteo.
WMO_DESCRIPTIONS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def get_weather(city: str) -> dict[str, Any]:
    """Текущая погода в городе: {"city", "temp_c", "description"}."""
    name, latitude, longitude = _geocode(city)
    data = get_json(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
        },
    )
    current = _require_dict(data, "current")
    temp_c = _require_number(current, "temperature_2m")
    weather_code = _require_number(current, "weather_code")
    weather = {
        "city": name,
        "temp_c": float(temp_c),
        "description": WMO_DESCRIPTIONS.get(int(weather_code), ""),
    }
    logger.info("Погода получена: %s", weather)
    return weather


def _geocode(city: str) -> tuple[str, float, float]:
    data = get_json(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
    )
    if not isinstance(data, dict):
        raise InvalidResponseError("Open-Meteo geocoding: ожидался JSON-объект")
    results = data.get("results", [])
    if not isinstance(results, list):
        raise InvalidResponseError("Open-Meteo geocoding: поле results не список")
    if not results:
        raise CityNotFoundError(city)

    place = results[0]
    if not isinstance(place, dict) or not isinstance(place.get("name"), str):
        raise InvalidResponseError("Open-Meteo geocoding: нет поля name")
    latitude = _require_number(place, "latitude")
    longitude = _require_number(place, "longitude")
    return place["name"], float(latitude), float(longitude)


def _require_dict(data: Any, key: str) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get(key), dict):
        raise InvalidResponseError(f"Open-Meteo: нет объекта {key}")
    return data[key]


def _require_number(data: dict[str, Any], key: str) -> int | float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidResponseError(f"Open-Meteo: поле {key} отсутствует или не число")
    return value
