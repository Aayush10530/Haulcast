"""Tests for settings security and environment configuration."""

import importlib
from collections.abc import Generator

import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture(autouse=True)
def restore_settings_after_test(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Ensure config.settings is restored to its baseline state after each test."""
    yield
    monkeypatch.setenv("DJANGO_DEBUG", "True")
    import config.settings as settings

    importlib.reload(settings)


def test_debug_false_with_missing_secret_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """When DEBUG is False and key is missing, settings raises ImproperlyConfigured."""
    import config.settings as settings

    monkeypatch.setenv("DJANGO_DEBUG", "False")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY must be set"):
        importlib.reload(settings)


def test_debug_false_with_insecure_default_secret_key_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When DEBUG is False and key starts with django-insecure, it must raise."""
    import config.settings as settings

    monkeypatch.setenv("DJANGO_DEBUG", "False")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "django-insecure-test-key")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY must be set"):
        importlib.reload(settings)


def test_debug_true_works_without_explicit_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """When DEBUG is True and key is missing, settings loads with dev placeholder."""
    import config.settings as settings

    monkeypatch.setenv("DJANGO_DEBUG", "True")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)

    reloaded = importlib.reload(settings)
    assert reloaded.DEBUG is True
    assert reloaded.SECRET_KEY.startswith("django-insecure")
