"""LLM-related exceptions for Esnaad Code."""

from esnaad.exceptions.base import EsnaadError


class LLMError(EsnaadError):
    """Base exception for LLM API errors."""

    def __init__(
        self,
        message: str,
        recoverable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, recoverable=recoverable)
        self.status_code = status_code
        if status_code:
            self.details["status_code"] = status_code


class LLMConnectionError(LLMError):
    """
    Failed to connect to LLM API.

    Raised when the HTTP connection to the LLM API cannot be established.
    """

    def __init__(self, message: str, url: str | None = None) -> None:
        super().__init__(message, recoverable=True)
        self.url = url
        if url:
            self.details["url"] = url


class LLMRateLimitError(LLMError):
    """
    Rate limited by LLM API.

    Raised when the API returns a 429 status code.
    """

    def __init__(
        self,
        message: str = "Rate limited by LLM API",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, recoverable=True, status_code=429)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class LLMResponseError(LLMError):
    """
    Invalid or unexpected response from LLM API.

    Raised when the API response cannot be parsed or is malformed.
    """

    def __init__(
        self,
        message: str,
        response_text: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, recoverable=False, status_code=status_code)
        self.response_text = response_text
        if response_text:
            # Truncate long responses
            self.details["response_preview"] = response_text[:500]


class LLMTimeoutError(LLMError):
    """
    LLM API request timed out.

    Raised when the request exceeds the configured timeout.
    """

    def __init__(
        self,
        message: str = "LLM API request timed out",
        timeout: float | None = None,
    ) -> None:
        super().__init__(message, recoverable=True)
        self.timeout = timeout
        if timeout:
            self.details["timeout"] = timeout
