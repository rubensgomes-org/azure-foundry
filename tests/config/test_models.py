"""Unit tests for :mod:`azure_foundry.config.models`."""

import pytest
from pydantic import ValidationError

from azure_foundry.config.models import AppConfig


def test_app_config_parses_valid_mapping(config_data):
    result = AppConfig.model_validate(config_data)
    assert result.foundry.model == "test-model"
    assert result.logging["version"] == 1


@pytest.mark.parametrize("key", ["project_endpoint", "model"])
def test_foundry_empty_value_raises(config_data, key):
    config_data["foundry"][key] = ""
    with pytest.raises(ValidationError, match=key):
        AppConfig.model_validate(config_data)


@pytest.mark.parametrize("key", ["project_endpoint", "model", "instructions"])
def test_foundry_missing_value_raises(config_data, key):
    del config_data["foundry"][key]
    with pytest.raises(ValidationError, match=key):
        AppConfig.model_validate(config_data)


@pytest.mark.parametrize("section", ["foundry", "logging"])
def test_missing_section_raises(config_data, section):
    del config_data[section]
    with pytest.raises(ValidationError, match=section):
        AppConfig.model_validate(config_data)
