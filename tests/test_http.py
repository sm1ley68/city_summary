import unittest
from unittest.mock import MagicMock, patch

import requests

from clients.exceptions import ServiceUnavailableError, UpstreamHTTPError
from clients.http import MAX_RETRIES, TIMEOUT_SECONDS, get_json, parse_retry_after


def make_response(status: int, payload: object = None, headers: dict | None = None):
    response = MagicMock(spec=requests.Response)
    response.status_code = status
    response.headers = headers or {}
    response.json.return_value = payload
    response.url = "https://example.com"
    return response


@patch("clients.http.time.sleep")
@patch("clients.http.requests.get")
class GetJsonTest(unittest.TestCase):
    def test_success_uses_timeout(self, mock_get, mock_sleep) -> None:
        mock_get.return_value = make_response(200, {"ok": True})
        self.assertEqual(get_json("https://example.com"), {"ok": True})
        self.assertEqual(mock_get.call_args.kwargs["timeout"], TIMEOUT_SECONDS)
        self.assertLessEqual(TIMEOUT_SECONDS, 10)

    def test_retries_on_5xx_then_succeeds(self, mock_get, mock_sleep) -> None:
        mock_get.side_effect = [
            make_response(503),
            make_response(502),
            make_response(200, {"ok": True}),
        ]
        self.assertEqual(get_json("https://example.com"), {"ok": True})
        self.assertEqual(mock_get.call_count, 3)

    def test_gives_up_after_retries_on_timeout(self, mock_get, mock_sleep) -> None:
        mock_get.side_effect = requests.exceptions.Timeout
        with self.assertRaises(ServiceUnavailableError):
            get_json("https://example.com")
        self.assertEqual(mock_get.call_count, MAX_RETRIES + 1)

    def test_connection_error_is_retried(self, mock_get, mock_sleep) -> None:
        mock_get.side_effect = [
            requests.exceptions.ConnectionError,
            make_response(200, [1]),
        ]
        self.assertEqual(get_json("https://example.com"), [1])

    def test_429_waits_retry_after(self, mock_get, mock_sleep) -> None:
        mock_get.side_effect = [
            make_response(429, headers={"Retry-After": "3"}),
            make_response(200, {"ok": True}),
        ]
        get_json("https://example.com")
        mock_sleep.assert_called_once_with(3.0)

    def test_4xx_is_not_retried(self, mock_get, mock_sleep) -> None:
        mock_get.return_value = make_response(422)
        with self.assertRaises(UpstreamHTTPError) as ctx:
            get_json("https://example.com")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(mock_get.call_count, 1)


class ParseRetryAfterTest(unittest.TestCase):
    def test_values(self) -> None:
        self.assertEqual(parse_retry_after("5"), 5.0)
        self.assertIsNone(parse_retry_after(None))
        self.assertIsNone(parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT"))
        self.assertIsNone(parse_retry_after("-1"))


if __name__ == "__main__":
    unittest.main()
