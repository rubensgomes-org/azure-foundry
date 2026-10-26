"""Tests for azure_foundry.agent_functions.agent."""

# Tests call the module's private helpers directly.
# pylint: disable=protected-access

import json
import logging
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import httpx2
import pytest
from openai import APIError, APIStatusError
from pytest_mock import MockerFixture

from azure_foundry.agent_functions import agent
from azure_foundry.agent_functions.functions import calculate_observation_cost
from tests.conftest import (
    AGENT_NAME,
    CONVERSATION_ID,
    REQUEST,
    AgentMocks,
    make_response,
)

MODULE = "azure_foundry.agent_functions.agent"
USER_MSG = "How much is 2 hours on an advanced telescope?"
AGENT_REPLY = "It costs $420."
ERROR_BODY = {"message": "Server returned 424", "type": "connector_error"}
CALL_ID = "call-123"
COST_ARGS = {"telescope_tier": "advanced", "hours": 2, "priority": "high"}

AgentMocksFactory = Callable[[str, list], AgentMocks]


def _function_call(name: str, arguments: dict) -> MagicMock:
    call = MagicMock(
        type="function_call", call_id=CALL_ID, arguments=json.dumps(arguments)
    )
    # "name" is a reserved MagicMock constructor argument.
    call.name = name
    return call


def _patch_agent(
    agent_mocks: AgentMocksFactory, mocker: MockerFixture, user_inputs: list
) -> AgentMocks:
    mocks = agent_mocks(MODULE, user_inputs)
    mocks.client_mgr.create_agent = mocker.AsyncMock(return_value=MagicMock())
    mocks.client_mgr.delete_agent = mocker.AsyncMock()
    return mocks


def test_list_function_tools_defines_every_agent_function() -> None:
    names = {tool["name"] for tool in agent._list_function_tools()}

    assert names == set(agent._AGENT_FUNCTIONS)


def test_run_function_calls_returns_function_outputs() -> None:
    items: list[Any] = [
        MagicMock(type="message"),
        _function_call("calculate_observation_cost", COST_ARGS),
    ]

    outputs = agent._run_function_calls(items)

    assert outputs == [
        {
            "type": "function_call_output",
            "call_id": CALL_ID,
            "output": calculate_observation_cost("advanced", 2, "high"),
        }
    ]


def test_log_api_error_logs_status_code_and_body_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = APIStatusError(
        "bad request",
        response=httpx2.Response(400, request=REQUEST),
        body=ERROR_BODY,
    )

    with caplog.at_level(logging.ERROR):
        agent._log_api_error(error)

    assert (
        "status_code=400, type=connector_error, "
        "message=Server returned 424" in caplog.text
    )


def test_log_api_error_without_status_uses_error_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = APIError("connection failed", REQUEST, body=None)

    with caplog.at_level(logging.ERROR):
        agent._log_api_error(error)

    assert (
        "status_code=None, type=None, message=connection failed" in caplog.text
    )


async def test_main_posts_user_message_and_prints_reply(
    agent_mocks: AgentMocksFactory,
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mocks = _patch_agent(agent_mocks, mocker, ["  ", USER_MSG, "quit"])
    client_mgr = mocks.client_mgr
    client_mgr.post_conversation_to_agent.return_value = make_response(
        AGENT_REPLY
    )

    await agent.main()

    client_mgr.save_user_msg_to_conversation.assert_awaited_once_with(
        CONVERSATION_ID, USER_MSG
    )
    client_mgr.post_conversation_to_agent.assert_awaited_once_with(
        conversation_id=CONVERSATION_ID, server_agent_name=AGENT_NAME
    )
    assert f"Agent response: {AGENT_REPLY}" in capsys.readouterr().out
    client_mgr.delete_agent.assert_awaited_once()
    client_mgr.close.assert_awaited_once()


async def test_main_posts_function_outputs_back_to_agent(
    agent_mocks: AgentMocksFactory,
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mocks = _patch_agent(agent_mocks, mocker, [USER_MSG, "quit"])
    client_mgr = mocks.client_mgr
    client_mgr.post_conversation_to_agent.side_effect = [
        make_response(
            "", [_function_call("calculate_observation_cost", COST_ARGS)]
        ),
        make_response(AGENT_REPLY),
    ]

    await agent.main()

    second_call = client_mgr.post_conversation_to_agent.await_args_list[1]
    assert second_call.kwargs["agent_input"][0]["call_id"] == CALL_ID
    assert f"Agent response: {AGENT_REPLY}" in capsys.readouterr().out


async def test_main_ends_conversation_on_eof(
    agent_mocks: AgentMocksFactory,
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mocks = _patch_agent(agent_mocks, mocker, [EOFError])

    await agent.main()

    assert "Ending conversation..." in capsys.readouterr().out
    mocks.client_mgr.close.assert_awaited_once()


async def test_main_logs_api_error_and_closes_client(
    agent_mocks: AgentMocksFactory,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocks = _patch_agent(agent_mocks, mocker, [USER_MSG])
    mocks.client_mgr.post_conversation_to_agent.side_effect = APIError(
        "agent failed", REQUEST, body=ERROR_BODY
    )

    with caplog.at_level(logging.ERROR):
        await agent.main()

    assert "message=Server returned 424" in caplog.text
    mocks.client_mgr.close.assert_awaited_once()


def test_run_executes_main(mocker: MockerFixture) -> None:
    main = mocker.patch(f"{MODULE}.main", new_callable=mocker.AsyncMock)

    agent.run()

    main.assert_awaited_once()


def test_run_handles_keyboard_interrupt(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    mocker.patch(f"{MODULE}.main", side_effect=KeyboardInterrupt)

    agent.run()

    assert "Program terminated." in capsys.readouterr().out
