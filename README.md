# Excel to WebApp Converter

> AI-powered tool that converts Excel files (.xlsx, .xlsm) to standalone web applications

[![Deploy Demo](https://github.com/seolcoding/excel/actions/workflows/deploy.yml/badge.svg)](https://github.com/seolcoding/excel/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Demo

**[Live Demo](https://excel.seolcoding.com)** - 470개 엑셀 파일 분석 → Top 10 선정 → AI Agent 변환

### Top 10 Demos

| # | Name | Category | Formulas | Links |
|---|------|----------|----------|-------|
| 01 | 간이영수증 | 수식풍부 | 233 | [Demo](https://excel.seolcoding.com/demos/01-receipt.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=01) |
| 02 | 종합소득세 계산기 | 세금계산 | 24 | [Demo](https://excel.seolcoding.com/demos/02-income-tax.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=02) |
| 03 | 4대보험 자동계산기 | 보험/급여 | 6 | [Demo](https://excel.seolcoding.com/demos/03-insurance.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=03) |
| 04 | 거래명세표 (자동계산) | 자동화 | - | [Demo](https://excel.seolcoding.com/demos/04-invoice-auto.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=04) |
| 05 | 계산서 | 세무/회계 | - | [Demo](https://excel.seolcoding.com/demos/05-statement.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=05) |
| 06 | 인사기록카드 | 인사/HR | - | [Demo](https://excel.seolcoding.com/demos/06-hr-record.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=06) |
| 07 | 거래명세표 | 거래/B2B | - | [Demo](https://excel.seolcoding.com/demos/07-invoice.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=07) |
| 08 | 자금집행품의서 | 재무/자금 | - | [Demo](https://excel.seolcoding.com/demos/08-fund-request.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=08) |
| 09 | CPM 공정표 | 건설/공사 | - | [Demo](https://excel.seolcoding.com/demos/09-construction.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=09) |
| 10 | 가계부 (자동화) | 개인용 | - | [Demo](https://excel.seolcoding.com/demos/10-household.html) · [Trace](https://excel.seolcoding.com/traces/trace-viewer.html?demo=10) |

## Features

- **Excel Analysis**: 셀 구조, 수식, VBA 매크로 자동 분석
- **Smart Conversion**: 간단한 수식은 직접 변환, 복잡한 수식은 LLM으로 변환
- **VBA to JavaScript**: VBA 매크로를 JavaScript로 자동 변환
- **Print Perfect**: Excel 인쇄 레이아웃 그대로 재현 (A4, margins)
- **Agent Trace Viewer**: 전체 LLM 대화 내역 및 Agent 실행 과정 시각화
- **Korean-First**: 모든 UI 한국어 지원

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Excel Analyzer Agent                                     │
│     └─ Excel 파일 분석 → ExcelAnalysis                      │
│                         ↓                                    │
│  2. WebApp Planner Agent                                     │
│     └─ 웹앱 설계 → WebAppPlan                               │
│                         ↓                                    │
│  3. Code Generator Agent                                     │
│     └─ 코드 생성 → HTML/CSS/JS                              │
│                                                              │
│  [Tracing: Full LLM conversation capture]                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: Python 3.12+, OpenAI Agents SDK
- **Excel Parsing**: openpyxl, xlrd (for .xls), LibreOffice (xls→xlsx conversion)
- **Frontend Output**: Bootstrap 5, Alpine.js (CDN-based, no build)
- **LLM**: GPT-4o (via OpenAI Agents SDK)
- **Tracing**: Custom ConversationCaptureHooks + JsonTracingProcessor

## Installation

```bash
# Clone repository
git clone https://github.com/seolcoding/excel.git
cd excel

# Install dependencies (using uv)
uv sync

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key"
```

## Usage

### Python

```python
import asyncio
from src.orchestrator import ExcelToWebAppOrchestrator

async def main():
    orchestrator = ExcelToWebAppOrchestrator()
    result = await orchestrator.convert("input.xlsx")

    if result.success:
        with open("output.html", "w") as f:
            f.write(result.app.html_code)
        print(f"Success! Pass rate: {result.final_pass_rate:.0%}")

        # Access conversation trace
        if result.conversation_trace:
            print(f"Agents used: {result.conversation_trace['agents_used']}")
            print(f"Total tokens: {result.conversation_trace['total_tokens']}")

asyncio.run(main())
```

## Project Structure

```
xls_agent/
├── src/
│   ├── models/                # Pydantic data models
│   │   ├── analysis.py        # ExcelAnalysis
│   │   ├── plan.py            # WebAppPlan
│   │   └── output.py          # GeneratedWebApp, ConversionResult
│   ├── tools/                 # Core utilities
│   │   ├── excel_analyzer.py  # Excel parsing
│   │   └── formula_converter.py # Formula → JS
│   ├── agents/                # OpenAI Agents
│   │   ├── analyzer.py        # Excel Analyzer Agent
│   │   ├── planner.py         # WebApp Planner Agent
│   │   └── generator.py       # Code Generator Agent
│   ├── tracing/               # Conversation capture
│   │   ├── conversation_hooks.py  # RunHooks for LLM capture
│   │   └── json_processor.py  # Trace export
│   └── orchestrator.py        # Pipeline coordination
├── demos/                     # Generated demo pages (10 demos)
├── traces/                    # Agent trace viewer & JSON files
│   ├── trace-viewer.html      # Full-page trace viewer
│   └── *.json                 # Trace data per demo
├── excel_files/               # Source Excel files
└── index.html                 # Landing page
```

## Agent Trace Viewer

Each demo includes a trace viewer showing:

- **Stats**: Agents used, LLM calls, total tokens, duration
- **LLM Calls**: System prompt, user input, assistant response per agent
- **Tool Calls**: Function inputs/outputs with timing

Access via: `traces/trace-viewer.html?demo=01`

## Supported Excel Features

| Feature | Support |
|---------|---------|
| Basic formulas (SUM, IF, AVERAGE) | Direct conversion |
| Complex formulas (VLOOKUP, SUMIF) | LLM conversion |
| VBA macros | LLM conversion |
| Print settings | Full support |
| Cell formatting | Partial |
| Charts | Not supported |

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `MAX_ITERATIONS` | Max generation iterations | 3 |
| `MIN_PASS_RATE` | Minimum test pass rate | 0.9 |

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request
