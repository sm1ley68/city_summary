import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clients import rates
from clients.exceptions import (
    CityNotFoundError,
    CurrencyNotFoundError,
    InvalidResponseError,
    UpstreamHTTPError,
)
from clients.weather import get_weather

GEO_RESPONSE = {"results": [{"name": "Moscow", "latitude": 55.75, "longitude": 37.61}]}
FORECAST_RESPONSE = {"current": {"temperature_2m": -3.2, "weather_code": 0}}


@patch("clients.weather.get_json")
class GetWeatherTest(unittest.TestCase):
    def test_parses_weather(self, mock_get_json) -> None:
        mock_get_json.side_effect = [GEO_RESPONSE, FORECAST_RESPONSE]
        self.assertEqual(
            get_weather("moscow"),
            {"city": "Moscow", "temp_c": -3.2, "description": "clear sky"},
        )

    def test_city_not_found(self, mock_get_json) -> None:
        mock_get_json.return_value = {"generationtime_ms": 0.1}
        with self.assertRaises(CityNotFoundError):
            get_weather("Qwzxyy")

    def test_missing_temperature(self, mock_get_json) -> None:
        mock_get_json.side_effect = [GEO_RESPONSE, {"current": {"weather_code": 0}}]
        with self.assertRaises(InvalidResponseError):
            get_weather("Moscow")


class GetRateTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        cache_patch = patch.object(
            rates, "CACHE_FILE", Path(tmp_dir.name) / "rates.json"
        )
        cache_patch.start()
        self.addCleanup(cache_patch.stop)

    @patch("clients.rates.get_json")
    def test_parses_rate(self, mock_get_json) -> None:
        mock_get_json.return_value = {"base": "USD", "quote": "RUB", "rate": 92.15}
        self.assertEqual(rates.get_rate("usd"), 92.15)
        mock_get_json.assert_called_once_with(
            "https://api.frankfurter.dev/v2/rate/USD/RUB"
        )

    @patch("clients.rates.get_json")
    def test_rate_is_cached(self, mock_get_json) -> None:
        mock_get_json.return_value = {"base": "EUR", "quote": "RUB", "rate": 99.0}
        rates.get_rate("EUR")
        self.assertEqual(rates.get_rate("EUR"), 99.0)
        mock_get_json.assert_called_once()

    @patch("clients.rates.get_json")
    def test_unknown_currency(self, mock_get_json) -> None:
        mock_get_json.side_effect = UpstreamHTTPError("url", 422)
        with self.assertRaises(CurrencyNotFoundError):
            rates.get_rate("XXX")

    @patch("clients.rates.get_json")
    def test_invalid_rate(self, mock_get_json) -> None:
        mock_get_json.return_value = {"base": "USD", "quote": "RUB", "rate": "abc"}
        with self.assertRaises(InvalidResponseError):
            rates.get_rate("USD")


if __name__ == "__main__":
    unittest.main()
