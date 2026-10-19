import logging
import math
import time
from typing import Any

import requests

from clients.exceptions import (
    InvalidResponseError,
    ServiceUnavailableError,
    UpstreamHTTPError,
)

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5
MAX_RETRIES = 2
BACKOFF_SECONDS = 0.5
MAX_RETRY_AFTER_SECONDS = 10
RETRYABLE_STATUSES = frozenset({500, 502, 503, 504})
TOO_MANY_REQUESTS = 429


def get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """GET-запрос с timeout и retry, возвращает разобранный JSON.

    Повторяет запрос при Timeout, ConnectionError, HTTP 500/502/503/504 и 429
    (для 429 ждёт столько секунд, сколько указано в числовом Retry-After).
    """
    attempts = MAX_RETRIES + 1
    reason = ""
    for attempt in range(1, attempts + 1):
        delay = BACKOFF_SECONDS * 2 ** (attempt - 1)
        logger.info("GET %s params=%s attempt=%d", url, params, attempt)
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            reason = type(exc).__name__
        else:
            status = response.status_code
            if status == TOO_MANY_REQUESTS:
                reason = "HTTP 429"
                retry_after = parse_retry_after(response.headers.get("Retry-After"))
                if retry_after is not None:
                    if retry_after > MAX_RETRY_AFTER_SECONDS:
                        raise ServiceUnavailableError(
                            f"{url}: лимит запросов, Retry-After={retry_after:g} с"
                        )
                    delay = retry_after
            elif status in RETRYABLE_STATUSES:
                reason = f"HTTP {status}"
            elif status >= 400:
                raise UpstreamHTTPError(url, status)
            else:
                return _decode_json(response)

        if attempt < attempts:
            logger.warning("Retry %s: %s, ждём %.1f с", url, reason, delay)
            time.sleep(delay)

    raise ServiceUnavailableError(
        f"{url}: сервис недоступен после {attempts} попыток ({reason})"
    )


def parse_retry_after(value: str | None) -> float | None:
    """Числовой Retry-After в секундах; дату и некорректные значения игнорируем."""
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    if not math.isfinite(seconds) or seconds < 0:
        return None
    return seconds


def _decode_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise InvalidResponseError(f"{response.url}: ответ не является JSON") from exc
