"""Tests for azure_foundry.agent_basic.agent_client."""

# Tests call the module's private helpers directly.
# pylint: disable=protected-access

import logging
from collections.abc import Callable

import httpx2
import pytest
from openai import APIError, APIStatusError
from pytest_mock import MockerFixture

from azure_foundry.agent_basic import agent_client
from tests.conftest import (
    AGENT_NAME,
    CONVERSATION_ID,
    REQUEST,
    AgentMocks,
    make_response,
)

MODULE = "azure_foundry.agent_basic.agent_client"
USER_MSG = "Hello, agent"
AGENT_REPLY = "Hi there"
ERROR_BODY = {"message": "Server returned 424", "type": "connector_error"}

AgentMocksFactory = Callable[[str, list], AgentMocks]


def test_log_api_error_logs_status_code_and_body_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = APIStatusError(
        "bad request",
        response=httpx2.Response(400, request=REQUEST),
        body=ERROR_BODY,
    )

    with caplog.at_level(logging.ERROR):
        agent_client._log_api_error(error)

    assert (
        "status_code=400, type=connector_error, "
        "message=Server returned 424" in caplog.text
    )


def test_log_api_error_without_status_uses_error_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = APIError("connection failed", REQUEST, body=None)

    with caplog.at_level(logging.ERROR):
        agent_client._log_api_error(error)

    assert (
        "status_code=None, type=None, message=connection failed" in caplog.text
    )


async def test_main_posts_user_message_and_prints_reply(
    agent_mocks: AgentMocksFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    mocks = agent_mocks(MODULE, ["  ", USER_MSG, "QUIT"])
    client_mgr = mocks.client_mgr
    client_mgr.post_conversation_to_agent.return_value = make_response(
        AGENT_REPLY
    )

    await agent_client.main()

    client_mgr.save_user_msg_to_conversation.assert_awaited_once_with(
        CONVERSATION_ID, USER_MSG
    )
    client_mgr.post_conversation_to_agent.assert_awaited_once_with(
        conversation_id=CONVERSATION_ID, server_agent_name=AGENT_NAME
    )
    assert f"Agent response: {AGENT_REPLY}" in capsys.readouterr().out
    client_mgr.close.assert_awaited_once()


async def test_main_ends_conversation_on_eof(
    agent_mocks: AgentMocksFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    mocks = agent_mocks(MODULE, [EOFError])

    await agent_client.main()

    assert "Ending conversation..." in capsys.readouterr().out
    mocks.client_mgr.close.assert_awaited_once()


async def test_main_logs_api_error_and_closes_client(
    agent_mocks: AgentMocksFactory, caplog: pytest.LogCaptureFixture
) -> None:
    mocks = agent_mocks(MODULE, [USER_MSG])
    mocks.client_mgr.post_conversation_to_agent.side_effect = APIError(
        "agent failed", REQUEST, body=ERROR_BODY
    )

    with caplog.at_level(logging.ERROR):
        await agent_client.main()

    assert "message=Server returned 424" in caplog.text
    mocks.client_mgr.close.assert_awaited_once()


def test_run_executes_main(mocker: MockerFixture) -> None:
    main = mocker.patch(f"{MODULE}.main", new_callable=mocker.AsyncMock)

    agent_client.run()

    main.assert_awaited_once()


def test_run_handles_keyboard_interrupt(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    mocker.patch(f"{MODULE}.main", side_effect=KeyboardInterrupt)

    agent_client.run()

    assert "Program terminated." in capsys.readouterr().out
