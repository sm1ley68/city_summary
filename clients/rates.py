import json
import logging
import os
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

from clients.http import (
    CurrencyNotFoundError,
    InvalidResponseError,
    UpstreamHTTPError,
    get_json,
)

logger = logging.getLogger(__name__)

RATE_URL = "https://api.frankfurter.dev/v2/rate/{currency}/RUB"
CACHE_TTL_SECONDS = 5 * 60
CACHE_DIR = (
    Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "city_summary"
)
CACHE_FILE = CACHE_DIR / "rates.json"

# Frankfurter отвечает 422 на неизвестный код валюты.
NOT_FOUND_STATUSES = frozenset({404, 422})


def get_rate(currency: str) -> float:
    """Курс валюты к рублю (сколько RUB стоит 1 единица currency)."""
    code = currency.strip().upper()
    cached = _read_cache(code)
    if cached is not None:
        logger.info("Курс %s→RUB взят из кэша: %s", code, cached)
        return cached

    url = RATE_URL.format(currency=quote(code, safe=""))
    try:
        data = get_json(url)
    except UpstreamHTTPError as exc:
        if exc.status_code in NOT_FOUND_STATUSES:
            raise CurrencyNotFoundError(code) from exc
        raise

    if not isinstance(data, dict):
        raise InvalidResponseError("Frankfurter: ожидался JSON-объект")
    rate = data.get("rate")
    if isinstance(rate, bool) or not isinstance(rate, int | float) or rate <= 0:
        raise InvalidResponseError("Frankfurter: поле rate отсутствует или некорректно")
    if data.get("base") != code or data.get("quote") != "RUB":
        raise InvalidResponseError(
            f"Frankfurter: ожидался курс {code}→RUB, "
            f"получен {data.get('base')}→{data.get('quote')}"
        )

    rate = float(rate)
    logger.info("Курс %s→RUB получен: %s", code, rate)
    _write_cache(code, rate)
    return rate


def _load_cache() -> dict:
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_cache(code: str) -> float | None:
    entry = _load_cache().get(code)
    if not isinstance(entry, dict):
        return None
    rate, saved_at = entry.get("rate"), entry.get("saved_at")
    if not isinstance(rate, int | float) or not isinstance(saved_at, int | float):
        return None
    if rate <= 0 or not 0 <= time.time() - saved_at <= CACHE_TTL_SECONDS:
        return None
    return float(rate)


def _write_cache(code: str, rate: float) -> None:
    cache = _load_cache()
    cache[code] = {"rate": rate, "saved_at": time.time()}
    try:
        CACHE_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Пишем во временный файл и атомарно подменяем, чтобы не оставить битый кэш.
        fd, tmp_path = tempfile.mkstemp(dir=CACHE_FILE.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(cache, tmp_file)
        os.replace(tmp_path, CACHE_FILE)
    except OSError:
        logger.warning("Не удалось сохранить кэш курса в %s", CACHE_FILE)
