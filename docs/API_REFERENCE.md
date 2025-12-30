# XLS Agent - API Reference

> Comprehensive API documentation for agents, models, and tools

---

## Table of Contents

1. [Agents API](#agents-api)
2. [Models API](#models-api)
3. [Tools API](#tools-api)
4. [Orchestrator API](#orchestrator-api)
5. [Tracing API](#tracing-api)

---

## Agents API

### Analyzer Agent

```python
from src.agents import create_analyzer_agent, create_analyze_prompt

# Create agent
agent = create_analyzer_agent()
# Returns: Agent(name="Excel Analyzer", model="gpt-5-mini")

# Create prompt
prompt = create_analyze_prompt("/path/to/file.xlsx")
# Returns: str - Analysis prompt with file path

# Run agent
from agents import Runner
result = await Runner.run(agent, prompt)
# Returns: RunResult with final_output: ExcelAnalysis
```

#### Tools

| Function | Parameters | Returns |
|----------|------------|---------|
| `analyze_layout_structure` | `sheet_cells: list[dict]` | `dict` - Layout analysis |
| `analyze_io_mapping` | `sheet_cells: list[dict]` | `dict` - Input/output mapping |
| `build_formula_dependency_graph` | `formulas: list[dict]` | `dict` - Dependency graph |
| `analyze_vba_cell_mapping` | `vba_code: str` | `dict` - VBA cell references |

---

### Spec Agent

```python
from src.agents import create_spec_agent, create_spec_prompt

# Create agent
agent = create_spec_agent()
# Returns: Agent(name="TDD Spec Generator", model="gpt-5.2")

# Create prompt
prompt = create_spec_prompt(analysis_dict)
# Parameters:
#   analysis_dict: dict - ExcelAnalysis.model_dump()
# Returns: str - Spec generation prompt

# Run agent
result = await Runner.run(agent, prompt)
# Returns: RunResult with final_output: WebAppSpec
```

---

### Generator Agent

```python
from src.agents import (
    create_generator_agent,
    create_generation_prompt,
    generate_html_template,
)

# Create agent
agent = create_generator_agent()
# Returns: Agent(name="WebApp Generator", model="gpt-5.1-codex")

# Create prompt
prompt = create_generation_prompt(plan_dict, analysis_dict=None)
# Parameters:
#   plan_dict: dict - WebAppPlan.model_dump()
#   analysis_dict: Optional[dict] - ExcelAnalysis.model_dump()
# Returns: str - Generation prompt

# Generate HTML template
html = generate_html_template(webapp_plan)
# Parameters:
#   webapp_plan: WebAppPlan
# Returns: str - HTML template with Alpine.js setup

# Run agent
result = await Runner.run(agent, prompt)
# Returns: RunResult with final_output: GeneratedWebApp
```

#### Tools

| Function | Parameters | Returns |
|----------|------------|---------|
| `convert_formula` | `formula: str, cell_map: dict` | `FormulaConversionResult` |
| `check_formula_complexity` | `formula: str` | `FormulaComplexityResult` |
| `get_js_helpers` | None | `str` - Helper functions |

---

### Tester Agent

```python
from src.agents import create_tester_agent, create_test_prompt, TestEvaluation

# Create agent
agent = create_tester_agent()
# Returns: Agent(name="Code Tester", model="gpt-5-mini")

# Create prompt
prompt = create_test_prompt(
    html="<!DOCTYPE html>...",
    css="body { ... }",
    js="function appData() { ... }",
    formulas=[{"cell": "B10", "formula": "=B3*0.1"}],
    iteration=1,
)
# Returns: str - Evaluation prompt

# Run agent
result = await Runner.run(agent, prompt)
# Returns: RunResult with final_output: TestEvaluation
```

#### Validation Tools

```python
from src.agents.tester_agent import (
    validate_html_structure,
    validate_javascript_syntax,
    validate_print_styles,
    validate_korean_ui,
    check_formula_implementation,
)

# All tools use on_invoke_tool with JSON input
result = await validate_html_structure.on_invoke_tool(
    {},  # context
    json.dumps({"html": "<html>...</html>"})
)
# Returns: {"valid": bool, "issues": list[str]}

result = await validate_javascript_syntax.on_invoke_tool(
    {},
    json.dumps({"js_code": "function test() {...}"})
)
# Returns: {"valid": bool, "issues": list[str]}

result = await validate_print_styles.on_invoke_tool(
    {},
    json.dumps({"css_or_html": "@media print {...}"})
)
# Returns: {"valid": bool, "issues": list[str]}

result = await validate_korean_ui.on_invoke_tool(
    {},
    json.dumps({"html": "<button>계산</button>"})
)
# Returns: {"valid": bool, "korean_keywords_found": list[str], "issues": list[str]}

result = await check_formula_implementation.on_invoke_tool(
    {},
    json.dumps({
        "js_code": "salary * 0.1",
        "formula_list": '[{"cell": "B10", "formula": "=B3*0.1"}]'
    })
)
# Returns: {"implementation_rate": float, "details": list[dict]}
```

---

### Test Generator Agent

```python
from src.agents import (
    create_test_generator_agent,
    create_test_generation_prompt,
    GeneratedTestSuite,
    convert_to_static_test_suite,
)

# Create agent
agent = create_test_generator_agent()
# Returns: Agent(name="Test Generator", model="gpt-5-mini")

# Create prompt
prompt = create_test_generation_prompt(analysis, max_formulas=15)
# Parameters:
#   analysis: ExcelAnalysis
#   max_formulas: int - Limit formulas to test
# Returns: str - Test generation prompt

# Run agent
result = await Runner.run(agent, prompt)
# Returns: RunResult with final_output: GeneratedTestSuite

# Convert to static test suite
static_suite = convert_to_static_test_suite(
    generated_suite,
    source_file="test.xlsx"
)
# Returns: StaticTestSuite
```

---

## Models API

### ExcelAnalysis

```python
from src.models import ExcelAnalysis, SheetInfo, FormulaInfo, CellInfo

# Complete Excel file analysis
analysis = ExcelAnalysis(
    filename="test.xlsx",
    file_path="/path/to/test.xlsx",
    sheets=[
        SheetInfo(
            name="Sheet1",
            row_count=100,
            col_count=20,
            cells=[
                CellInfo(
                    cell="A1",
                    value="Header",
                    data_type="string",
                    is_formula=False,
                )
            ],
            formulas=[
                FormulaInfo(
                    cell="B10",
                    formula="=B3*0.1",
                    dependencies=["B3"],
                    formula_type="multiplication",
                )
            ],
            named_ranges={},
            print_settings=PrintSettings(
                paper_size="A4",
                orientation="portrait",
            ),
        )
    ],
    vba_modules=[],
    has_macros=False,
)

# Serialize
json_str = analysis.model_dump_json()
dict_form = analysis.model_dump()
```

---

### WebAppSpec

```python
from src.models import WebAppSpec

# TDD Specification
spec = WebAppSpec(
    app_name="급여 계산기",
    app_description="급여 기반 4대보험료 자동 계산",
    input_fields=[
        {
            "name": "salary",
            "type": "number",
            "label": "급여",
            "source_cell": "B3",
            "validation": {"min": 0, "required": True},
        }
    ],
    output_fields=[
        {
            "name": "tax",
            "format": "currency",
            "label": "세금",
            "source_cell": "B10",
            "source_formula": "=B3*0.1",
        }
    ],
    calculations=[
        {
            "name": "calculate_tax",
            "inputs": ["salary"],
            "output": "tax",
            "formula": "=B3*0.1",
            "logic": "세금 = 급여 × 10%",
        }
    ],
    expected_behaviors=[
        "급여 5000000원 입력 시 세금 500000원",
        "0 입력 시 세금 0원",
    ],
    boundary_conditions=[
        {
            "name": "zero_salary",
            "inputs": {"salary": 0},
            "expected_output": {"tax": 0},
            "description": "급여 0원 경계 테스트",
        }
    ],
    korean_labels=True,
    print_layout={
        "paper_size": "A4",
        "orientation": "portrait",
        "margins": {"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
    },
)
```

---

### GeneratedWebApp

```python
from src.models import GeneratedWebApp, TestSuite

# Generated web application
webapp = GeneratedWebApp(
    app_name="테스트 앱",
    source_excel="test.xlsx",
    html="""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body x-data="appData()">
    <!-- Content -->
</body>
</html>""",
    css="@media print { .no-print { display: none; } }",
    js="function appData() { return { salary: 0, get tax() { return this.salary * 0.1; } }; }",
    generation_iteration=1,
    test_results=None,
    feedback_applied=[],
)
```

---

### VerificationReport

```python
from src.models import VerificationReport

# Requirement verification report
report = VerificationReport(
    spec_name="급여 계산기",
    total_requirements=10,
    verified_requirements=9,
    unverified_requirements=1,
    verification_rate=0.9,
    requirement_results=[
        {
            "requirement": "급여 5000000원 입력 시 세금 500000원",
            "test_name": "behavior_0",
            "passed": True,
            "details": "Verified by static tests",
        }
    ],
    static_test_pass_rate=0.95,
    llm_evaluation_pass_rate=0.85,
    combined_pass_rate=0.91,  # 0.95*0.6 + 0.85*0.4
    blocking_issues=[],
    warnings=["Minor formatting issue"],
)
```

---

### ConversionResult

```python
from src.models import ConversionResult

# Final conversion output
result = ConversionResult(
    success=True,
    app=webapp,
    iterations_used=2,
    final_pass_rate=0.92,
    message="Successfully converted Excel to web application",
    conversation_trace={"turns": [...]},
    verification_report=report,
)

# Check result
if result.success:
    with open("output.html", "w") as f:
        f.write(result.app.html)
```

---

## Tools API

### Excel Analyzer

```python
from src.tools import analyze_excel

# Analyze Excel file
analysis = analyze_excel("/path/to/file.xlsx")
# Returns: dict - Raw analysis data

# Or using the function tool
from src.tools.excel_analyzer import analyze_excel_tool

result = await analyze_excel_tool.on_invoke_tool(
    {},
    json.dumps({"file_path": "/path/to/file.xlsx"})
)
```

---

### Test Generator

```python
from src.tools import extract_test_cases

# Extract test cases from Excel
suite = extract_test_cases(
    excel_path="/path/to/file.xlsx",
    analysis=analysis,  # ExcelAnalysis
)
# Returns: StaticTestSuite
```

---

### Static Test Runner

```python
from src.tools import run_static_tests

# Run static tests
result = await run_static_tests(
    test_suite=static_suite,  # StaticTestSuite
    html="<!DOCTYPE html>...",
    css="body {...}",
    js="function appData() {...}",
)
# Returns: StaticTestResult

# Result structure
print(f"Passed: {result.passed}/{result.total_tests}")
print(f"Pass Rate: {result.pass_rate:.1%}")
for failure in result.failures:
    print(f"  - {failure}")
```

---

## Orchestrator API

### ExcelToWebAppOrchestrator

```python
from src.orchestrator import (
    ExcelToWebAppOrchestrator,
    convert_excel_to_webapp,
    convert_excel_to_webapp_sync,
    ConversionProgress,
)

# Using class
orchestrator = ExcelToWebAppOrchestrator(
    max_iterations=3,      # Max improvement loops
    min_pass_rate=0.9,     # Success threshold (90%)
    progress_callback=None,
    verbose=True,
    run_static_tests=True,
)

result = await orchestrator.convert("/path/to/file.xlsx")

# Using convenience function (async)
result = await convert_excel_to_webapp(
    excel_path="/path/to/file.xlsx",
    progress_callback=lambda p: print(f"{p.stage}: {p.message} ({p.progress:.0%})"),
    verbose=True,
    max_iterations=3,
    run_static_tests=True,
)

# Synchronous wrapper
result = convert_excel_to_webapp_sync("/path/to/file.xlsx")
```

### Progress Callback

```python
from src.orchestrator import ConversionProgress, ProgressCallback

def on_progress(progress: ConversionProgress):
    print(f"[{progress.stage}] {progress.message} - {progress.progress:.0%}")

# Progress stages:
# - analyze: "Excel 파일 분석 중..." (10%)
# - spec: "TDD 스펙 생성 중..." (20%)
# - test_first: "테스트 케이스 생성 중 (TDD)..." (30%)
# - generate: "코드 생성 중..." (50-90%)
# - static_test: "정적 테스트 실행 중..."
# - test: "코드 평가 중..."
# - complete: "변환 완료!" (100%)
```

---

## Tracing API

### Conversation Hooks

```python
from src.tracing import ConversationCaptureHooks, ConversationTrace

# Create hooks
hooks = ConversationCaptureHooks(workflow_name="Excel-to-WebApp: test.xlsx")

# Use with Runner
from agents import Runner
result = await Runner.run(agent, prompt, hooks=hooks)

# Finalize and get trace
hooks.finalize()
trace = hooks.get_trace()

# Save trace
trace_dict = trace.to_dict()
with open("trace.json", "w") as f:
    json.dump(trace_dict, f, indent=2)
```

### Streaming Monitor

```python
from src.tracing import StreamingMonitorHooks, Colors

# Create monitor hooks for verbose output
monitor = StreamingMonitorHooks()

# Use with Runner
result = await Runner.run(agent, prompt, hooks=monitor)

# Colors utility
print(f"{Colors.BOLD}Bold text{Colors.RESET}")
print(f"{Colors.THINKING}Thinking...{Colors.RESET}")
print(f"{Colors.OUTPUT}Output text{Colors.RESET}")
print(f"{Colors.ERROR}Error message{Colors.RESET}")
```

### Trace Context

```python
from agents import trace, custom_span

# Wrap operations in trace
with trace("Pipeline: test.xlsx"):
    # ... pipeline operations

    with custom_span("Custom Operation"):
        # ... custom operation
        pass
```

---

## Type Definitions

### Enums

```python
from src.models import TestStatus

class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

### Type Aliases

```python
from src.orchestrator import ProgressCallback

ProgressCallback = Callable[[ConversionProgress], None]
```

---

## Error Handling

```python
from pydantic import ValidationError

try:
    spec = WebAppSpec(**invalid_data)
except ValidationError as e:
    print(f"Validation error: {e}")

# Conversion errors
result = await convert_excel_to_webapp(excel_path)
if not result.success:
    print(f"Error: {result.message}")
```

---

*Generated by /sc:index on 2025-12-30*
