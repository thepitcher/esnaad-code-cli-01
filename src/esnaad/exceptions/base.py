"""Base exception classes for Esnaad Code."""


class EsnaadError(Exception):
    """
    Base exception for all Esnaad errors.

    Attributes:
        message: Human-readable error message
        recoverable: Whether the error can be recovered from
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        recoverable: bool = False,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.recoverable = recoverable
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, recoverable={self.recoverable})"


class ConfigurationError(EsnaadError):
    """
    Configuration-related errors.

    Raised when there are issues with settings, environment variables,
    or configuration files.
    """

    def __init__(self, message: str, config_key: str | None = None) -> None:
        super().__init__(message, recoverable=False)
        self.config_key = config_key
        if config_key:
            self.details["config_key"] = config_key
