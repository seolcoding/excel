"""Streaming Monitor - Real-time LLM output and thinking process monitoring."""

import asyncio
from datetime import datetime
from typing import Any, Optional, Callable
from dataclasses import dataclass, field

from agents import Agent, Runner, ItemHelpers
from agents.lifecycle import RunHooks
from agents.items import ModelResponse, TResponseInputItem
from agents.run_context import RunContextWrapper


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Agent colors
    AGENT = "\033[36m"      # Cyan
    THINKING = "\033[33m"   # Yellow
    OUTPUT = "\033[32m"     # Green
    TOOL = "\033[35m"       # Magenta
    ERROR = "\033[31m"      # Red
    INFO = "\033[34m"       # Blue


@dataclass
class MonitorEvent:
    """A single monitoring event."""
    timestamp: str
    event_type: str  # "agent_start", "llm_start", "thinking", "output", "tool", "agent_end"
    agent_name: str
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class MonitorSession:
    """Session data for monitoring."""
    session_id: str
    started_at: str
    events: list[MonitorEvent] = field(default_factory=list)
    total_tokens: int = 0
    total_thinking_tokens: int = 0
    agents_called: list[str] = field(default_factory=list)


# Callback types for external handlers
OutputCallback = Callable[[str, str], None]  # (event_type, content)
ThinkingCallback = Callable[[str], None]  # (thinking_content)


class StreamingMonitorHooks(RunHooks):
    """
    RunHooks implementation for real-time monitoring of LLM output.

    Features:
    - Real-time token-by-token output
    - Thinking/reasoning content capture (for models that support it)
    - Tool call monitoring
    - Agent lifecycle tracking

    Usage:
        monitor = StreamingMonitorHooks(verbose=True)
        result = await Runner.run(agent, prompt, hooks=monitor)
        session = monitor.get_session()
    """

    def __init__(
        self,
        verbose: bool = True,
        show_thinking: bool = True,
        show_tool_calls: bool = True,
        output_callback: Optional[OutputCallback] = None,
        thinking_callback: Optional[ThinkingCallback] = None,
    ):
        """
        Initialize the streaming monitor.

        Args:
            verbose: Whether to print to console
            show_thinking: Whether to display thinking/reasoning content
            show_tool_calls: Whether to display tool calls
            output_callback: Optional callback for output events
            thinking_callback: Optional callback for thinking content
        """
        self.verbose = verbose
        self.show_thinking = show_thinking
        self.show_tool_calls = show_tool_calls
        self.output_callback = output_callback
        self.thinking_callback = thinking_callback

        self.session = MonitorSession(
            session_id=f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            started_at=datetime.now().isoformat(),
        )

        self._current_agent: Optional[str] = None
        self._llm_start_time: Optional[datetime] = None

    def _log(self, color: str, prefix: str, message: str, end: str = "\n"):
        """Print colored output if verbose mode is enabled."""
        if self.verbose:
            print(f"{color}{prefix}{Colors.RESET} {message}", end=end, flush=True)

    def _add_event(
        self,
        event_type: str,
        content: str,
        metadata: Optional[dict] = None
    ):
        """Add an event to the session."""
        event = MonitorEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            agent_name=self._current_agent or "unknown",
            content=content,
            metadata=metadata or {},
        )
        self.session.events.append(event)

        if self.output_callback:
            self.output_callback(event_type, content)

    async def on_agent_start(self, context, agent: Agent) -> None:
        """Called when an agent starts."""
        agent_name = getattr(agent, 'name', str(agent))
        self._current_agent = agent_name

        if agent_name not in self.session.agents_called:
            self.session.agents_called.append(agent_name)

        self._add_event("agent_start", f"Agent '{agent_name}' started")
        self._log(Colors.AGENT, f"🚀 [{agent_name}]", "시작")

    async def on_agent_end(self, context, agent: Agent, output: Any) -> None:
        """Called when an agent produces final output."""
        agent_name = getattr(agent, 'name', str(agent))
        output_str = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)

        self._add_event("agent_end", f"Agent '{agent_name}' ended", {"output": output_str})
        self._log(Colors.AGENT, f"✅ [{agent_name}]", f"완료: {output_str[:100]}...")

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        """Called just before invoking the LLM."""
        self._llm_start_time = datetime.now()
        agent_name = getattr(agent, 'name', str(agent))

        # Count input messages
        msg_count = len(input_items)

        self._add_event("llm_start", f"LLM call started", {
            "agent": agent_name,
            "input_message_count": msg_count,
        })
        self._log(Colors.INFO, f"📝 [{agent_name}]", f"LLM 호출 시작 (입력 메시지: {msg_count}개)")

    async def on_llm_end(
        self,
        context: RunContextWrapper,
        agent: Agent,
        response: ModelResponse,
    ) -> None:
        """Called immediately after the LLM call returns."""
        agent_name = getattr(agent, 'name', str(agent))
        duration_ms = 0

        if self._llm_start_time:
            duration_ms = (datetime.now() - self._llm_start_time).total_seconds() * 1000

        # Extract usage info
        usage = {}
        if hasattr(response, 'usage') and response.usage:
            usage = {
                "input_tokens": getattr(response.usage, 'input_tokens', 0),
                "output_tokens": getattr(response.usage, 'output_tokens', 0),
                "total_tokens": getattr(response.usage, 'total_tokens', 0),
            }
            self.session.total_tokens += usage.get('total_tokens', 0)

        # Extract reasoning content if available
        reasoning_content = ""
        output_content = ""
        tool_calls = []

        if hasattr(response, 'output'):
            for item in response.output:
                item_type = getattr(item, 'type', None)

                # Check for reasoning content
                if hasattr(item, 'reasoning_content') and item.reasoning_content:
                    reasoning_content = item.reasoning_content
                    if self.show_thinking and self.thinking_callback:
                        self.thinking_callback(reasoning_content)

                # Handle message output
                if item_type == 'message' and hasattr(item, 'content') and item.content:
                    for content_part in item.content:
                        if hasattr(content_part, 'text'):
                            output_content += content_part.text

                # Handle tool calls
                elif item_type == 'function_call':
                    tool_calls.append({
                        "name": getattr(item, 'name', 'unknown'),
                        "arguments": getattr(item, 'arguments', '{}'),
                    })

        self._add_event("llm_end", f"LLM call completed", {
            "duration_ms": duration_ms,
            "usage": usage,
            "has_reasoning": bool(reasoning_content),
            "tool_calls_count": len(tool_calls),
        })

        # Log output
        token_info = f"토큰: {usage.get('total_tokens', '?')}"
        self._log(Colors.INFO, f"📝 [{agent_name}]", f"LLM 완료 ({duration_ms:.0f}ms, {token_info})")

        # Log reasoning if present
        if reasoning_content and self.show_thinking:
            self._add_event("thinking", reasoning_content)
            self._log(Colors.THINKING, "💭 Thinking:", "")
            for line in reasoning_content.split('\n')[:10]:  # First 10 lines
                self._log(Colors.THINKING, "   ", line)
            if reasoning_content.count('\n') > 10:
                self._log(Colors.DIM, "   ", f"... ({reasoning_content.count(chr(10)) - 10} more lines)")

        # Log output content
        if output_content:
            preview = output_content[:300] + "..." if len(output_content) > 300 else output_content
            self._add_event("output", output_content)
            self._log(Colors.OUTPUT, "📄 Output:", preview.replace('\n', ' ')[:200])

        # Log tool calls
        if tool_calls and self.show_tool_calls:
            for tc in tool_calls:
                self._log(Colors.TOOL, "🔧 Tool:", f"{tc['name']}({tc['arguments'][:100]}...)")

        self._llm_start_time = None

    async def on_tool_start(self, context, agent: Agent, tool) -> None:
        """Called before a tool is invoked."""
        tool_name = getattr(tool, 'name', str(tool))
        agent_name = getattr(agent, 'name', str(agent))

        self._add_event("tool_start", f"Tool '{tool_name}' starting")

        if self.show_tool_calls:
            self._log(Colors.TOOL, f"🔧 [{agent_name}]", f"도구 호출: {tool_name}")

    async def on_tool_end(self, context, agent: Agent, tool, result: str) -> None:
        """Called after a tool returns."""
        tool_name = getattr(tool, 'name', str(tool))
        result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)

        self._add_event("tool_end", f"Tool '{tool_name}' completed", {"result": result_preview})

        if self.show_tool_calls:
            self._log(Colors.TOOL, f"   └─ 결과:", result_preview.replace('\n', ' ')[:150])

    async def on_handoff(self, context, from_agent: Agent, to_agent: Agent) -> None:
        """Called when one agent hands off to another."""
        from_name = getattr(from_agent, 'name', str(from_agent))
        to_name = getattr(to_agent, 'name', str(to_agent))

        self._add_event("handoff", f"Handoff from '{from_name}' to '{to_name}'")
        self._log(Colors.AGENT, "🔄 Handoff:", f"{from_name} → {to_name}")

    def get_session(self) -> MonitorSession:
        """Get the monitoring session data."""
        return self.session

    def print_summary(self):
        """Print a summary of the monitoring session."""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}모니터링 세션 요약{Colors.RESET}")
        print(f"{'='*60}")
        print(f"세션 ID: {self.session.session_id}")
        print(f"시작 시간: {self.session.started_at}")
        print(f"총 이벤트: {len(self.session.events)}개")
        print(f"사용 에이전트: {', '.join(self.session.agents_called)}")
        print(f"총 토큰: {self.session.total_tokens:,}")

        # Event breakdown
        event_types = {}
        for event in self.session.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        print(f"\n이벤트 유형:")
        for event_type, count in sorted(event_types.items()):
            print(f"  - {event_type}: {count}개")

        print(f"{'='*60}\n")


async def run_with_streaming(
    agent: Agent,
    prompt: str,
    verbose: bool = True,
    show_thinking: bool = True,
) -> tuple[Any, MonitorSession]:
    """
    Convenience function to run an agent with streaming monitoring.

    Args:
        agent: The agent to run
        prompt: The input prompt
        verbose: Whether to print to console
        show_thinking: Whether to show thinking content

    Returns:
        Tuple of (result, monitor_session)
    """
    monitor = StreamingMonitorHooks(
        verbose=verbose,
        show_thinking=show_thinking,
    )

    result = await Runner.run(agent, prompt, hooks=monitor)

    if verbose:
        monitor.print_summary()

    return result, monitor.get_session()


async def stream_agent_output(
    agent: Agent,
    prompt: str,
    on_token: Optional[Callable[[str], None]] = None,
    on_thinking: Optional[Callable[[str], None]] = None,
) -> Any:
    """
    Stream agent output with token-by-token callbacks.

    Uses Runner.run_streamed for true streaming.

    Args:
        agent: The agent to run
        prompt: The input prompt
        on_token: Callback for each output token
        on_thinking: Callback for thinking content

    Returns:
        The final result
    """
    from openai.types.responses import ResponseTextDeltaEvent

    result = Runner.run_streamed(agent, prompt)

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            # Check for thinking/reasoning content
            if hasattr(event.data, 'type'):
                if event.data.type == "response.reasoning_text.delta":
                    if on_thinking:
                        on_thinking(event.data.delta)
                    print(f"{Colors.THINKING}{event.data.delta}{Colors.RESET}", end="", flush=True)

                elif event.data.type == "response.output_text.delta":
                    if on_token:
                        on_token(event.data.delta)
                    print(f"{Colors.OUTPUT}{event.data.delta}{Colors.RESET}", end="", flush=True)

                elif isinstance(event.data, ResponseTextDeltaEvent):
                    if on_token:
                        on_token(event.data.delta)
                    print(f"{Colors.OUTPUT}{event.data.delta}{Colors.RESET}", end="", flush=True)

        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                tool_name = getattr(event.item.raw_item, 'name', 'Unknown Tool')
                print(f"\n{Colors.TOOL}🔧 Tool: {tool_name}{Colors.RESET}")

            elif event.item.type == "tool_call_output_item":
                output = str(event.item.output)[:100]
                print(f"{Colors.TOOL}   └─ Result: {output}{Colors.RESET}")

            elif event.item.type == "message_output_item":
                # Final message already streamed
                pass

    print()  # Newline after streaming
    return await result
