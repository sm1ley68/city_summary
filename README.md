# City Summary

CLI-утилита «Сводка по городу»: получает текущую погоду и курс выбранной валюты к рублю
из внешних API, применяет правила предобработки и печатает сводку в консоль.

Внешние API (ключи не нужны):
- погода — [Open-Meteo](https://open-meteo.com/): сначала геокодинг города, затем прогноз по координатам;
- курс — [Frankfurter](https://frankfurter.dev/): `GET https://api.frankfurter.dev/v2/rate/{currency}/RUB`.

## Требования

- Python 3.12
- Зависимости из `requirements.txt` (`requests`)

## Установка

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

```bash
python main.py --city Moscow                  # курс USD→RUB (по умолчанию)
python main.py --city Moscow --currency EUR   # курс EUR→RUB
python main.py --city Moscow --json           # сводка в JSON
```

Пример вывода:

```text
Город: Moscow
Погода: -3.2°C, clear sky
Тёплая одежда: да
USD→RUB: 92.15
Дорогой курс: нет
```

## Коды выхода

| Код | Значение |
|-----|----------|
| 0 | успех |
| 2 | ошибка аргументов |
| 3 | город или код валюты не найден |
| 4 | внешний сервис недоступен после retry (или вернул некорректный ответ) |

## Структура

```text
city_summary/
├── main.py                 # CLI: argparse, логирование с run_id, вывод, коды выхода
├── clients/                # только общение с внешними API
│   ├── http.py             # общий GET: timeout 5 с, 2 повтора, Retry-After для 429; исключения
│   ├── weather.py          # get_weather(city) → dict
│   └── rates.py            # get_rate(currency) → float, кэш курса на 5 минут
├── processing/
│   ├── preprocessing.py    # правила: warm_clothes, expensive, пустое описание погоды
│   └── service.py          # build_city_summary(city, currency="USD") → dict
└── tests/                  # unittest + unittest.mock, без сетевых запросов
    ├── test_preprocessing.py
    ├── test_http.py
    └── test_clients.py
```

## Правила предобработки

- температура `< 0 °C` → `warm_clothes: true`;
- курс `> 100` RUB → `expensive: true`;
- пустое описание погоды → `"no description"`.

## Надёжность запросов

- только GET, timeout 5 с на каждый запрос;
- до 2 повторов после первой попытки при `Timeout`, `ConnectionError`, HTTP 500/502/503/504 и 429
  (для 429 ждём числовой `Retry-After`, иначе экспоненциальная пауза);
- ответы проверяются на статус, формат JSON и обязательные поля; неожиданный ответ → понятная ошибка.

## Дополнительно

- логирование с `run_id` (логи пишутся в stderr, сводка — в stdout);
- кэш курса на 5 минут (`~/.cache/city_summary/rates.json`);
- флаг `--json`;
- аннотации типов;
- тесты клиентов через `unittest.mock`.

## Тесты

```bash
python -m unittest discover -s tests -t .
```
