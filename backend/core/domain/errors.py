"""Domain error types."""

import datetime


class NonexistentLocalTimeError(ValueError):
    """Raised when a local datetime falls in a daylight saving spring-forward transition gap."""


class DepartureOutOfWindowError(ValueError):
    """Raised when departure time falls outside the allowed scheduling window."""

    def __init__(
        self,
        message: str,
        allowed_from: datetime.datetime,
        allowed_to: datetime.datetime,
    ) -> None:
        super().__init__(message)
        self.allowed_from = allowed_from
        self.allowed_to = allowed_to


class BeyondForecastHorizonError(ValueError):
    """Raised when trip times extend beyond the available forecast horizon."""

    def __init__(
        self,
        message: str,
        last_forecast_time: datetime.datetime,
    ) -> None:
        super().__init__(message)
        self.last_forecast_time = last_forecast_time
