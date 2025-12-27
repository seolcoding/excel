"""Main entry point for the Excel to WebApp Converter."""

import argparse
import asyncio
import sys
from pathlib import Path


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    import uvicorn
    from src.api import app

    uvicorn.run(app, host=host, port=port)


async def convert_file(excel_path: str, output_path: str = None):
    """Convert a single Excel file to a web app."""
    from src.orchestrator import convert_excel_to_webapp, ConversionProgress

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

    def progress_callback(progress: ConversionProgress):
        print(f"[{progress.progress:.0%}] {progress.message}")

    print(f"Converting: {excel_path}")
    print("-" * 40)

    result = await convert_excel_to_webapp(excel_path, progress_callback)

    if result.success:
        # Write HTML to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.app.html)

        print("-" * 40)
        print(f"Success! Output saved to: {output_path}")
        print(f"Iterations used: {result.iterations_used}")
        print(f"Test pass rate: {result.final_pass_rate:.0%}")
    else:
        print("-" * 40)
        print(f"Error: {result.message}")
        sys.exit(1)


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
