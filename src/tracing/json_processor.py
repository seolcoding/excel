"""JSON-based tracing processor for exporting agent traces."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.tracing import TracingProcessor, Trace, Span, add_trace_processor


class JsonTracingProcessor(TracingProcessor):
    """Collects trace data and exports to JSON file."""

    def __init__(self, output_dir: str = "traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.traces: dict[str, dict] = {}
        self.spans: dict[str, list[dict]] = {}

    def on_trace_start(self, trace: Trace) -> None:
        """Called when a new trace begins."""
        self.traces[trace.trace_id] = {
            "trace_id": trace.trace_id,
            "workflow_name": trace.name,
            "group_id": trace.group_id,
            "metadata": trace.metadata,
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "spans": [],
        }
        self.spans[trace.trace_id] = []

    def on_trace_end(self, trace: Trace) -> None:
        """Called when a trace completes - exports to JSON."""
        if trace.trace_id in self.traces:
            self.traces[trace.trace_id]["ended_at"] = datetime.now().isoformat()
            self.traces[trace.trace_id]["spans"] = self.spans.get(trace.trace_id, [])

            # Export to JSON file
            self._export_trace(trace.trace_id)

            # Cleanup
            del self.traces[trace.trace_id]
            if trace.trace_id in self.spans:
                del self.spans[trace.trace_id]

    def on_span_start(self, span: Span[Any]) -> None:
        """Called when a new span begins."""
        pass  # We capture data on span_end

    def on_span_end(self, span: Span[Any]) -> None:
        """Called when a span completes."""
        trace_id = span.trace_id
        if trace_id and trace_id in self.spans:
            span_data = {
                "span_id": span.span_id,
                "parent_id": span.parent_id,
                "started_at": span.started_at,
                "ended_at": span.ended_at,
                "error": span.error,
            }

            # Add span-specific data
            if span.span_data:
                span_data["type"] = span.span_data.type
                span_data["data"] = self._safe_export(span.span_data.export())

            self.spans[trace_id].append(span_data)

    def _safe_export(self, data: dict) -> dict:
        """Safely export data, handling non-serializable types."""
        def make_serializable(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            else:
                return str(obj)

        return make_serializable(data)

    def _export_trace(self, trace_id: str) -> None:
        """Export trace to JSON file."""
        trace_data = self.traces.get(trace_id)
        if not trace_data:
            return

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{timestamp}_{trace_id[:8]}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)

        print(f"[Trace] Exported to: {filepath}")

    def shutdown(self) -> None:
        """Clean up resources."""
        self.traces.clear()
        self.spans.clear()

    def force_flush(self) -> None:
        """Force export of any pending traces."""
        for trace_id in list(self.traces.keys()):
            self._export_trace(trace_id)

    def get_latest_trace(self) -> dict | None:
        """Get the most recent trace data (for embedding in HTML)."""
        trace_files = sorted(self.output_dir.glob("trace_*.json"), reverse=True)
        if trace_files:
            with open(trace_files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        return None


# Global processor instance
_processor: JsonTracingProcessor | None = None


def add_json_tracing(output_dir: str = "traces") -> JsonTracingProcessor:
    """Add JSON tracing processor to the agent runtime."""
    global _processor
    _processor = JsonTracingProcessor(output_dir)
    add_trace_processor(_processor)
    return _processor


def get_processor() -> JsonTracingProcessor | None:
    """Get the global JSON tracing processor."""
    return _processor
