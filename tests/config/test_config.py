"""Unit tests for :mod:`azure_foundry.config.config`."""

# Tests exercise the private path resolver directly.
# pylint: disable=protected-access

import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from azure_foundry.config import config
from tests.conftest import CONFIG_ENV

TEST_LOGGER = "azure_foundry.test"


@pytest.fixture()
def test_logger():
    """Return the test logger; restore its level afterwards."""
    logger = logging.getLogger(TEST_LOGGER)
    level = logger.level
    yield logger
    logger.setLevel(level)


def test_resolve_config_path_uses_env_var(monkeypatch, tmp_path):
    path = tmp_path / "custom.yaml"
    monkeypatch.setenv(CONFIG_ENV, str(path))
    assert config._resolve_config_path() == path


@pytest.mark.parametrize("value", [None, ""])
def test_resolve_config_path_defaults_to_bundled(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(CONFIG_ENV, raising=False)
    else:
        monkeypatch.setenv(CONFIG_ENV, value)
    path = config._resolve_config_path()
    assert path == Path(config.__file__).with_name("config.yaml")
    assert path.is_file()


def test_get_config_loads_bundled_config(monkeypatch):
    monkeypatch.delenv(CONFIG_ENV, raising=False)
    assert config.get_config().foundry.model


def test_get_config_reads_env_path(write_config, config_data):
    write_config(config_data)
    assert config.get_config().foundry.model == "test-model"


def test_get_config_is_cached(write_config, config_data):
    path = write_config(config_data)
    first = config.get_config()
    path.unlink()
    assert config.get_config() is first


def test_get_config_invalid_file_raises(write_config, config_data):
    del config_data["foundry"]
    write_config(config_data)
    with pytest.raises(ValidationError, match="foundry"):
        config.get_config()


def test_get_config_missing_file_raises(monkeypatch, tmp_path):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path / "missing.yaml"))
    with pytest.raises(FileNotFoundError):
        config.get_config()


def test_configure_logging_applies_config(
    write_config, config_data, test_logger
):
    test_logger.setLevel(logging.DEBUG)
    write_config(config_data)
    config.configure_logging()
    assert test_logger.level == logging.WARNING
