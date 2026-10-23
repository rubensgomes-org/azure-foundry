import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from ai_utils_lib.config import aload_config
from ai_utils_lib.config_models import AppConfig
from ai_utils_lib.file.file_config import configure_logging
from ai_utils_lib.foundry.project_clients import get_ai_project_clients
from azure.ai.projects.models import AgentDetails
from openai.types.conversations import Conversation

CONFIG_PATH = Path(__file__).with_name("config.yaml")

logger = logging.getLogger("azure_foundry.agent_foundry_iq")


async def main() -> None:
    #################################################################
    # 1. Load app configuration
    app_config: AppConfig = await aload_config(CONFIG_PATH)
    configure_logging(app_config)
    logger.debug(
        "app_config: %s",
        app_config.model_dump_json(indent=2, exclude={"logging"}),
    )

    #################################################################
    # 2. Create:
    #   2.1 DefaultAzureCredential
    #   2.2 AIProjectClient with endpoint
    # 3. Get an authenticated AsyncOpenAI client from the openai package.
    async with get_ai_project_clients(app_config.foundry.project_endpoint) as (
        project_client,
        openai_client,
    ):

        #################################################################
        # 4. Get the agent by name
        agent: AgentDetails = await project_client.agents.get(
            agent_name=app_config.foundry.agent_name
        )
        agent_json: dict[str, Any] = agent.as_dict()
        logger.debug("agent: %s", json.dumps(agent_json, indent=2, default=str))

        #################################################################
        # 5. Create a new conversation
        conversation: Conversation = await openai_client.conversations.create(
            items=[]
        )
        logger.debug("conversation: %s", conversation.model_dump_json(indent=2))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
