"""Home Assistant fixtures with project integration loading enabled."""

from pathlib import Path

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations, monkeypatch):
    import custom_components

    monkeypatch.setattr(
        custom_components, "__path__", [str(Path(__file__).parents[1] / "custom_components")]
    )
    yield
