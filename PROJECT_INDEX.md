# Project Index: xls-agent

**Generated**: 2025-12-28
**Purpose**: Excel 파일을 웹 애플리케이션으로 자동 변환하는 AI 에이전트 시스템

---

## 📁 Project Structure

```
xls_agent/
├── main.py                    # CLI 엔트리포인트
├── src/
│   ├── orchestrator.py        # 파이프라인 오케스트레이터
│   ├── agents/                # OpenAI Agents SDK 에이전트
│   │   ├── analyzer_agent.py  # Excel 분석 에이전트 (gpt-5-mini)
│   │   ├── planner_agent.py   # 웹앱 설계 에이전트 (gpt-5.2)
│   │   └── generator_agent.py # 코드 생성 에이전트 (gpt-5.2)
│   ├── tools/                 # 에이전트 도구
│   │   ├── excel_analyzer.py  # Excel 파싱 도구
│   │   ├── formula_converter.py # 수식→JS 변환
│   │   └── vba_converter.py   # VBA→JS 변환
│   ├── models/                # Pydantic 모델
│   │   ├── analysis.py        # ExcelAnalysis 모델
│   │   ├── plan.py            # WebAppPlan 모델
│   │   └── output.py          # GeneratedWebApp, TestResult 모델
│   ├── tracing/               # 트레이싱
│   │   └── json_processor.py  # JSON trace 처리
│   └── api/                   # FastAPI 라우트
│       └── routes.py
├── demos/                     # 생성된 웹앱 데모 (10개)
├── traces/                    # Agent trace JSON 파일
├── excel_files/               # 테스트용 Excel 파일
├── index.html                 # 데모 갤러리 메인 페이지
├── trace-viewer.html          # 빌드 과정 모니터링 UI
└── docs/                      # 문서
    ├── PRD.md
    └── ARCHITECTURE.md
```

---

## 🚀 Entry Points

| Entry | Path | Description |
|-------|------|-------------|
| CLI | `main.py` | `python main.py serve` / `convert` |
| API | `src/api/routes.py` | FastAPI 서버 (POST /convert) |
| Demo | `index.html` | 배포된 데모 갤러리 |

---

## 🤖 Agent Pipeline

```
Excel File (.xlsx/.xlsm)
       ↓
┌─────────────────┐
│ Analyzer Agent  │ ← gpt-5-mini (비용 최적화)
│ analyze_excel() │   Excel 구조 분석
└────────┬────────┘
         ↓ ExcelAnalysis
┌─────────────────┐
│ Planner Agent   │ ← gpt-5.2 (SOTA)
│ design web app  │   UI/UX 설계
└────────┬────────┘
         ↓ WebAppPlan
┌─────────────────┐
│ Generator Agent │ ← gpt-5.2 (SOTA)
│ generate code   │   HTML/CSS/JS 생성
└────────┬────────┘
         ↓ GeneratedWebApp
     HTML Output
```

---

## 📦 Core Modules

### `src/orchestrator.py`
- **Class**: `ExcelToWebAppOrchestrator`
- **Methods**: `convert()`, `_analyze()`, `_plan()`, `_generate_with_iterations()`
- **Purpose**: 3개 에이전트를 순차 실행하고 테스트 기반 반복

### `src/agents/analyzer_agent.py`
- **Function**: `create_analyzer_agent()` → `Agent`
- **Tools**: `analyze_excel`, `get_sheet_cells`
- **Model**: `gpt-5-mini`

### `src/agents/planner_agent.py`
- **Function**: `create_planner_agent()` → `Agent`
- **Output**: `WebAppPlan` (structured output)
- **Model**: `gpt-5.2`

### `src/agents/generator_agent.py`
- **Function**: `create_generator_agent()` → `Agent`
- **Tools**: `convert_formula`, `check_formula_complexity`, `get_js_helpers`
- **Output**: `GeneratedWebApp`
- **Model**: `gpt-5.2`

### `src/tools/excel_analyzer.py`
- **Function**: `analyze_excel_file(path)` → `ExcelAnalysis`
- **Extracts**: sheets, formulas, VBA macros, print settings

### `src/tools/formula_converter.py`
- **Function**: `convert_formula(formula)` → JS code
- **Handles**: 셀 참조, 함수, 연산자 변환

---

## 🔧 Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python 의존성 (uv) |
| `.github/workflows/deploy.yml` | GitHub Pages 배포 |
| `CLAUDE.md` | AI 개발 가이드 |

---

## 📚 Documentation

| Document | Topic |
|----------|-------|
| `docs/PRD.md` | 제품 요구사항 정의서 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 |
| `README.md` | 프로젝트 소개 |
| `CLAUDE.md` | Claude Code 개발 지침 |

---

## 🧪 Testing

- **Test-driven iteration**: 최대 3회 반복으로 테스트 통과율 90% 목표
- **Test types**: HTML 구조, 필수 요소, 인쇄 스타일, JS 검증, 한국어 라벨

---

## 🔗 Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `openai-agents` | ≥0.6.4 | OpenAI Agents SDK |
| `openpyxl` | ≥3.1.5 | Excel 파일 파싱 |
| `formulas` | ≥1.3.3 | Excel 수식 파싱 |
| `oletools` | ≥0.60.2 | VBA 매크로 추출 |
| `fastapi` | ≥0.127.1 | REST API |
| `pydantic` | ≥2.12.5 | 데이터 모델링 |

---

## 🌐 Deployment

- **GitHub Pages**: https://excel.seolcoding.com
- **Repository**: seolcoding/excel
- **Branch**: main
- **Workflow**: `.github/workflows/deploy.yml`

---

## 📝 Quick Start

```bash
# 1. 의존성 설치
uv sync

# 2. API 서버 실행
uv run python main.py serve

# 3. Excel 파일 변환
uv run python main.py convert input.xlsx -o output.html

# 4. 로컬 테스트 서버
python -m http.server 8080
```

---

## 🎯 Key Features

1. **Excel → WebApp 자동 변환**: 수식, VBA, 인쇄 설정 보존
2. **OpenAI Agents SDK**: 3단계 에이전트 파이프라인
3. **한국어 UI**: 모든 인터페이스 한국어 지원
4. **Agent Trace**: 빌드 과정 모니터링 및 시각화
5. **반복 개선**: 테스트 기반 자동 코드 개선

---

## 📊 Token Efficiency

| Action | Tokens |
|--------|--------|
| 이 인덱스 읽기 | ~2,500 |
| 전체 코드 읽기 | ~50,000+ |
| **절감률** | **95%** |
