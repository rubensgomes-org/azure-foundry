"""Tests for azure_foundry.agent_foundry_iq.agent_client."""

# Tests call the module's private helpers directly.
# pylint: disable=protected-access

import logging
from collections.abc import Callable
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIError, APIStatusError
from pytest_mock import MockerFixture

from azure_foundry.agent_foundry_iq import agent_client
from tests.conftest import (
    AGENT_NAME,
    CONVERSATION_ID,
    REQUEST,
    AgentMocks,
    make_response,
)

MODULE = "azure_foundry.agent_foundry_iq.agent_client"
USER_MSG = "Which tents do you sell?"
AGENT_REPLY = "We sell the TrailMaster tent."
ERROR_BODY = {"message": "Server returned 424", "type": "connector_error"}
APPROVAL_ID = "apr-123"
TOOL_NAME = "knowledge_base_retrieve"
SERVER_LABEL = "kb-test"

AgentMocksFactory = Callable[[str, list], AgentMocks]


def _approval_request(arguments: str | None) -> MagicMock:
    request = MagicMock(
        type="mcp_approval_request",
        id=APPROVAL_ID,
        server_label=SERVER_LABEL,
        arguments=arguments,
    )
    # "name" is a reserved MagicMock constructor argument.
    request.name = TOOL_NAME
    return request


def _approval_response(approved: bool) -> dict:
    return {
        "type": "mcp_approval_response",
        "approval_request_id": APPROVAL_ID,
        "approve": approved,
    }


@pytest.mark.parametrize(
    ("answer", "approved"),
    [("yes", True), (" Y ", True), ("no", False), ("", False)],
)
async def test_process_approvals_returns_user_decision(
    mocker: MockerFixture, answer: str, approved: bool
) -> None:
    mocker.patch("builtins.input", return_value=answer)
    response = make_response("", [_approval_request('{"queries": ["x"]}')])

    approval_items = await agent_client._process_approvals(response)

    assert approval_items == [_approval_response(approved)]


@pytest.mark.parametrize("arguments", ["not json", None])
async def test_process_approvals_prints_unparsable_arguments_as_is(
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
    arguments: str | None,
) -> None:
    mocker.patch("builtins.input", return_value="yes")
    response = make_response("", [_approval_request(arguments)])

    await agent_client._process_approvals(response)

    assert f"Arguments: {arguments}" in capsys.readouterr().out


async def test_process_approvals_ignores_other_output_items(
    mocker: MockerFixture,
) -> None:
    user_input = mocker.patch("builtins.input")
    response = make_response("", [MagicMock(type="message")])

    assert not await agent_client._process_approvals(response)
    user_input.assert_not_called()


def test_log_api_error_logs_status_code_and_body_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = APIStatusError(
        "bad request",
        response=httpx.Response(400, request=REQUEST),
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
    mocks = agent_mocks(MODULE, ["  ", USER_MSG, "quit"])
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
    client_mgr.save_items_to_conversation.assert_not_awaited()
    assert f"Agent response: {AGENT_REPLY}" in capsys.readouterr().out
    client_mgr.close.assert_awaited_once()


async def test_main_saves_approvals_and_reposts_conversation(
    agent_mocks: AgentMocksFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    mocks = agent_mocks(MODULE, [USER_MSG, "yes", "quit"])
    client_mgr = mocks.client_mgr
    client_mgr.post_conversation_to_agent.side_effect = [
        make_response("", [_approval_request('{"queries": ["tents"]}')]),
        make_response(AGENT_REPLY),
    ]

    await agent_client.main()

    client_mgr.save_items_to_conversation.assert_awaited_once_with(
        conversation_id=CONVERSATION_ID, items=[_approval_response(True)]
    )
    assert client_mgr.post_conversation_to_agent.await_count == 2
    assert f"Agent response: {AGENT_REPLY}" in capsys.readouterr().out


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
