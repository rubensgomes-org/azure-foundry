"""Interactive console client for a server-side agent with function tools."""

import asyncio
import json
import logging
from collections.abc import Callable
from pathlib import Path

from ai_utils_lib.config import aload_config
from ai_utils_lib.config_models import AppConfig
from ai_utils_lib.file.file_config import configure_logging
from ai_utils_lib.foundry.client_mgr import AIClientManager
from azure.ai.projects.models import AgentVersionDetails, FunctionTool, Tool
from openai import APIError, APIStatusError
from openai.types.conversations import Conversation
from openai.types.responses import Response, ResponseOutputItem
from openai.types.responses.response_input_param import (
    FunctionCallOutput,
    ResponseInputParam,
)

from azure_foundry.agent_functions.functions import (
    calculate_observation_cost,
    generate_observation_report,
    next_visible_event,
)

CONFIG_PATH = Path(__file__).with_name("config.yaml")

_AGENT_FUNCTIONS: dict[str, Callable[..., str]] = {
    "next_visible_event": next_visible_event,
    "calculate_observation_cost": calculate_observation_cost,
    "generate_observation_report": generate_observation_report,
}

_INDENT: int = 2

logger = logging.getLogger(__name__)


def _list_function_tools() -> list[Tool]:
    tools: list[Tool] = []

    # Define the event function tool
    event_tool = FunctionTool(
        name="next_visible_event",
        description="Get the next visible event in a given location.",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "continent to find the next visible event in (e.g. 'north_america', 'south_america', 'australia')",
                },
            },
            "required": ["location"],
            "additionalProperties": False,
        },
        strict=True,
    )
    tools.append(event_tool)

    # Define the observation cost function tool
    cost_tool = FunctionTool(
        name="calculate_observation_cost",
        description="Calculate the cost of an observation based on the telescope tier, number of hours, and priority level.",
        parameters={
            "type": "object",
            "properties": {
                "telescope_tier": {
                    "type": "string",
                    "description": "the tier of the telescope (e.g. 'standard', 'advanced', 'premium')",
                },
                "hours": {
                    "type": "number",
                    "description": "the number of hours for the observation",
                },
                "priority": {
                    "type": "string",
                    "description": "the priority level of the observation (e.g. 'low', 'normal', 'high')",
                },
            },
            "required": ["telescope_tier", "hours", "priority"],
            "additionalProperties": False,
        },
        strict=True,
    )
    tools.append(cost_tool)

    # Define the observation report generation function tool
    report_tool = FunctionTool(
        name="generate_observation_report",
        description="Generate a report summarizing an astronomical observation",
        parameters={
            "type": "object",
            "properties": {
                "event_name": {
                    "type": "string",
                    "description": "the name of the astronomical event being observed",
                },
                "location": {
                    "type": "string",
                    "description": "the location of the observer",
                },
                "telescope_tier": {
                    "type": "string",
                    "description": "the tier of the telescope used for the observation (e.g. 'standard', 'advanced', 'premium')",
                },
                "hours": {
                    "type": "number",
                    "description": "the number of hours the telescope was used for the observation",
                },
                "priority": {
                    "type": "string",
                    "description": "the priority level of the observation (e.g. 'low', 'normal', 'high')",
                },
                "observer_name": {
                    "type": "string",
                    "description": "the name of the person who conducted the observation",
                },
            },
            "required": [
                "event_name",
                "location",
                "telescope_tier",
                "hours",
                "priority",
                "observer_name",
            ],
            "additionalProperties": False,
        },
        strict=True,
    )
    tools.append(report_tool)
    return tools


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


def _run_function_calls(
    output_items: list[ResponseOutputItem],
) -> ResponseInputParam:
    """Run agent's function calls and return their outputs as input items."""
    input_list: ResponseInputParam = []
    for item in output_items:
        if item.type != "function_call":
            continue
        print(f"function_name: {item.name}")
        result = _AGENT_FUNCTIONS[item.name](**json.loads(item.arguments))
        input_list.append(
            FunctionCallOutput(
                type="function_call_output",
                call_id=item.call_id,
                output=result,
            )
        )
    return input_list


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

    #################################################################
    # Create list of tools to be used by the Agent
    tools: list[Tool] = _list_function_tools()

    #################################################################
    # Create Foundry Service Agent
    agent: AgentVersionDetails = await client_mgr.create_agent(
        app_config.foundry.agent_name,
        app_config.model.name,
        instructions=app_config.model.instructions,
        tools=tools,
    )

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
            raw_input = await asyncio.to_thread(input, "User: ")
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

            input_list: ResponseInputParam = _run_function_calls(
                response.output
            )

            if input_list:
                # Post conversation to server-side agent
                response = await client_mgr.post_conversation_to_agent(
                    conversation_id=conversation.id,
                    server_agent_name=app_config.foundry.agent_name,
                    agent_input=input_list,
                )

            # Display the agent's response
            print(f"Agent response: {response.output_text}\n")

    except EOFError:
        logger.info("user hit Ctrl+D")
        print("\nEnding conversation...")
    except APIError as error:
        _log_api_error(error)
    finally:
        logger.info("Deleting agent: %s", agent.name)
        await client_mgr.delete_agent(agent.name)
        logger.info("Closing the AIClientManager.")
        await client_mgr.close()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("user hit Ctrl+C")
        print("\nProgram terminated.")


if __name__ == "__main__":
    run()
