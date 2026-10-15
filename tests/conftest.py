"""Shared pytest fixtures."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from azure_foundry.config import config

CONFIG_ENV = "AZUREFOUNDRY_CONFIG"


@pytest.fixture(autouse=True)
def _clear_config_cache():
    """Isolate tests from the ``get_config`` cache."""
    config.get_config.cache_clear()
    yield
    config.get_config.cache_clear()


@pytest.fixture()
def config_data() -> dict[str, Any]:
    """Return a valid config.yaml mapping."""
    return {
        "foundry": {
            "project_endpoint": "https://aif.example.com/api/projects/p",
            "model": "test-model",
            "instructions": "Test instructions.",
        },
        "logging": {
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {"azure_foundry.test": {"level": "WARNING"}},
        },
    }


@pytest.fixture()
def write_config(tmp_path, monkeypatch):
    """Return a function that writes a config file and points to it."""

    def _write(data: Any) -> Path:
        path = tmp_path / "config.yaml"
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        monkeypatch.setenv(CONFIG_ENV, str(path))
        return path

    return _write
