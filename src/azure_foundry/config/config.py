"""Configuration helpers — loads config.yaml and configures logging."""

import functools
import logging
import logging.config
import os
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from azure_foundry.config.models import AppConfig

logger = logging.getLogger(__name__)


def _resolve_config_path() -> Path:
    """Return the config.yaml path.

    Resolution order:

    1. The ``AZUREFOUNDRY_CONFIG`` environment variable, when set.
    2. The ``config.yaml`` bundled inside the
       ``azure_foundry.config`` package.

    Returns:
        The resolved path to config.yaml.
    """
    env_path = os.environ.get("AZUREFOUNDRY_CONFIG")
    if env_path:
        return Path(env_path)
    return Path(str(files("azure_foundry.config").joinpath("config.yaml")))


def _load_config(path: Path) -> AppConfig:
    """Parse and validate the config file at ``path``.

    Raises:
        pydantic.ValidationError: If the file does not match the models.
    """
    return AppConfig.model_validate(_read_yaml(path))


def _read_yaml(path: Path) -> dict[str, Any]:
    """Return the YAML mapping in the file at ``path``."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


################################################################################
# The following Public APIs define where and how the config is loaded.         #
################################################################################


@functools.cache
def get_config() -> AppConfig:
    """Return the application config, loaded once on first call."""
    return _load_config(_resolve_config_path())


def configure_logging() -> None:
    """Apply config.yaml logging configuration."""
    logging.config.dictConfig(get_config().logging)
    logger.debug("Loaded logging config from %s", _resolve_config_path())
