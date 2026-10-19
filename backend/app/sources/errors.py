"""Source-layer errors mapped to API error codes later."""


class SourceError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AppNotFoundError(SourceError):
    def __init__(self, message: str = "App not found on the store.") -> None:
        super().__init__("app_not_found", message, status_code=404)


class SourceRateLimited(SourceError):
    def __init__(self, message: str = "Store rate-limited the request. Try again shortly.") -> None:
        super().__init__("rate_limited", message, status_code=429)


class SourceUnavailable(SourceError):
    def __init__(self, message: str) -> None:
        super().__init__("source_unavailable", message, status_code=502)
