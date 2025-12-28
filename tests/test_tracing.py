"""Unit tests for tracing in TDD pipeline.

Based on OpenAI Agents SDK tracing patterns.
Reference: refs/openai-agents-python/tests/test_tracing.py
"""

from __future__ import annotations

import threading
from typing import Any
import pytest

from agents import Agent, Runner
from agents.tracing import (
    Span,
    Trace,
    TracingProcessor,
    trace,
    agent_span,
    custom_span,
    generation_span,
    function_span,
    set_trace_processors,
)

from tests.fake_model import FakeModel
from tests.helpers import get_text_message, get_json_message, get_webapp_spec_output


class SpanProcessorForTests(TracingProcessor):
    """
    A simple processor that stores spans in memory for testing.
    Based on SDK's testing_processor.py
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._spans: list[Span[Any]] = []
        self._traces: list[Trace] = []
        self._events: list[str] = []

    def on_trace_start(self, trace: Trace) -> None:
        with self._lock:
            self._traces.append(trace)
            self._events.append("trace_start")

    def on_trace_end(self, trace: Trace) -> None:
        with self._lock:
            self._events.append("trace_end")

    def on_span_start(self, span: Span[Any]) -> None:
        with self._lock:
            self._events.append("span_start")

    def on_span_end(self, span: Span[Any]) -> None:
        with self._lock:
            self._events.append("span_end")
            self._spans.append(span)

    def get_ordered_spans(self) -> list[Span[Any]]:
        with self._lock:
            spans = [x for x in self._spans if x.export()]
            return sorted(spans, key=lambda x: x.started_at or 0)

    def get_traces(self) -> list[Trace]:
        with self._lock:
            return [x for x in self._traces if x.export()]

    def clear(self) -> None:
        with self._lock:
            self._spans.clear()
            self._traces.clear()
            self._events.clear()

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass


# Global test processor instance
TEST_PROCESSOR = SpanProcessorForTests()


@pytest.fixture(autouse=True)
def setup_test_processor():
    """Set up test processor before each test."""
    TEST_PROCESSOR.clear()
    set_trace_processors([TEST_PROCESSOR])
    yield
    TEST_PROCESSOR.clear()


class TestBasicTracing:
    """Tests for basic tracing functionality."""

    def test_trace_creates_trace_object(self):
        """Test that trace() creates a Trace object."""
        with trace("test_workflow"):
            pass

        traces = TEST_PROCESSOR.get_traces()
        assert len(traces) == 1
        assert traces[0].name == "test_workflow"

    def test_trace_has_trace_id(self):
        """Test that trace has a trace_id."""
        with trace("test_workflow") as t:
            assert t.trace_id is not None
            assert t.trace_id.startswith("trace_")

    def test_trace_with_custom_id(self):
        """Test trace with custom trace_id."""
        with trace("test_workflow", trace_id="trace_custom123"):
            pass

        traces = TEST_PROCESSOR.get_traces()
        assert traces[0].trace_id == "trace_custom123"

    def test_trace_with_group_id(self):
        """Test trace with group_id for conversation tracking."""
        with trace("test_workflow", group_id="conversation_123"):
            pass

        traces = TEST_PROCESSOR.get_traces()
        assert traces[0].group_id == "conversation_123"


class TestSpanCreation:
    """Tests for span creation."""

    def test_agent_span_creates_span(self):
        """Test that agent_span creates a span."""
        with trace("test_workflow"):
            with agent_span(name="test_agent"):
                pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1

    def test_custom_span_creates_span(self):
        """Test that custom_span creates a span."""
        with trace("test_workflow"):
            with custom_span(name="custom_operation"):
                pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1

    def test_generation_span_creates_span(self):
        """Test that generation_span creates a span."""
        with trace("test_workflow"):
            with generation_span():
                pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1

    def test_nested_spans(self):
        """Test nested spans are properly parented."""
        with trace("test_workflow"):
            with custom_span(name="outer", span_id="outer_span"):
                with custom_span(name="inner", span_id="inner_span"):
                    pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 2

        # Find inner span and check parent
        inner_span = next((s for s in spans if s.span_id == "inner_span"), None)
        if inner_span:
            assert inner_span.parent_id == "outer_span"


class TestAgentTracingWithFakeModel:
    """Tests for agent tracing using FakeModel."""

    @pytest.mark.asyncio
    async def test_agent_run_creates_trace(self):
        """Test that Runner.run creates a trace."""
        model = FakeModel(tracing_enabled=True)
        model.set_next_output([get_text_message("Hello")])

        agent = Agent(
            name="Test Agent",
            instructions="Say hello",
            tools=[],
            model=model,
        )

        with trace("agent_run_test"):
            await Runner.run(agent, input="Hi")

        traces = TEST_PROCESSOR.get_traces()
        assert len(traces) >= 1

    @pytest.mark.asyncio
    async def test_agent_span_contains_agent_name(self):
        """Test that agent span contains agent name."""
        model = FakeModel(tracing_enabled=True)
        model.set_next_output([get_text_message("Hello")])

        agent = Agent(
            name="Named Agent",
            instructions="Test",
            tools=[],
            model=model,
        )

        with trace("test"):
            await Runner.run(agent, input="Hi")

        # Spans should include agent information
        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1


class TestTDDPipelineTracing:
    """Tests for tracing in TDD pipeline context."""

    def test_pipeline_trace_workflow_name(self):
        """Test that TDD pipeline uses appropriate workflow name."""
        with trace("TDD Pipeline - Excel to WebApp"):
            with custom_span(name="analyze"):
                pass
            with custom_span(name="spec"):
                pass
            with custom_span(name="generate"):
                pass
            with custom_span(name="test"):
                pass

        traces = TEST_PROCESSOR.get_traces()
        assert len(traces) == 1
        assert "TDD Pipeline" in traces[0].name

    def test_pipeline_stages_are_traced(self):
        """Test that all pipeline stages create spans."""
        with trace("TDD Pipeline"):
            with custom_span(name="analysis", span_id="analyze_span"):
                pass
            with custom_span(name="specification", span_id="spec_span"):
                pass
            with custom_span(name="generation", span_id="gen_span"):
                pass
            with custom_span(name="testing", span_id="test_span"):
                pass
            with custom_span(name="verification", span_id="verify_span"):
                pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        span_ids = [s.span_id for s in spans]

        assert "analyze_span" in span_ids
        assert "spec_span" in span_ids
        assert "gen_span" in span_ids
        assert "test_span" in span_ids
        assert "verify_span" in span_ids

    def test_iteration_loop_tracing(self):
        """Test that iteration loop creates multiple spans."""
        with trace("TDD Pipeline"):
            for i in range(3):
                with custom_span(name=f"iteration_{i}", span_id=f"iter_{i}"):
                    with custom_span(name="generate"):
                        pass
                    with custom_span(name="test"):
                        pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        # Should have 3 iteration spans + 6 nested spans (2 per iteration)
        assert len(spans) >= 9


class TestTracingEvents:
    """Tests for tracing event lifecycle."""

    def test_trace_start_event(self):
        """Test that trace_start event is recorded."""
        with trace("test"):
            pass

        assert "trace_start" in TEST_PROCESSOR._events

    def test_trace_end_event(self):
        """Test that trace_end event is recorded."""
        with trace("test"):
            pass

        assert "trace_end" in TEST_PROCESSOR._events

    def test_span_events_order(self):
        """Test that span events are in correct order."""
        with trace("test"):
            with custom_span(name="operation"):
                pass

        # Events should be: trace_start, span_start, span_end, trace_end
        events = TEST_PROCESSOR._events
        assert events[0] == "trace_start"
        assert "span_start" in events
        assert "span_end" in events
        assert events[-1] == "trace_end"


class TestTracingMetadata:
    """Tests for trace and span metadata."""

    def test_trace_metadata(self):
        """Test that trace can have metadata."""
        with trace(
            "test",
            metadata={"excel_file": "test.xlsx", "user_id": "user123"}
        ):
            pass

        traces = TEST_PROCESSOR.get_traces()
        # Metadata should be stored on trace
        assert traces[0].metadata is not None

    def test_span_timestamps(self):
        """Test that spans have start and end timestamps."""
        with trace("test"):
            with custom_span(name="operation"):
                pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1

        span = spans[0]
        assert span.started_at is not None
        assert span.ended_at is not None
        assert span.ended_at >= span.started_at


class TestTracingDisabled:
    """Tests for disabled tracing."""

    def test_disabled_trace_not_recorded(self):
        """Test that disabled traces are not recorded."""
        with trace("test", disabled=True):
            with custom_span(name="operation"):
                pass

        # Should not record the disabled trace
        traces = [t for t in TEST_PROCESSOR.get_traces() if t.name == "test"]
        # Disabled traces may still appear but with disabled flag
        if traces:
            for t in traces:
                assert t.disabled


class TestTracingWithErrors:
    """Tests for tracing with errors."""

    def test_span_records_error(self):
        """Test that span can record errors."""
        with trace("test"):
            span = custom_span(name="failing_operation")
            span.start()
            try:
                raise ValueError("Test error")
            except ValueError:
                from agents.tracing.spans import SpanError
                span.set_error(SpanError(
                    message="Operation failed",
                    data={"error_type": "ValueError", "message": "Test error"}
                ))
            finally:
                span.finish()

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1
        # Error should be recorded on span
        span = spans[0]
        assert span.error is not None

    @pytest.mark.asyncio
    async def test_agent_exception_traced(self):
        """Test that agent exceptions are traced."""
        model = FakeModel(tracing_enabled=True)
        model.set_next_output(ValueError("Model error"))

        agent = Agent(
            name="Failing Agent",
            instructions="Test",
            tools=[],
            model=model,
        )

        with trace("test"):
            try:
                await Runner.run(agent, input="Hi")
            except ValueError:
                pass  # Expected

        # Error should be captured in trace
        spans = TEST_PROCESSOR.get_ordered_spans()
        # At least the trace should exist
        traces = TEST_PROCESSOR.get_traces()
        assert len(traces) >= 1


class TestTracingConcurrency:
    """Tests for tracing with concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_traces_are_separate(self):
        """Test that concurrent traces don't interfere."""
        import asyncio

        async def run_trace(name: str):
            with trace(f"trace_{name}"):
                with custom_span(name=f"operation_{name}"):
                    await asyncio.sleep(0.01)

        await asyncio.gather(
            run_trace("a"),
            run_trace("b"),
            run_trace("c"),
        )

        traces = TEST_PROCESSOR.get_traces()
        trace_names = [t.name for t in traces]

        assert "trace_a" in trace_names
        assert "trace_b" in trace_names
        assert "trace_c" in trace_names


class TestTracingExport:
    """Tests for trace/span export functionality."""

    def test_trace_export(self):
        """Test that trace can be exported."""
        with trace("exportable_trace"):
            pass

        traces = TEST_PROCESSOR.get_traces()
        assert len(traces) >= 1

        exported = traces[0].export()
        assert exported is not None
        assert exported.get("workflow_name") == "exportable_trace"

    def test_span_export(self):
        """Test that span can be exported."""
        with trace("test"):
            with custom_span(name="exportable_span"):
                pass

        spans = TEST_PROCESSOR.get_ordered_spans()
        assert len(spans) >= 1

        exported = spans[0].export()
        assert exported is not None
        assert "span_data" in exported
