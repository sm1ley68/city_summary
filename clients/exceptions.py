class AppError(Exception):
    """Базовая ошибка приложения."""


class NotFoundError(AppError):
    """Запрошенная сущность не найдена во внешнем сервисе."""


class CityNotFoundError(NotFoundError):
    def __init__(self, city: str) -> None:
        super().__init__(f"Город не найден: {city}")
        self.city = city


class CurrencyNotFoundError(NotFoundError):
    def __init__(self, currency: str) -> None:
        super().__init__(f"Код валюты не найден: {currency}")
        self.currency = currency


class ExternalServiceError(AppError):
    """Внешний сервис не смог корректно ответить."""


class ServiceUnavailableError(ExternalServiceError):
    """Сервис недоступен после всех повторов."""


class UpstreamHTTPError(ExternalServiceError):
    """Сервис вернул статус ошибки, который не имеет смысла повторять (4xx)."""

    def __init__(self, url: str, status_code: int) -> None:
        super().__init__(f"{url}: HTTP {status_code}")
        self.url = url
        self.status_code = status_code


class InvalidResponseError(ExternalServiceError):
    """Ответ сервиса не соответствует ожидаемому формату."""
