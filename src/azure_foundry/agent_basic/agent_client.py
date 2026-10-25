"""Interactive console client for a basic server-side agent."""

import asyncio
import logging
from pathlib import Path

from ai_utils_lib.config import aload_config
from ai_utils_lib.config_models import AppConfig
from ai_utils_lib.file.file_config import configure_logging
from ai_utils_lib.foundry.client_mgr import AIClientManager
from openai import APIError, APIStatusError
from openai.types.conversations import Conversation
from openai.types.responses import Response

CONFIG_PATH = Path(__file__).with_name("config.yaml")

_INDENT: int = 2

logger = logging.getLogger("azure_foundry.agent_basic")


def _log_api_error(error: APIError) -> None:
    # Foundry wraps agent tool failures (e.g. 424) in an HTTP 400.
    status_code = (
        error.status_code if isinstance(error, APIStatusError) else None
    )
    message = (
        error.body.get("message")
        if isinstance(error.body, dict)
        else error.message
    )
    logger.error(
        "Foundry request failed: status_code=%s, type=%s, message=%s",
        status_code,
        error.type,
        message,
    )


async def main() -> None:
    #################################################################
    # Load app configuration settings and configure loggers
    app_config: AppConfig = await aload_config(CONFIG_PATH)
    configure_logging(app_config)
    logger.debug(
        "app_config: %s",
        app_config.model_dump_json(indent=_INDENT, exclude={"logging"}),
    )

    #################################################################
    # Create/initialize AIClientManager instance
    logger.info("Initializing AIClientManager...")
    client_mgr: AIClientManager = AIClientManager(
        app_config.foundry.project_endpoint
    )
    await client_mgr.initialize()

    try:
        logger.info("Creating conversation...")
        #################################################################
        # Create a new conversation
        conversation: Conversation = (
            await client_mgr.openai_client.conversations.create(items=[])
        )
        logger.debug(
            "conversation: %s", conversation.model_dump_json(indent=_INDENT)
        )

        #################################################################
        # User input interaction
        while True:
            raw_input = await asyncio.to_thread(input, "You: ")
            user_input = raw_input.strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\nEnding conversation...")
                break

            # Persist user input to the conversation in the backend
            await client_mgr.save_user_msg_to_conversation(
                conversation.id, user_input
            )
            await client_mgr.debuglog_conversation(conversation.id)

            # Post conversation to server-side agent
            response: Response = await client_mgr.post_conversation_to_agent(
                conversation_id=conversation.id,
                server_agent_name=app_config.foundry.agent_name,
            )

            print(f"Agent response: {response.output_text}\n")
    except EOFError:
        logger.info("user hit Ctrl+D")
        print("\nEnding conversation...")
    except APIError as error:
        _log_api_error(error)
    finally:
        logger.debug("Closing the AIClientManager.")
        await client_mgr.close()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("user hit Ctrl+C")
        print("\nProgram terminated.")


if __name__ == "__main__":
    run()
