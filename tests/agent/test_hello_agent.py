"""Unit tests for :mod:`azure_foundry.agent.hello_agent`."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from azure_foundry.agent import hello_agent


@pytest.fixture()
def mocks(monkeypatch):
    """Replace the Foundry client, credential, and agent with mocks."""
    client_cls = MagicMock(name="FoundryChatClient")
    credential_cls = MagicMock(name="AzureCliCredential")
    agent_cls = MagicMock(name="Agent")
    monkeypatch.setattr(hello_agent, "FoundryChatClient", client_cls)
    monkeypatch.setattr(hello_agent, "AzureCliCredential", credential_cls)
    monkeypatch.setattr(hello_agent, "Agent", agent_cls)
    return client_cls, credential_cls, agent_cls


def test_create_agent_builds_client_from_config(
    mocks, write_config, config_data
):
    client_cls, credential_cls, _ = mocks
    write_config(config_data)

    hello_agent.create_agent()

    client_cls.assert_called_once_with(
        project_endpoint=config_data["foundry"]["project_endpoint"],
        model=config_data["foundry"]["model"],
        credential=credential_cls.return_value,
    )


def test_create_agent_returns_named_agent(mocks, write_config, config_data):
    client_cls, _, agent_cls = mocks
    write_config(config_data)

    agent = hello_agent.create_agent()

    assert agent is agent_cls.return_value
    agent_cls.assert_called_once_with(
        client=client_cls.return_value,
        name=hello_agent.AGENT_NAME,
        instructions=config_data["foundry"]["instructions"],
    )


@pytest.fixture()
def agent_reply(monkeypatch):
    """Make ``create_agent`` return a mock agent replying with fixed text."""
    reply = "Hi there!"
    agent = MagicMock(name="agent")
    agent.run = AsyncMock(return_value=MagicMock(text=reply))
    monkeypatch.setattr(hello_agent, "create_agent", lambda: agent)
    return agent, reply


async def test_ask_returns_reply_text(agent_reply):
    agent, reply = agent_reply

    assert await hello_agent.ask("Hello") == reply
    agent.run.assert_awaited_once_with("Hello")


@pytest.mark.parametrize(
    ("argv", "expected_prompt"),
    [
        ([], hello_agent.DEFAULT_PROMPT),
        (["What", "is", "Foundry?"], "What is Foundry?"),
    ],
)
def test_main_prints_reply(
    agent_reply, write_config, config_data, capsys, argv, expected_prompt
):
    agent, reply = agent_reply
    write_config(config_data)

    hello_agent.main(argv)

    agent.run.assert_awaited_once_with(expected_prompt)
    assert capsys.readouterr().out == f"{reply}\n"
