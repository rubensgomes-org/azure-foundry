"""A very basic hello agent."""

import asyncio
import logging
import sys

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

from azure_foundry.config.config import configure_logging, get_config

AGENT_NAME = "HelloAgent"
DEFAULT_PROMPT = "Hello! Who are you?"

logger = logging.getLogger(__name__)


def create_agent() -> Agent:
    """Return a Foundry-backed hello agent built from config.yaml."""
    foundry = get_config().foundry
    logger.debug(
        "Creating %s with Foundry endpoint %s",
        AGENT_NAME,
        foundry.project_endpoint,
    )
    return Agent(
        client=FoundryChatClient(
            project_endpoint=foundry.project_endpoint,
            model=foundry.model,
            credential=AzureCliCredential(),
        ),
        name=AGENT_NAME,
        instructions=foundry.instructions,
    )


async def ask(prompt: str) -> str:
    """Send ``prompt`` to a new hello agent and return its reply text."""
    agent = create_agent()
    logger.debug("Sending prompt to %s: %s", AGENT_NAME, prompt)
    response = await agent.run(prompt)
    logger.debug("Received reply from %s", AGENT_NAME)
    return response.text


def main(argv: list[str] | None = None) -> None:
    """Ask the agent the prompt in ``argv`` and print the reply."""
    configure_logging()
    args = sys.argv[1:] if argv is None else argv
    prompt = " ".join(args) or DEFAULT_PROMPT
    print(asyncio.run(ask(prompt)))
