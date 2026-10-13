"""Shared HTTP client request execution and error mapping for external providers."""

from collections.abc import Callable
from typing import Any

import httpx

from core.providers.base import (
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)


def execute_request_with_retry(
    client: httpx.Client,
    url: str,
    params: dict[str, Any] | None = None,
    service_label: str = "External",
    sleep_fn: Callable[[float], None] | None = None,
    check_200: bool = False,
) -> httpx.Response:
    """Send HTTP GET request with at most one retry on timeout, 429, or 5xx.

    Maps httpx errors and HTTP status codes to domain Provider exceptions.
    Never includes raw URLs or API keys in exception messages.
    """
    prefix = service_label if service_label.endswith("provider") else f"{service_label} provider"
    req_label = service_label if service_label.endswith("provider") else service_label
    for attempt in range(2):
        try:
            resp = client.get(url, params=params)
        except httpx.TimeoutException:
            if attempt == 0 and sleep_fn:
                sleep_fn(0.3)
                continue
            raise ProviderTimeout(f"{req_label} request timed out") from None
        except httpx.RequestError:
            if attempt == 0 and sleep_fn:
                sleep_fn(0.3)
                continue
            raise ProviderUnavailable(f"{prefix} is currently unavailable") from None

        if resp.status_code == 429:
            if attempt == 0 and sleep_fn:
                sleep_fn(0.3)
                continue
            raise ProviderRateLimited(f"{prefix} rate limit exceeded")

        if resp.status_code >= 500:
            if attempt == 0 and sleep_fn:
                sleep_fn(0.3)
                continue
            raise ProviderUnavailable(f"{prefix} is currently unavailable")

        if resp.status_code in (401, 403):
            raise ProviderUnavailable(f"{prefix} authentication failed")

        if check_200 and resp.status_code != 200:
            raise ProviderBadResponse(
                f"{prefix} returned error HTTP {resp.status_code}"
            )

        return resp
