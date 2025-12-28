"""Conversation Hooks - Captures full LLM conversation for debugging."""

import json
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field, asdict

from agents import Agent
from agents.lifecycle import RunHooks
from agents.items import ModelResponse, TResponseInputItem
from agents.run_context import RunContextWrapper


@dataclass
class ConversationMessage:
    """A single message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    token_count: Optional[int] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolCall:
    """A tool/function call record."""
    name: str
    input: str
    output: str
    started_at: str
    ended_at: str
    duration_ms: float


@dataclass
class LLMCall:
    """A complete LLM call with input and output."""
    agent_name: str
    system_prompt: Optional[str]
    input_messages: list[dict]
    output_content: str
    output_tool_calls: list[dict]
    started_at: str
    ended_at: str
    duration_ms: float
    usage: dict  # token counts
    model: Optional[str] = None


@dataclass
class ConversationTrace:
    """Full conversation trace with all data."""
    trace_id: str
    workflow_name: str
    started_at: str
    ended_at: Optional[str] = None
    llm_calls: list[LLMCall] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    agents_used: list[str] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ConversationCaptureHooks(RunHooks):
    """
    RunHooks implementation that captures full LLM conversation.

    Usage:
        hooks = ConversationCaptureHooks("my-workflow")
        result = await Runner.run(agent, prompt, run_hooks=hooks)
        trace = hooks.get_trace()
    """

    def __init__(self, workflow_name: str = "unknown"):
        self.trace = ConversationTrace(
            trace_id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            workflow_name=workflow_name,
            started_at=datetime.now().isoformat(),
        )
        self._current_llm_start: Optional[str] = None
        self._current_llm_data: dict = {}
        self._current_tool_start: dict = {}

    async def on_agent_start(self, context, agent) -> None:
        """Called when an agent starts."""
        agent_name = getattr(agent, 'name', str(agent))
        if agent_name not in self.trace.agents_used:
            self.trace.agents_used.append(agent_name)

    async def on_agent_end(self, context, agent, output: Any) -> None:
        """Called when an agent produces final output."""
        pass

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        """Called just before invoking the LLM."""
        self._current_llm_start = datetime.now().isoformat()

        # Parse input items into readable format
        input_messages = []
        for item in input_items:
            msg = self._parse_input_item(item)
            if msg:
                input_messages.append(msg)

        self._current_llm_data = {
            "agent_name": getattr(agent, 'name', 'unknown'),
            "system_prompt": system_prompt,
            "input_messages": input_messages,
            "model": getattr(agent, 'model', None),
        }

    async def on_llm_end(
        self,
        context: RunContextWrapper,
        agent: Agent,
        response: ModelResponse,
    ) -> None:
        """Called immediately after the LLM call returns."""
        ended_at = datetime.now().isoformat()

        # Calculate duration
        start_dt = datetime.fromisoformat(self._current_llm_start)
        end_dt = datetime.fromisoformat(ended_at)
        duration_ms = (end_dt - start_dt).total_seconds() * 1000

        # Parse response content
        output_content = ""
        output_tool_calls = []

        if hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    # Text content
                    for content_part in item.content:
                        if hasattr(content_part, 'text'):
                            output_content += content_part.text
                if hasattr(item, 'type') and item.type == 'function_call':
                    # Tool call
                    output_tool_calls.append({
                        "name": getattr(item, 'name', 'unknown'),
                        "arguments": getattr(item, 'arguments', '{}'),
                    })

        # Extract usage
        usage = {}
        if hasattr(response, 'usage') and response.usage:
            usage = {
                "input_tokens": getattr(response.usage, 'input_tokens', 0),
                "output_tokens": getattr(response.usage, 'output_tokens', 0),
                "total_tokens": getattr(response.usage, 'total_tokens', 0),
            }
            self.trace.total_tokens += usage.get('total_tokens', 0)

        # Create LLM call record
        llm_call = LLMCall(
            agent_name=self._current_llm_data.get("agent_name", "unknown"),
            system_prompt=self._current_llm_data.get("system_prompt"),
            input_messages=self._current_llm_data.get("input_messages", []),
            output_content=output_content,
            output_tool_calls=output_tool_calls,
            started_at=self._current_llm_start,
            ended_at=ended_at,
            duration_ms=duration_ms,
            usage=usage,
            model=self._current_llm_data.get("model"),
        )

        self.trace.llm_calls.append(llm_call)

        # Reset
        self._current_llm_start = None
        self._current_llm_data = {}

    async def on_tool_start(self, context, agent, tool) -> None:
        """Called before a tool is invoked."""
        tool_name = getattr(tool, 'name', str(tool))
        self._current_tool_start[tool_name] = datetime.now().isoformat()

    async def on_tool_end(self, context, agent, tool, result: str) -> None:
        """Called after a tool returns."""
        tool_name = getattr(tool, 'name', str(tool))
        ended_at = datetime.now().isoformat()

        started_at = self._current_tool_start.get(tool_name, ended_at)
        start_dt = datetime.fromisoformat(started_at)
        end_dt = datetime.fromisoformat(ended_at)
        duration_ms = (end_dt - start_dt).total_seconds() * 1000

        # Get input from context if available
        tool_input = ""
        if hasattr(context, 'last_tool_input'):
            tool_input = str(context.last_tool_input)

        tool_call = ToolCall(
            name=tool_name,
            input=tool_input,
            output=result[:5000] if result else "",  # Limit output size
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
        )

        self.trace.tool_calls.append(tool_call)

        # Cleanup
        if tool_name in self._current_tool_start:
            del self._current_tool_start[tool_name]

    def _parse_input_item(self, item) -> Optional[dict]:
        """Parse an input item into a readable dict."""
        # Handle dict items (new SDK format)
        if isinstance(item, dict):
            role = item.get('role')
            content = item.get('content')
            if role and content:
                if isinstance(content, list):
                    # Multiple content parts
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and 'text' in part:
                            text_parts.append(part['text'])
                        elif hasattr(part, 'text'):
                            text_parts.append(part.text)
                        else:
                            text_parts.append(str(part))
                    content = "\n".join(text_parts)
                return {
                    "role": role,
                    "content": str(content)[:10000],  # Limit size
                }
            elif 'type' in item:
                return {
                    "type": item['type'],
                    "content": str(item)[:10000],
                }
        # Handle object items (legacy format)
        elif hasattr(item, 'role') and hasattr(item, 'content'):
            content = item.content
            if isinstance(content, list):
                # Multiple content parts
                text_parts = []
                for part in content:
                    if hasattr(part, 'text'):
                        text_parts.append(part.text)
                content = "\n".join(text_parts)
            return {
                "role": item.role,
                "content": str(content)[:10000],  # Limit size
            }
        elif hasattr(item, 'type'):
            return {
                "type": item.type,
                "content": str(item)[:10000],
            }
        return None

    def finalize(self) -> None:
        """Finalize the trace."""
        self.trace.ended_at = datetime.now().isoformat()

    def get_trace(self) -> ConversationTrace:
        """Get the captured trace."""
        if not self.trace.ended_at:
            self.finalize()
        return self.trace

    def save_to_file(self, filepath: str) -> None:
        """Save trace to JSON file."""
        self.finalize()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.trace.to_json())
