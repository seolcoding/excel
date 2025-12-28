"""Main entry point for the Excel to WebApp Converter."""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    import uvicorn
    from src.api import app

    uvicorn.run(app, host=host, port=port)


async def convert_file(excel_path: str, output_path: str = None, with_trace: bool = True):
    """Convert a single Excel file to a web app."""
    from src.orchestrator import convert_excel_to_webapp, ConversionProgress
    from src.tracing import add_json_tracing, get_processor

    path = Path(excel_path)
    if not path.exists():
        print(f"Error: File not found: {excel_path}")
        sys.exit(1)

    if path.suffix.lower() not in [".xlsx", ".xlsm"]:
        print(f"Error: Unsupported file type: {path.suffix}")
        sys.exit(1)

    # Determine output path
    if output_path is None:
        output_path = path.with_suffix(".html")
    else:
        output_path = Path(output_path)

    # Enable JSON tracing
    trace_processor = None
    if with_trace:
        trace_processor = add_json_tracing("traces")

    def progress_callback(progress: ConversionProgress):
        print(f"[{progress.progress:.0%}] {progress.message}")

    print(f"Converting: {excel_path}")
    print("-" * 40)

    result = await convert_excel_to_webapp(excel_path, progress_callback)

    if result.success:
        html = result.app.html

        # Embed trace data in HTML if available
        if trace_processor:
            trace_processor.force_flush()
            trace_data = trace_processor.get_latest_trace()
            if trace_data:
                html = embed_trace_in_html(html, trace_data)

        # Write HTML to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print("-" * 40)
        print(f"Success! Output saved to: {output_path}")
        print(f"Iterations used: {result.iterations_used}")
        print(f"Test pass rate: {result.final_pass_rate:.0%}")
    else:
        print("-" * 40)
        print(f"Error: {result.message}")
        sys.exit(1)


def embed_trace_in_html(html: str, trace_data: dict) -> str:
    """Embed trace data and viewer UI in the generated HTML."""
    trace_json = json.dumps(trace_data, ensure_ascii=False)

    # Trace viewer HTML/CSS/JS
    trace_viewer = '''
<!-- Agent Trace Viewer -->
<style>
.trace-toggle {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    background: #6366f1;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 25px;
    cursor: pointer;
    font-size: 14px;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    display: flex;
    align-items: center;
    gap: 8px;
}
.trace-toggle:hover { background: #4f46e5; }
.trace-panel {
    position: fixed;
    top: 0;
    right: -450px;
    width: 450px;
    height: 100vh;
    background: #1e1e2e;
    color: #cdd6f4;
    z-index: 9998;
    transition: right 0.3s ease;
    overflow-y: auto;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
}
.trace-panel.open { right: 0; }
.trace-header {
    padding: 16px;
    background: #313244;
    border-bottom: 1px solid #45475a;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.trace-header h3 { margin: 0; font-size: 14px; }
.trace-close {
    background: none;
    border: none;
    color: #cdd6f4;
    cursor: pointer;
    font-size: 18px;
}
.trace-content { padding: 16px; }
.span-item {
    margin-bottom: 12px;
    padding: 12px;
    background: #313244;
    border-radius: 8px;
    border-left: 3px solid #89b4fa;
}
.span-item.agent { border-left-color: #a6e3a1; }
.span-item.generation { border-left-color: #f9e2af; }
.span-item.function { border-left-color: #cba6f7; }
.span-type {
    font-size: 10px;
    text-transform: uppercase;
    color: #6c7086;
    margin-bottom: 4px;
}
.span-name { font-weight: bold; color: #89dceb; }
.span-data {
    margin-top: 8px;
    padding: 8px;
    background: #1e1e2e;
    border-radius: 4px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
}
.span-time { color: #6c7086; font-size: 11px; }
.trace-summary {
    padding: 12px 16px;
    background: #45475a;
    margin: 0 16px 16px;
    border-radius: 8px;
}
.trace-summary-item { display: flex; justify-content: space-between; margin: 4px 0; }
</style>

<button class="trace-toggle" onclick="toggleTracePanel()">
    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
        <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
    </svg>
    Agent Trace
</button>

<div class="trace-panel" id="tracePanel">
    <div class="trace-header">
        <h3>Agent Trace Viewer</h3>
        <button class="trace-close" onclick="toggleTracePanel()">&times;</button>
    </div>
    <div class="trace-summary" id="traceSummary"></div>
    <div class="trace-content" id="traceContent"></div>
</div>

<script>
const TRACE_DATA = ''' + trace_json + ''';

function toggleTracePanel() {
    document.getElementById('tracePanel').classList.toggle('open');
}

function renderTrace() {
    const summary = document.getElementById('traceSummary');
    const content = document.getElementById('traceContent');

    if (!TRACE_DATA) {
        content.innerHTML = '<p>No trace data available</p>';
        return;
    }

    // Summary
    const spans = TRACE_DATA.spans || [];
    const agentSpans = spans.filter(s => s.type === 'agent').length;
    const genSpans = spans.filter(s => s.type === 'generation').length;
    const funcSpans = spans.filter(s => s.type === 'function').length;

    summary.innerHTML = `
        <div class="trace-summary-item"><span>Workflow</span><span>${TRACE_DATA.workflow_name || '-'}</span></div>
        <div class="trace-summary-item"><span>Agent Spans</span><span>${agentSpans}</span></div>
        <div class="trace-summary-item"><span>LLM Generations</span><span>${genSpans}</span></div>
        <div class="trace-summary-item"><span>Function Calls</span><span>${funcSpans}</span></div>
    `;

    // Spans
    let html = '';
    spans.forEach(span => {
        const typeClass = span.type || 'custom';
        const data = span.data || {};
        html += `
            <div class="span-item ${typeClass}">
                <div class="span-type">${span.type || 'span'}</div>
                <div class="span-name">${data.name || data.model || span.span_id?.slice(0, 8) || '-'}</div>
                ${data.input ? `<div class="span-data">${typeof data.input === 'string' ? data.input.slice(0, 200) : JSON.stringify(data.input).slice(0, 200)}...</div>` : ''}
                ${data.output ? `<div class="span-data">${typeof data.output === 'string' ? data.output.slice(0, 200) : JSON.stringify(data.output).slice(0, 200)}...</div>` : ''}
                ${data.usage ? `<div class="span-time">Tokens: ${data.usage.total_tokens || '-'}</div>` : ''}
            </div>
        `;
    });
    content.innerHTML = html || '<p>No spans recorded</p>';
}

document.addEventListener('DOMContentLoaded', renderTrace);
</script>
'''

    # Insert before </body>
    if '</body>' in html:
        html = html.replace('</body>', trace_viewer + '</body>')
    else:
        html += trace_viewer

    return html


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Excel files to web applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the API server
  python main.py serve

  # Convert a single file
  python main.py convert input.xlsx

  # Convert with custom output path
  python main.py convert input.xlsx -o output.html
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert an Excel file")
    convert_parser.add_argument(
        "file",
        help="Excel file to convert (.xlsx or .xlsm)",
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        help="Output HTML file path (default: same as input with .html extension)",
    )

    args = parser.parse_args()

    if args.command == "serve":
        run_api(host=args.host, port=args.port)
    elif args.command == "convert":
        asyncio.run(convert_file(args.file, args.output))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
