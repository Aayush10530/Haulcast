"""Unit tests for TomTom geocoding provider and CachedGeocoding wrapper."""

from collections.abc import Generator
from typing import Any

import httpx
import pytest
import respx

from core.domain.types import Coordinate, Place
from core.infra.cache import InMemoryTTLCache
from core.providers.base import (
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from core.providers.geocoding_tomtom import CachedGeocoding, TomTomGeocodingProvider
from core.tests.fakes import FakeGeocodingProvider

BASE_SEARCH_URL = "https://api.tomtom.com/search/2/search/"


@pytest.fixture(scope="module")
def mock_client() -> Generator[httpx.Client]:
    with httpx.Client() as client:
        yield client


def test_init_validation() -> None:
    with pytest.raises(ValueError, match="api_key cannot be empty"):
        TomTomGeocodingProvider(api_key="")
    with pytest.raises(ValueError, match="api_key cannot be empty"):
        TomTomGeocodingProvider(api_key="   ")


def test_search_empty_or_whitespace_returns_empty_list() -> None:
    provider = TomTomGeocodingProvider(api_key="test-key")
    assert provider.search("") == []
    assert provider.search("   ") == []


@respx.mock(assert_all_mocked=True)
def test_successful_geocoding_search(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="test-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )

    route_mock = respx_mock.get(
        url__startswith=f"{BASE_SEARCH_URL}Dallas%2C%20TX.json",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "summary": {"query": "Dallas, TX", "numResults": 2},
                "results": [
                    {
                        "id": "USA/GEO/1",
                        "address": {"freeformAddress": "Dallas, TX"},
                        "position": {"lat": 32.7767, "lon": -96.7970},
                    },
                    {
                        "id": "USA/GEO/2",
                        "poi": {"name": "Dallas Downtown"},
                        "position": {"lat": 32.7800, "lon": -96.8000},
                    },
                ],
            },
        )
    )

    places = provider.search("Dallas, TX", limit=2)
    assert len(places) == 2
    assert places[0].label == "Dallas, TX"
    assert places[0].coordinate == Coordinate(32.7767, -96.7970)
    assert places[0].id == "USA/GEO/1"

    assert places[1].label == "Dallas Downtown"
    assert places[1].coordinate == Coordinate(32.7800, -96.8000)
    assert places[1].id == "USA/GEO/2"

    assert route_mock.called
    req = route_mock.calls.last.request
    assert req.url.params["key"] == "test-key"
    assert req.url.params["typeahead"] == "true"
    assert req.url.params["countrySet"] == "US"
    assert req.url.params["limit"] == "2"


@respx.mock(assert_all_mocked=True)
def test_label_fallback_to_query_when_address_and_poi_empty(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="test-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "position": {"lat": 39.7392, "lon": -104.9903},
                    }
                ]
            },
        )
    )
    places = provider.search("Denver", limit=1)
    assert len(places) == 1
    assert places[0].label == "Denver"
    assert places[0].coordinate == Coordinate(39.7392, -104.9903)
    assert places[0].id == "39.73920,-104.99030"


@respx.mock(assert_all_mocked=True)
def test_timeout_retried_then_raises_provider_timeout(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        side_effect=httpx.TimeoutException("timeout"),
    )

    with pytest.raises(ProviderTimeout) as exc_info:
        provider.search("Denver")

    assert "secret-key" not in str(exc_info.value)
    assert len(fake_sleeps) == 1
    assert fake_sleeps[0] == 0.3


@respx.mock(assert_all_mocked=True)
def test_request_error_retried_then_raises_provider_unavailable(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        side_effect=httpx.NetworkError("connection reset"),
    )

    with pytest.raises(ProviderUnavailable):
        provider.search("Denver")

    assert len(fake_sleeps) == 1


@respx.mock(assert_all_mocked=True)
def test_rate_limited_429_retried_then_raises(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        return_value=httpx.Response(429)
    )

    with pytest.raises(ProviderRateLimited):
        provider.search("Denver")

    assert len(fake_sleeps) == 1


@respx.mock(assert_all_mocked=True)
def test_server_error_500_retried_then_raises(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        return_value=httpx.Response(500)
    )

    with pytest.raises(ProviderUnavailable):
        provider.search("Denver")

    assert len(fake_sleeps) == 1


@pytest.mark.parametrize("status_code", [401, 403])
@respx.mock(assert_all_mocked=True)
def test_auth_error_raises_immediately_without_retry(
    status_code: int, respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key",
        client=mock_client,
        sleep=fake_sleeps.append,
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        return_value=httpx.Response(status_code)
    )

    with pytest.raises(ProviderUnavailable, match="authentication failed"):
        provider.search("Denver")

    assert len(fake_sleeps) == 0


@respx.mock(assert_all_mocked=True)
def test_bad_status_code_400_raises_provider_bad_response(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key", client=mock_client, sleep=fake_sleeps.append
    )
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        return_value=httpx.Response(400)
    )

    with pytest.raises(ProviderBadResponse, match="error response"):
        provider.search("Denver")


@pytest.mark.parametrize(
    "payload",
    [
        "non-json",
        [1, 2, 3],
        {"results": "not-a-list"},
        {"results": ["not-a-dict"]},
        {"results": [{"position": "not-a-dict"}]},
        {"results": [{"position": {"lat": "invalid", "lon": 10}}]},
    ],
)
@respx.mock(assert_all_mocked=True)
def test_malformed_payloads_raise_provider_bad_response(
    payload: Any, respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    fake_sleeps: list[float] = []
    provider = TomTomGeocodingProvider(
        api_key="secret-key", client=mock_client, sleep=fake_sleeps.append
    )
    if isinstance(payload, str):
        respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
            return_value=httpx.Response(200, text=payload)
        )
    else:
        respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
            return_value=httpx.Response(200, json=payload)
        )

    with pytest.raises(ProviderBadResponse):
        provider.search("Denver")


@respx.mock(assert_all_mocked=True)
def test_default_client_execution(respx_mock: respx.MockRouter) -> None:
    provider = TomTomGeocodingProvider(api_key="secret-key", client=None)
    respx_mock.get(url__startswith=f"{BASE_SEARCH_URL}Denver.json").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    places = provider.search("Denver")
    assert places == []


def test_cached_geocoding_wrapper() -> None:
    cache = InMemoryTTLCache()
    fake = FakeGeocodingProvider(
        places_by_query={
            "Denver": [
                Place("Denver, CO", Coordinate(39.7392, -104.9903), id="1"),
                Place("Denver Airport", Coordinate(39.8561, -104.6737), id="2"),
            ]
        }
    )
    cached_wrapper = CachedGeocoding(provider=fake, cache=cache, ttl_seconds=86400)

    # First call - cache miss
    res1 = cached_wrapper.search("Denver", limit=2)
    assert len(res1) == 2
    assert len(fake.calls) == 1

    # Second call with mixed case and whitespace - cache hit
    res2 = cached_wrapper.search("  dEnVeR  ", limit=1)
    assert len(res2) == 1
    assert res2[0].label == "Denver, CO"
    assert len(fake.calls) == 1  # No additional provider call
