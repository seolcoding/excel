# Excel to WebApp Converter

> AI-powered tool that converts Excel files (.xlsx, .xlsm) to standalone web applications

[![Deploy Demo](https://github.com/seolcoding/excel/actions/workflows/deploy.yml/badge.svg)](https://github.com/seolcoding/excel/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Demo

**[Live Demo](https://excel.seolcoding.com)** - Excel 파일과 변환된 웹앱 비교

| Excel File | Generated WebApp |
|------------|------------------|
| 4대보험_자동계산기_엑셀템플릿.xlsx | [4대보험 계산기](https://excel.seolcoding.com/demos/insurance-calculator.html) |
| 종합소득세 엑셀 간이 계산기 v2.1.xlsx | [종합소득세 계산기](https://excel.seolcoding.com/demos/tax-calculator.html) |
| 엑셀 자동화 견적서 v1.0.xlsm | [자동화 견적서](https://excel.seolcoding.com/demos/quote-form.html) |

## Features

- **Excel Analysis**: 셀 구조, 수식, VBA 매크로 자동 분석
- **Smart Conversion**: 간단한 수식은 직접 변환, 복잡한 수식은 GPT-5.2로 변환
- **VBA to JavaScript**: VBA 매크로를 JavaScript로 자동 변환
- **Print Perfect**: Excel 인쇄 레이아웃 그대로 재현 (A4, margins)
- **Korean-First**: 모든 UI 한국어 지원

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Analyzer Agent (gpt-5-mini)                             │
│     └─ Excel 파일 분석 → ExcelAnalysis                      │
│                         ↓                                    │
│  2. Planner Agent (gpt-5.2)                                 │
│     └─ 웹앱 설계 → WebAppPlan                               │
│                         ↓                                    │
│  3. Generator Agent (gpt-5.2)                               │
│     └─ 코드 생성 → HTML/CSS/JS                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, OpenAI Agents SDK
- **Excel Parsing**: openpyxl, formulas, oletools
- **Frontend Output**: Bootstrap 5, Alpine.js (CDN-based, no build)
- **LLM**: GPT-5.2 (SOTA), GPT-5-mini

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/xls-agent.git
cd xls-agent

# Install dependencies (using uv)
uv sync

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key"
```

## Usage

### CLI

```bash
# Convert a single file
uv run python main.py convert input.xlsx -o output.html

# Start API server
uv run python main.py serve --port 8000
```

### API

```bash
# Upload and convert
curl -X POST http://localhost:8000/api/v1/convert \
  -F "file=@input.xlsx"

# Check status
curl http://localhost:8000/api/v1/status/{job_id}

# Download result
curl http://localhost:8000/api/v1/download/{job_id} -o output.html
```

### Python

```python
import asyncio
from src.orchestrator import convert_excel_to_webapp

async def main():
    result = await convert_excel_to_webapp("input.xlsx")
    if result.success:
        with open("output.html", "w") as f:
            f.write(result.app.html)
        print(f"Success! Pass rate: {result.final_pass_rate:.0%}")

asyncio.run(main())
```

## Project Structure

```
xls_agent/
├── main.py                    # CLI entry point
├── src/
│   ├── models/                # Pydantic data models
│   │   ├── analysis.py        # ExcelAnalysis
│   │   ├── plan.py            # WebAppPlan
│   │   └── output.py          # GeneratedWebApp
│   ├── tools/                 # Core utilities
│   │   ├── excel_analyzer.py  # Excel parsing
│   │   ├── formula_converter.py # Formula → JS
│   │   └── vba_converter.py   # VBA → JS
│   ├── agents/                # OpenAI Agents
│   │   ├── analyzer_agent.py
│   │   ├── planner_agent.py
│   │   └── generator_agent.py
│   ├── orchestrator.py        # Pipeline coordination
│   ├── templates/             # Jinja2 templates
│   └── api/                   # FastAPI endpoints
├── excel_files/               # Sample Excel files
├── demos/                     # Generated demo pages
└── docs/                      # Documentation
```

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
