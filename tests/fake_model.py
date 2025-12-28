"""Fake Model for testing agents without real API calls.

Based on OpenAI Agents SDK testing patterns.
Reference: refs/openai-agents-python/tests/fake_model.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai.types.responses import (
    Response,
    ResponseCompletedEvent,
    ResponseCreatedEvent,
    ResponseInProgressEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseUsage,
)
from openai.types.responses.response_usage import InputTokensDetails, OutputTokensDetails

from agents.agent_output import AgentOutputSchemaBase
from agents.handoffs import Handoff
from agents.items import (
    ModelResponse,
    TResponseInputItem,
    TResponseOutputItem,
    TResponseStreamEvent,
)
from agents.model_settings import ModelSettings
from agents.models.interface import Model, ModelTracing
from agents.tool import Tool
from agents.tracing import SpanError, generation_span
from agents.usage import Usage


class FakeModel(Model):
    """
    A fake model for testing agents.

    Usage:
        model = FakeModel()
        model.set_next_output([get_text_message("Hello")])

        agent = Agent(name="test", model=model)
        result = await Runner.run(agent, input="test")
        assert result.final_output == "Hello"
    """

    def __init__(
        self,
        tracing_enabled: bool = False,
        initial_output: list[TResponseOutputItem] | Exception | None = None,
    ):
        if initial_output is None:
            initial_output = []
        self.turn_outputs: list[list[TResponseOutputItem] | Exception] = (
            [initial_output] if initial_output else []
        )
        self.tracing_enabled = tracing_enabled
        self.last_turn_args: dict[str, Any] = {}
        self.first_turn_args: dict[str, Any] | None = None
        self.hardcoded_usage: Usage | None = None

    def set_hardcoded_usage(self, usage: Usage):
        """Set a fixed usage to return."""
        self.hardcoded_usage = usage

    def set_next_output(self, output: list[TResponseOutputItem] | Exception):
        """Set the output for the next turn."""
        self.turn_outputs.append(output)

    def add_multiple_turn_outputs(self, outputs: list[list[TResponseOutputItem] | Exception]):
        """Add multiple turn outputs for multi-turn conversations."""
        self.turn_outputs.extend(outputs)

    def get_next_output(self) -> list[TResponseOutputItem] | Exception:
        """Get and remove the next output."""
        if not self.turn_outputs:
            return []
        return self.turn_outputs.pop(0)

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any | None,
    ) -> ModelResponse:
        """Mock implementation of get_response."""
        turn_args = {
            "system_instructions": system_instructions,
            "input": input,
            "model_settings": model_settings,
            "tools": tools,
            "output_schema": output_schema,
            "previous_response_id": previous_response_id,
            "conversation_id": conversation_id,
        }

        if self.first_turn_args is None:
            self.first_turn_args = turn_args.copy()

        self.last_turn_args = turn_args

        with generation_span(disabled=not self.tracing_enabled) as span:
            output = self.get_next_output()

            if isinstance(output, Exception):
                span.set_error(
                    SpanError(
                        message="Error",
                        data={
                            "name": output.__class__.__name__,
                            "message": str(output),
                        },
                    )
                )
                raise output

            return ModelResponse(
                output=output,
                usage=self.hardcoded_usage or Usage(),
                response_id="resp-test-789",
            )

    async def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None = None,
        conversation_id: str | None = None,
        prompt: Any | None = None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        """Mock implementation of stream_response."""
        turn_args = {
            "system_instructions": system_instructions,
            "input": input,
            "model_settings": model_settings,
            "tools": tools,
            "output_schema": output_schema,
            "previous_response_id": previous_response_id,
            "conversation_id": conversation_id,
        }

        if self.first_turn_args is None:
            self.first_turn_args = turn_args.copy()

        self.last_turn_args = turn_args

        with generation_span(disabled=not self.tracing_enabled) as span:
            output = self.get_next_output()
            if isinstance(output, Exception):
                span.set_error(
                    SpanError(
                        message="Error",
                        data={
                            "name": output.__class__.__name__,
                            "message": str(output),
                        },
                    )
                )
                raise output

            response = get_response_obj(output, usage=self.hardcoded_usage)
            sequence_number = 0

            yield ResponseCreatedEvent(
                type="response.created",
                response=response,
                sequence_number=sequence_number,
            )
            sequence_number += 1

            yield ResponseInProgressEvent(
                type="response.in_progress",
                response=response,
                sequence_number=sequence_number,
            )
            sequence_number += 1

            for output_index, output_item in enumerate(output):
                yield ResponseOutputItemAddedEvent(
                    type="response.output_item.added",
                    item=output_item,
                    output_index=output_index,
                    sequence_number=sequence_number,
                )
                sequence_number += 1

                yield ResponseOutputItemDoneEvent(
                    type="response.output_item.done",
                    item=output_item,
                    output_index=output_index,
                    sequence_number=sequence_number,
                )
                sequence_number += 1

            yield ResponseCompletedEvent(
                type="response.completed",
                response=response,
                sequence_number=sequence_number,
            )


def get_response_obj(
    output: list[TResponseOutputItem],
    response_id: str | None = None,
    usage: Usage | None = None,
) -> Response:
    """Create a Response object for testing."""
    return Response(
        id=response_id or "resp-test-789",
        created_at=123,
        model="test_model",
        object="response",
        output=output,
        tool_choice="none",
        tools=[],
        top_p=None,
        parallel_tool_calls=False,
        usage=ResponseUsage(
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
        ),
    )
