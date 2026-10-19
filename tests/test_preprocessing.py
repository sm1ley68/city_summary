import unittest

from processing.preprocessing import (
    UNKNOWN_DESCRIPTION,
    preprocess_rate,
    preprocess_weather,
)


class PreprocessWeatherTest(unittest.TestCase):
    def test_cold_weather_needs_warm_clothes(self) -> None:
        result = preprocess_weather({"temp_c": -3.2, "description": "clear sky"})
        self.assertTrue(result["warm_clothes"])

    def test_zero_degrees_is_not_cold(self) -> None:
        result = preprocess_weather({"temp_c": 0.0, "description": "clear sky"})
        self.assertFalse(result["warm_clothes"])

    def test_empty_description_replaced(self) -> None:
        result = preprocess_weather({"temp_c": 10.0, "description": "  "})
        self.assertEqual(result["description"], UNKNOWN_DESCRIPTION)


class PreprocessRateTest(unittest.TestCase):
    def test_expensive_rate(self) -> None:
        result = preprocess_rate("EUR", 100.5)
        self.assertEqual(
            result, {"currency": "EUR", "rate_to_rub": 100.5, "expensive": True}
        )

    def test_rate_on_threshold_is_not_expensive(self) -> None:
        self.assertFalse(preprocess_rate("USD", 100.0)["expensive"])


if __name__ == "__main__":
    unittest.main()
