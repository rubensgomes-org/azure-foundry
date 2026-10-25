"""Shared fixtures for the agent client tests."""

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock

import httpx
import pytest
from pytest_mock import MockerFixture

AGENT_NAME = "test-agent"
CONVERSATION_ID = "conv-123"
REQUEST = httpx.Request("POST", "https://test.services.ai.azure.com")


@dataclass(frozen=True)
class AgentMocks:
    client_mgr: MagicMock
    user_input: MagicMock


def make_response(output_text: str, output: list | None = None) -> MagicMock:
    """Build a mock Foundry Response."""
    return MagicMock(output=output or [], output_text=output_text)


@pytest.fixture
def agent_mocks(
    mocker: MockerFixture,
) -> Callable[[str, list], AgentMocks]:
    """
    Return a factory that patches the config loader, logging setup,
    AIClientManager and input() in the given agent_client module.
    """

    def _patch(module: str, user_inputs: list) -> AgentMocks:
        app_config = mocker.MagicMock()
        app_config.foundry.agent_name = AGENT_NAME
        mocker.patch(f"{module}.aload_config", return_value=app_config)
        mocker.patch(f"{module}.configure_logging")

        client_mgr = mocker.MagicMock()
        client_mgr.initialize = mocker.AsyncMock()
        client_mgr.close = mocker.AsyncMock()
        client_mgr.save_user_msg_to_conversation = mocker.AsyncMock()
        client_mgr.save_items_to_conversation = mocker.AsyncMock()
        client_mgr.debuglog_conversation = mocker.AsyncMock()
        client_mgr.post_conversation_to_agent = mocker.AsyncMock()
        client_mgr.openai_client.conversations.create = mocker.AsyncMock(
            return_value=mocker.MagicMock(id=CONVERSATION_ID)
        )
        mocker.patch(f"{module}.AIClientManager", return_value=client_mgr)

        user_input = mocker.patch("builtins.input", side_effect=user_inputs)
        return AgentMocks(client_mgr=client_mgr, user_input=user_input)

    return _patch
