# XLS Agent - Project Index

> Excel to WebApp Conversion Pipeline with TDD and LLM-as-a-Judge

**Last Updated**: 2025-12-30
**Version**: 0.1.0
**Status**: Active Development

---

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture](#architecture) | TDD Pipeline overview |
| [Directory Structure](#directory-structure) | File organization |
| [Agents](#agents) | AI agent components |
| [Models](#models) | Pydantic data models |
| [Tools](#tools) | Utility functions |
| [Testing](#testing) | Test suite overview |
| [API](#api) | REST API endpoints |

---

## Architecture

### TDD Pipeline Flow

```
Excel File (.xlsx/.xlsm)
         │
         ▼
┌─────────────────┐
│  Analyzer Agent │ ← gpt-5-mini
│  (Excel 분석)    │
└────────┬────────┘
         │ ExcelAnalysis
         ▼
┌─────────────────┐
│   Spec Agent    │ ← gpt-5.2
│  (TDD 스펙 생성) │
└────────┬────────┘
         │ WebAppSpec
         ▼
┌─────────────────┐
│  Test Generator │ ← gpt-5-mini
│ (테스트 케이스)   │
└────────┬────────┘
         │ StaticTestSuite
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Generator Agent │◄────│  Tester Agent   │
│  (코드 생성)     │     │ (LLM-as-a-Judge)│
│  gpt-5.1-codex  │     │   gpt-5-mini    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │   pass_rate >= 90%?   │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
      YES ▼                   NO ▼
┌─────────────────┐    ┌─────────────────┐
│   Output HTML   │    │ Iterate (max 3) │
│ + Verification  │    │ with feedback   │
│    Report       │    └─────────────────┘
└─────────────────┘
```

### Key Features

- **TDD-Driven**: Spec → Tests → Code → Verify
- **LLM-as-a-Judge**: AI-powered code evaluation
- **Static Tests**: Deterministic formula verification (60% weight)
- **LLM Evaluation**: Quality assessment (40% weight)
- **Korean UI**: All labels in Korean
- **Print Layout**: A4 paper optimization

---

## Directory Structure

```
xls_agent/
├── src/                          # Source code
│   ├── agents/                   # AI agent definitions
│   │   ├── __init__.py          # Agent exports
│   │   ├── analyzer_agent.py    # Excel structure extraction
│   │   ├── spec_agent.py        # TDD specification generation
│   │   ├── planner_agent.py     # Legacy: WebApp planning
│   │   ├── generator_agent.py   # HTML/CSS/JS generation
│   │   ├── tester_agent.py      # LLM-as-a-Judge evaluation
│   │   └── test_generator_agent.py  # Test case generation
│   │
│   ├── models/                   # Pydantic data models
│   │   ├── __init__.py          # Model exports
│   │   ├── analysis.py          # ExcelAnalysis, SheetInfo
│   │   ├── plan.py              # WebAppPlan, ComponentSpec
│   │   ├── output.py            # WebAppSpec, ConversionResult
│   │   └── test_case.py         # TestSuite, TestCase
│   │
│   ├── tools/                    # Utility functions
│   │   ├── __init__.py          # Tool exports
│   │   ├── excel_analyzer.py    # openpyxl-based parsing
│   │   ├── formula_converter.py # Excel → JS conversion
│   │   ├── vba_converter.py     # VBA → JS conversion
│   │   ├── test_generator.py    # Test case extraction
│   │   ├── static_test_runner.py # Node.js test execution
│   │   └── e2e_test_runner.py   # Playwright tests (unused)
│   │
│   ├── tracing/                  # Observability
│   │   ├── __init__.py          # Tracing exports
│   │   ├── conversation_hooks.py # LLM conversation capture
│   │   ├── streaming_monitor.py  # Real-time monitoring
│   │   └── json_processor.py     # Trace JSON generation
│   │
│   ├── api/                      # FastAPI routes
│   │   ├── __init__.py
│   │   └── routes.py            # REST endpoints
│   │
│   ├── templates/               # Jinja2 templates
│   │   └── __init__.py
│   │
│   ├── generators/              # Code generators
│   │   └── __init__.py
│   │
│   └── orchestrator.py          # Pipeline coordinator
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── fake_model.py            # FakeModel for mocking
│   ├── helpers.py               # Test utilities
│   ├── test_output_models.py    # Model validation tests
│   ├── test_tracing.py          # Tracing system tests
│   └── agents/                  # Agent unit tests
│       ├── __init__.py
│       ├── test_spec_agent.py
│       ├── test_generator_agent.py
│       ├── test_tester_agent.py
│       └── test_communication.py
│
├── docs/                         # Documentation
│   ├── PROJECT_INDEX.md         # This file
│   └── TDD_PIPELINE_ARCHITECTURE.md
│
├── demos/                        # Generated demo apps
├── traces/                       # Agent execution traces
├── excel_files/                  # Sample Excel files
├── refs/                         # Reference documentation
│   └── openai-agents-python/    # SDK reference
│
├── main.py                       # CLI entry point
├── convert_top10.py             # Batch conversion script
├── generate_traces.py           # Trace generation
├── index.html                    # Web interface
├── trace-viewer.html            # Trace viewer UI
│
├── pyproject.toml               # Project config
├── uv.lock                      # Dependency lock
├── CLAUDE.md                    # AI assistant config
└── README.md                    # Project readme
```

---

## Agents

### Agent Summary

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| Analyzer | gpt-5-mini | Extract Excel structure | ExcelAnalysis |
| Spec | gpt-5.2 | Create TDD specification | WebAppSpec |
| Test Generator | gpt-5-mini | Generate test cases | StaticTestSuite |
| Generator | gpt-5.1-codex | Produce HTML/CSS/JS | GeneratedWebApp |
| Tester | gpt-5-mini | Evaluate code quality | TestEvaluation |
| Planner | gpt-5.2 | Legacy: Plan web app | WebAppPlan |

### Agent Details

#### Analyzer Agent (`analyzer_agent.py`)
- **Model**: `gpt-5-mini`
- **Tools**: `analyze_excel`, `get_sheet_cells`, `analyze_layout_structure`, `analyze_io_mapping`, `build_formula_dependency_graph`, `analyze_vba_cell_mapping`
- **Output**: `ExcelAnalysis`
- **Purpose**: Extract structure, formulas, and VBA from Excel files

#### Spec Agent (`spec_agent.py`)
- **Model**: `gpt-5.2`
- **Output**: `WebAppSpec`
- **Purpose**: Create PRD-style specification with testable requirements

#### Generator Agent (`generator_agent.py`)
- **Model**: `gpt-5.1-codex`
- **Tools**: `convert_formula`, `check_formula_complexity`, `get_js_helpers`
- **Output**: `GeneratedWebApp`
- **Purpose**: Generate complete HTML/CSS/JS web application

#### Tester Agent (`tester_agent.py`)
- **Model**: `gpt-5-mini`
- **Tools**: `validate_html_structure`, `validate_javascript_syntax`, `validate_print_styles`, `validate_korean_ui`, `check_formula_implementation`
- **Output**: `TestEvaluation`
- **Purpose**: LLM-as-a-Judge pattern for code quality evaluation

---

## Models

### Core Models

| Model | File | Description |
|-------|------|-------------|
| `ExcelAnalysis` | `analysis.py` | Complete Excel file analysis |
| `WebAppSpec` | `output.py` | TDD specification document |
| `WebAppPlan` | `plan.py` | Web application design plan |
| `GeneratedWebApp` | `output.py` | Generated HTML/CSS/JS code |
| `TestEvaluation` | `output.py` | LLM evaluation result |
| `VerificationReport` | `output.py` | Requirement verification |
| `ConversionResult` | `output.py` | Final conversion output |

### Model Hierarchy

```
ExcelAnalysis
├── SheetInfo[]
│   ├── CellInfo[]
│   ├── FormulaInfo[]
│   └── PrintSettings
└── VBAModule[]

WebAppSpec
├── input_fields[]
├── output_fields[]
├── calculations[]
├── expected_behaviors[]
├── boundary_conditions[]
└── print_layout

WebAppPlan
├── ComponentSpec[]
│   ├── FormField[]
│   └── OutputField[]
├── JavaScriptFunction[]
└── PrintLayout

GeneratedWebApp
├── html: str
├── css: str
├── js: str
└── test_results: TestSuite

ConversionResult
├── success: bool
├── app: GeneratedWebApp
├── verification_report: VerificationReport
└── conversation_trace: dict
```

---

## Tools

### Tool Functions

| Tool | File | Description |
|------|------|-------------|
| `analyze_excel` | `excel_analyzer.py` | Parse Excel with openpyxl |
| `extract_test_cases` | `test_generator.py` | Generate test cases from Excel |
| `run_static_tests` | `static_test_runner.py` | Execute tests with Node.js |
| `convert_formula` | `formula_converter.py` | Excel formula → JavaScript |
| `convert_vba` | `vba_converter.py` | VBA macro → JavaScript |

---

## Testing

### Test Structure

```
tests/
├── conftest.py           # Fixtures (FakeModel, sample data)
├── fake_model.py         # SDK-pattern mock model
├── helpers.py            # Test utilities
├── test_output_models.py # 29 tests - Pydantic validation
├── test_tracing.py       # 24 tests - Observability
└── agents/
    ├── test_spec_agent.py      # 22 tests
    ├── test_generator_agent.py # 22 tests
    ├── test_tester_agent.py    # 27 tests
    └── test_communication.py   # 16 tests
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/agents/test_spec_agent.py

# Run with verbose output
uv run pytest -v
```

### Test Count: 160 tests

---

## API

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/convert` | Convert Excel to WebApp |
| GET | `/status/{task_id}` | Check conversion status |
| GET | `/download/{task_id}` | Download generated HTML |

### Usage

```bash
# Start server
uv run uvicorn src.api.routes:app --reload

# Convert Excel
curl -X POST http://localhost:8000/convert \
  -F "file=@sample.xlsx"
```

---

## Configuration

### Environment

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `MAX_ITERATIONS` | Max improvement loops | 3 |
| `MIN_PASS_RATE` | Success threshold | 0.9 |

### CLAUDE.md Settings

```yaml
Model Selection:
  - SOTA: gpt-5.2
  - Code Generation: gpt-5.1-codex
  - Cost-Optimized: gpt-5-mini

TDD Pipeline:
  - Spec-First Development
  - 90% Pass Rate Threshold
  - Static:LLM Weight = 60:40
```

---

## Deployment

### GitHub Pages

- **Repository**: seolcoding/excel
- **URL**: https://seolcoding.github.io/excel/
- **Custom Domain**: excel.seolcoding.com

### Build

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Generate demos
uv run python convert_top10.py
```

---

## References

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [TDD Pipeline Architecture](./TDD_PIPELINE_ARCHITECTURE.md)
- [SDK Reference](../refs/openai-agents-python/)

---

## Contributing

1. Create feature branch from `main`
2. Write tests first (TDD)
3. Implement changes
4. Run `uv run pytest`
5. Create pull request

---

*Generated by /sc:index on 2025-12-30*
