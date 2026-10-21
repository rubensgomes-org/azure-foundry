"""Pydantic models for the config.yaml sections."""

from typing import Any

from pydantic import BaseModel, Field


class FoundryConfig(BaseModel):
    """The ``foundry`` section of config.yaml."""

    project_endpoint: str = Field(min_length=1)
    model: str = Field(min_length=1)
    instructions: str


class AppConfig(BaseModel):
    """The full config.yaml; ``logging`` is a ``dictConfig`` mapping."""

    foundry: FoundryConfig
    logging: dict[str, Any]

