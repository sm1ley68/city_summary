import argparse
import json
import logging
import sys
import uuid
from typing import Any

from clients.http import ExternalServiceError, NotFoundError
from processing.service import build_city_summary

EXIT_OK = 0
EXIT_BAD_ARGS = 2
EXIT_NOT_FOUND = 3
EXIT_SERVICE_UNAVAILABLE = 4

logger = logging.getLogger("city_summary")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Сводка по городу: погода и курс валюты"
    )
    parser.add_argument(
        "--city", required=True, help="название города, например Moscow"
    )
    parser.add_argument(
        "--currency", default="USD", help="ISO-код валюты (по умолчанию USD)"
    )
    parser.add_argument("--json", action="store_true", help="вывести сводку в JSON")
    args = parser.parse_args(argv)
    if not args.city.strip():
        parser.error("--city не может быть пустым")
    if not args.currency.strip():
        parser.error("--currency не может быть пустым")
    return args


def setup_logging() -> str:
    run_id = uuid.uuid4().hex[:8]
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.run_id = run_id
        return record

    logging.setLogRecordFactory(record_factory)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [run_id=%(run_id)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    return run_id


def format_summary(summary: dict[str, Any]) -> str:
    weather, rates = summary["weather"], summary["rates"]
    return "\n".join(
        [
            f"Город: {summary['city']}",
            f"Погода: {weather['temp_c']}°C, {weather['description']}",
            f"Тёплая одежда: {'да' if weather['warm_clothes'] else 'нет'}",
            f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}",
            f"Дорогой курс: {'да' if rates['expensive'] else 'нет'}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_id = setup_logging()
    logger.info(
        "Запуск run_id=%s city=%s currency=%s", run_id, args.city, args.currency
    )

    try:
        summary = build_city_summary(args.city, args.currency)
    except NotFoundError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_NOT_FOUND
    except ExternalServiceError as exc:
        print(f"Ошибка: внешний сервис недоступен ({exc})", file=sys.stderr)
        return EXIT_SERVICE_UNAVAILABLE

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_summary(summary))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
