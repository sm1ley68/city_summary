from typing import Any

COLD_THRESHOLD_C = 0.0
EXPENSIVE_RATE_THRESHOLD = 100.0
UNKNOWN_DESCRIPTION = "no description"


def needs_warm_clothes(temp_c: float) -> bool:
    return temp_c < COLD_THRESHOLD_C


def is_expensive(rate_to_rub: float) -> bool:
    return rate_to_rub > EXPENSIVE_RATE_THRESHOLD


def normalize_description(description: str) -> str:
    description = description.strip()
    return description if description else UNKNOWN_DESCRIPTION


def preprocess_weather(weather: dict[str, Any]) -> dict[str, Any]:
    return {
        "temp_c": round(weather["temp_c"], 1),
        "description": normalize_description(weather["description"]),
        "warm_clothes": needs_warm_clothes(weather["temp_c"]),
    }


def preprocess_rate(currency: str, rate_to_rub: float) -> dict[str, Any]:
    return {
        "currency": currency,
        "rate_to_rub": round(rate_to_rub, 2),
        "expensive": is_expensive(rate_to_rub),
    }
