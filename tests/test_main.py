import unittest
from unittest.mock import patch

import main
from clients.exceptions import CurrencyNotFoundError, ServiceUnavailableError

SUMMARY = {
    "city": "Moscow",
    "weather": {"temp_c": -3.2, "description": "clear sky", "warm_clothes": True},
    "rates": {"currency": "USD", "rate_to_rub": 92.15, "expensive": False},
}


@patch("main.setup_logging")
@patch("main.build_city_summary")
class MainTest(unittest.TestCase):
    def test_success(self, mock_build, _) -> None:
        mock_build.return_value = SUMMARY
        with patch("builtins.print") as mock_print:
            self.assertEqual(main.main(["--city", "Moscow"]), main.EXIT_OK)
        mock_build.assert_called_once_with("Moscow", "USD")
        self.assertIn("Тёплая одежда: да", mock_print.call_args.args[0])

    def test_not_found(self, mock_build, _) -> None:
        mock_build.side_effect = CurrencyNotFoundError("XXX")
        code = main.main(["--city", "Moscow", "--currency", "XXX"])
        self.assertEqual(code, main.EXIT_NOT_FOUND)

    def test_service_unavailable(self, mock_build, _) -> None:
        mock_build.side_effect = ServiceUnavailableError("down")
        code = main.main(["--city", "Moscow"])
        self.assertEqual(code, main.EXIT_SERVICE_UNAVAILABLE)

    def test_bad_args(self, mock_build, _) -> None:
        with self.assertRaises(SystemExit) as ctx:
            main.main([])
        self.assertEqual(ctx.exception.code, main.EXIT_BAD_ARGS)


if __name__ == "__main__":
    unittest.main()
