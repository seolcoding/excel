# Excel → Web App Agent: Final Architecture

> POC (Proof of Concept) - 엑셀 파일을 웹앱으로 변환하는 AI 에이전트 시스템

## 1. 프로젝트 개요

### 1.1 목표
- **Input**: Excel 파일 (.xlsx, .xlsm)
- **Output**: 독립 실행 가능한 웹앱 (HTML + CSS + JS)
- **검증**: 엑셀의 데이터, 수식, VBA, 차트가 웹앱으로 정확히 변환됨

### 1.2 핵심 원칙
- **Vanilla Only**: 프레임워크 없이 순수 HTML/CSS/JS
- **LLM 최적화**: LLM이 가장 정확하게 생성하는 코드 스택 사용
- **빌드 불필요**: CDN 기반, 즉시 실행 가능
- **POC 수준**: 관리자 UI 없음, 최소 기능만 구현

---

## 2. 기술 스택

### 2.1 Backend (Python)

```
openai-agents>=0.2.9      # 멀티 에이전트 오케스트레이션
openpyxl>=3.1.0           # Excel 파싱 (구조, 차트)
pandas>=2.0.0             # 데이터 처리
formulas>=1.3.0           # Excel 수식 파싱/변환
oletools>=0.60            # VBA 매크로 추출
fastapi>=0.100.0          # API 서버
uvicorn>=0.23.0           # ASGI 서버
python-multipart>=0.0.6   # 파일 업로드
```

### 2.2 Frontend - POC UI (Vanilla)

```html
<!-- 단순 파일 업로드 + 프리뷰 -->
Bootstrap 5 (CDN)         # UI 컴포넌트
Vanilla JS                # 로직
```

### 2.3 Generated Output (웹앱)

```html
Bootstrap 5 (CDN)         # 레이아웃/컴포넌트
Alpine.js (CDN)           # 상태 관리/인터랙션
Chart.js (CDN)            # 차트 렌더링
Vanilla JS                # 수식 로직 (Excel → JS 변환)
```

---

## 3. 에이전트 아키텍처

### 3.1 디자인 패턴 (Azure AI Agent Patterns 기반)

| 패턴 | 적용 위치 | 이유 |
|------|----------|------|
| **Sequential** | 전체 파이프라인 | 분석→설계→생성→검증 순차 의존성 |
| **Handoff** | Planner → Generators | 엑셀 유형에 따른 전문 생성기 라우팅 |
| **Maker-Checker** | Code Generator ↔ Reviewer | 코드 품질 보장, 반복 개선 |

### 3.2 에이전트 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Excel File]                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. ANALYZER AGENT                                       │   │
│  │     Instructions: 엑셀 파일의 구조, 데이터, 수식,         │   │
│  │                   VBA, 차트를 분석하여 메타데이터 추출     │   │
│  │     Tools:                                               │   │
│  │       - analyze_structure (openpyxl)                     │   │
│  │       - parse_formulas (formulas)                        │   │
│  │       - extract_vba (oletools)                           │   │
│  │       - extract_charts (openpyxl)                        │   │
│  │     Output: ExcelAnalysis (structured)                   │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2. PLANNER AGENT                                        │   │
│  │     Instructions: 분석 결과를 기반으로 웹앱 유형 결정,    │   │
│  │                   컴포넌트 구조 및 레이아웃 설계          │   │
│  │     Tools: None (LLM reasoning only)                     │   │
│  │     Output: WebAppPlan (structured)                      │   │
│  │                                                          │   │
│  │     Handoff Decision:                                    │   │
│  │       - 단순 데이터 → Table Generator                    │   │
│  │       - 차트 포함 → Dashboard Generator                  │   │
│  │       - 수식 중심 → Calculator Generator                 │   │
│  │       - 입력 폼 → Form Generator                         │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │ (Handoff)                             │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  3. CODE GENERATOR AGENTS (Specialized)                  │   │
│  │                                                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │   Table     │ │  Dashboard  │ │ Calculator  │        │   │
│  │  │  Generator  │ │  Generator  │ │  Generator  │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  │                                                          │   │
│  │     Tools:                                               │   │
│  │       - generate_html                                    │   │
│  │       - generate_chart_config                            │   │
│  │       - convert_formula_to_js                            │   │
│  │     Output: GeneratedCode (html, css, js)                │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  4. MAKER-CHECKER LOOP                                   │   │
│  │                                                          │   │
│  │     ┌──────────────┐         ┌──────────────┐           │   │
│  │     │    Coder     │ ──────▶ │   Reviewer   │           │   │
│  │     │   (Maker)    │ ◀────── │  (Checker)   │           │   │
│  │     └──────────────┘         └──────────────┘           │   │
│  │                                                          │   │
│  │     Reviewer Checks:                                     │   │
│  │       - HTML 문법 오류                                   │   │
│  │       - 데이터 바인딩 정확성                              │   │
│  │       - 수식 변환 검증                                   │   │
│  │       - 차트 설정 유효성                                 │   │
│  │                                                          │   │
│  │     Max Iterations: 3                                    │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  5. OUTPUT AGENT                                         │   │
│  │     Instructions: 최종 코드 패키징 및 프리뷰 생성         │   │
│  │     Tools:                                               │   │
│  │       - package_webapp                                   │   │
│  │       - generate_preview                                 │   │
│  │     Output: WebAppBundle (index.html + assets)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         │                                       │
│                         ▼                                       │
│                  [Generated Web App]                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 도구 (Tools) 상세 정의

### 4.1 Analyzer Tools

```python
@function_tool
async def analyze_structure(file_path: str) -> dict:
    """
    Excel 파일 구조 분석

    Returns:
        {
            "sheets": [{"name": str, "rows": int, "cols": int}],
            "data_types": {"A1": "number", "B1": "string", ...},
            "merged_cells": [...],
            "named_ranges": {...}
        }
    """

@function_tool
async def parse_formulas(file_path: str) -> dict:
    """
    Excel 수식 파싱 및 의존성 분석

    Returns:
        {
            "formulas": [
                {"cell": "C1", "formula": "=A1+B1", "dependencies": ["A1", "B1"]}
            ],
            "formula_types": {"SUM": 5, "IF": 3, "VLOOKUP": 1}
        }
    """

@function_tool
async def extract_vba(file_path: str) -> dict:
    """
    VBA 매크로 코드 추출

    Returns:
        {
            "modules": [
                {"name": "Module1", "code": "Sub Calculate()..."}
            ],
            "functions": ["Calculate", "FormatData"],
            "has_macros": True
        }
    """

@function_tool
async def extract_charts(file_path: str) -> dict:
    """
    차트 메타데이터 추출

    Returns:
        {
            "charts": [
                {
                    "type": "barChart",
                    "title": "Sales by Month",
                    "data_range": "A1:B12",
                    "series": [...]
                }
            ]
        }
    """
```

### 4.2 Generator Tools

```python
@function_tool
async def convert_formula_to_js(excel_formula: str) -> str:
    """
    Excel 수식을 JavaScript 함수로 변환

    Example:
        Input: "=SUM(A1:A10)"
        Output: "function sum_a1_a10() { return data.slice(0,10).reduce((a,b) => a+b, 0); }"
    """

@function_tool
async def generate_chart_config(chart_meta: dict) -> str:
    """
    Chart.js 설정 코드 생성

    Returns: Chart.js configuration object as string
    """
```

---

## 5. 데이터 모델

### 5.1 분석 결과 (Pydantic)

```python
from pydantic import BaseModel
from typing import Optional

class SheetInfo(BaseModel):
    name: str
    rows: int
    cols: int
    data_sample: list[list]  # 첫 10행

class FormulaInfo(BaseModel):
    cell: str
    formula: str
    dependencies: list[str]
    result_type: str  # number, string, boolean

class ChartInfo(BaseModel):
    type: str  # bar, line, pie, etc.
    title: Optional[str]
    data_range: str
    series_count: int

class VBAModule(BaseModel):
    name: str
    code: str
    functions: list[str]

class ExcelAnalysis(BaseModel):
    file_name: str
    sheets: list[SheetInfo]
    formulas: list[FormulaInfo]
    charts: list[ChartInfo]
    vba_modules: list[VBAModule]
    complexity_score: int  # 1-10
```

### 5.2 생성 계획

```python
class ComponentPlan(BaseModel):
    type: str  # table, chart, form, calculator
    data_source: str  # sheet name or range
    interactive: bool

class WebAppPlan(BaseModel):
    app_type: str  # dashboard, form, calculator, report
    layout: str  # single-page, tabs, sections
    components: list[ComponentPlan]
    requires_input: bool
    requires_calculation: bool
```

### 5.3 생성 결과

```python
class GeneratedCode(BaseModel):
    html: str
    css: str  # inline or embedded
    js: str

class WebAppBundle(BaseModel):
    index_html: str  # 완성된 단일 HTML 파일
    preview_url: Optional[str]  # data URI or temp file
```

---

## 6. API 엔드포인트

### 6.1 POC API (FastAPI)

```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse

app = FastAPI(title="Excel to WebApp Agent")

@app.post("/convert")
async def convert_excel(file: UploadFile = File(...)) -> dict:
    """
    Excel 파일을 웹앱으로 변환

    Returns:
        {
            "success": True,
            "webapp_html": "<html>...</html>",
            "analysis": {...},
            "plan": {...}
        }
    """

@app.post("/convert/stream")
async def convert_excel_stream(file: UploadFile = File(...)):
    """
    스트리밍 변환 (진행 상황 실시간 전송)

    Yields:
        {"stage": "analyzing", "progress": 20}
        {"stage": "planning", "progress": 40}
        {"stage": "generating", "progress": 70}
        {"stage": "reviewing", "progress": 90}
        {"stage": "complete", "webapp_html": "..."}
    """

@app.get("/preview/{job_id}")
async def get_preview(job_id: str) -> HTMLResponse:
    """
    생성된 웹앱 프리뷰
    """
```

---

## 7. 프로젝트 구조

```
xls_agent/
├── docs/
│   ├── ARCHITECTURE.md          # 이 문서
│   ├── openai_agents_sdk_reference.md
│   └── tool_stack_research.md
│
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Analyzer Agent
│   │   ├── planner.py           # Planner Agent
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   ├── table.py         # Table Generator
│   │   │   ├── dashboard.py     # Dashboard Generator
│   │   │   └── calculator.py    # Calculator Generator
│   │   ├── reviewer.py          # Code Reviewer Agent
│   │   └── orchestrator.py      # 전체 워크플로우 오케스트레이션
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── excel_parser.py      # openpyxl 기반 파싱
│   │   ├── formula_converter.py # formulas 기반 변환
│   │   ├── vba_extractor.py     # oletools 기반 추출
│   │   └── chart_extractor.py   # 차트 메타데이터 추출
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── analysis.py          # ExcelAnalysis 등
│   │   ├── plan.py              # WebAppPlan 등
│   │   └── output.py            # GeneratedCode 등
│   │
│   ├── templates/
│   │   ├── base.html            # 기본 HTML 템플릿
│   │   ├── table.html           # 테이블 컴포넌트
│   │   ├── chart.html           # 차트 컴포넌트
│   │   └── form.html            # 폼 컴포넌트
│   │
│   └── api/
│       ├── __init__.py
│       └── main.py              # FastAPI 앱
│
├── frontend/                    # POC UI (Vanilla)
│   └── index.html               # 파일 업로드 + 프리뷰
│
├── tests/
│   ├── sample_files/            # 테스트용 엑셀 파일
│   │   ├── simple_data.xlsx
│   │   ├── with_formulas.xlsx
│   │   ├── with_charts.xlsx
│   │   └── with_vba.xlsm
│   └── test_agents.py
│
├── pyproject.toml
├── README.md
└── .env.example
```

---

## 8. 생성될 웹앱 예시

### 8.1 단순 데이터 테이블

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <h1 class="mb-4">Sales Report</h1>

        <div class="card">
            <div class="card-body">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Month</th>
                            <th>Revenue</th>
                            <th>Expenses</th>
                            <th>Profit</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>January</td><td>$10,000</td><td>$7,000</td><td>$3,000</td></tr>
                        <tr><td>February</td><td>$12,000</td><td>$8,000</td><td>$4,000</td></tr>
                        <!-- ... -->
                    </tbody>
                    <tfoot class="table-secondary">
                        <tr>
                            <th>Total</th>
                            <th>$120,000</th>
                            <th>$85,000</th>
                            <th>$35,000</th>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

### 8.2 차트 포함 대시보드

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-light">
    <div class="container-fluid py-4">
        <h1 class="mb-4">Sales Dashboard</h1>

        <div class="row">
            <!-- KPI Cards -->
            <div class="col-md-3">
                <div class="card text-white bg-primary mb-3">
                    <div class="card-body">
                        <h6 class="card-title">Total Revenue</h6>
                        <h2 class="card-text">$120,000</h2>
                    </div>
                </div>
            </div>
            <!-- ... more cards -->
        </div>

        <div class="row">
            <!-- Chart -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">Monthly Revenue</div>
                    <div class="card-body">
                        <canvas id="revenueChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('revenueChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Revenue',
                    data: [10000, 12000, 11000, 14000, 13000, 15000],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)'
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } }
            }
        });
    </script>
</body>
</html>
```

### 8.3 수식 계산기

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loan Calculator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js" defer></script>
</head>
<body class="bg-light">
    <div class="container py-5" x-data="calculator()">
        <h1 class="mb-4">Loan Calculator</h1>

        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">Loan Amount ($)</label>
                    <input type="number" class="form-control" x-model="principal" @input="calculate()">
                </div>

                <div class="mb-3">
                    <label class="form-label">Interest Rate (%)</label>
                    <input type="number" class="form-control" x-model="rate" @input="calculate()">
                </div>

                <div class="mb-3">
                    <label class="form-label">Term (months)</label>
                    <input type="number" class="form-control" x-model="term" @input="calculate()">
                </div>

                <hr>

                <div class="alert alert-success">
                    <h5>Monthly Payment</h5>
                    <h2 x-text="'$' + monthlyPayment.toFixed(2)"></h2>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Excel 수식 변환: =PMT(rate/12, term, -principal)
        function calculator() {
            return {
                principal: 100000,
                rate: 5,
                term: 360,
                monthlyPayment: 0,

                calculate() {
                    const r = (this.rate / 100) / 12;
                    const n = this.term;
                    const p = this.principal;

                    if (r === 0) {
                        this.monthlyPayment = p / n;
                    } else {
                        this.monthlyPayment = p * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
                    }
                },

                init() {
                    this.calculate();
                }
            }
        }
    </script>
</body>
</html>
```

---

## 9. 구현 우선순위

### Phase 1: 기본 파이프라인 (MVP)
1. [x] 아키텍처 설계
2. [ ] 프로젝트 세팅 (uv init, 의존성)
3. [ ] Excel 파싱 도구 구현 (openpyxl)
4. [ ] Analyzer Agent 구현
5. [ ] 단순 테이블 생성기 구현
6. [ ] POC UI (파일 업로드 → 프리뷰)

### Phase 2: 수식 및 차트
7. [ ] 수식 파싱 및 JS 변환 (formulas)
8. [ ] Chart.js 설정 생성기
9. [ ] Calculator Generator 구현
10. [ ] Dashboard Generator 구현

### Phase 3: VBA 및 고급 기능
11. [ ] VBA 추출 및 분석 (oletools)
12. [ ] VBA → JS 변환 (LLM 기반)
13. [ ] Maker-Checker 루프 구현
14. [ ] 복잡한 레이아웃 지원

---

## 10. 환경 설정

### 10.1 환경 변수

```bash
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1
LOG_LEVEL=INFO
```

### 10.2 의존성 설치

```bash
cd xls_agent
uv init
uv add openai-agents openpyxl pandas formulas oletools fastapi uvicorn python-multipart
```

---

## References

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [Azure AI Agent Design Patterns](https://learn.microsoft.com/ko-kr/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [DesignBench: MLLM Front-end Code Generation Benchmark](https://arxiv.org/html/2506.06251v1)
- [formulas Documentation](https://formulas.readthedocs.io/)
- [oletools olevba](https://github.com/decalage2/oletools/wiki/olevba)
