# TDD-Driven Excel-to-WebApp Pipeline Architecture

> Spec-Driven Development with Test-First Code Generation

## Implementation Status ✅

**Status: IMPLEMENTED** (2025-12-29)

### Changes Made

| Component | Change | Status |
|-----------|--------|--------|
| `src/models/output.py` | Added `WebAppSpec` and `VerificationReport` models | ✅ Done |
| `src/agents/spec_agent.py` | New TDD Spec Agent (replaces Planner in TDD flow) | ✅ Done |
| `src/agents/generator_agent.py` | Changed model from `gpt-5.2` to `gpt-5.1-codex` | ✅ Done |
| `src/orchestrator.py` | Implemented TDD flow: Analyze → Spec → Test-First → Generate → Verify | ✅ Done |
| `src/orchestrator.py` | Changed `min_pass_rate` from 0.8 to 0.9 | ✅ Done |
| `src/orchestrator.py` | Added `VerificationReport` to `ConversionResult` | ✅ Done |

### TDD Pipeline Flow

```
Excel File
    │
    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Analyzer   │────▶│  Spec Agent │────▶│ Test-First  │
│ (gpt-5-mini)│     │  (gpt-5.2)  │     │(Test Gen)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────────────────┘
                    ▼
              ┌─────────────┐
              │  Generator  │◄─────────────┐
              │(gpt-5.1-codex)             │
              └─────────────┘              │
                    │                      │
                    ▼                 Feedback
              ┌─────────────┐              │
              │   Verify    │──────────────┘
              │ (90% pass)  │
              └─────────────┘
                    │
                    ▼
            VerificationReport
```

---

## 1. Executive Summary

### 1.1 Current State vs. Proposed State

| Aspect | Current Pipeline | Proposed TDD Pipeline |
|--------|------------------|----------------------|
| **Design** | Excel → Analyze → Plan → Generate → Test | Excel → Analyze → **Spec** → **Test-First** → Generate → Verify |
| **Test Origin** | Excel 값에서 직접 추출 | **스펙 문서 기반** 생성 |
| **Contract** | Planner ↔ Generator 암묵적 | **PRD 스타일 명시적 계약** |
| **Code Gen** | Generate → Test (후 검증) | **Test-First → Generate (TDD)** |
| **Feedback** | LLM-as-a-Judge + Static | **Spec Compliance + TDD Assertions** |

### 1.2 Key Benefits

1. **명확한 요구사항 추적**: FR-001, NFR-001 등 체계적 관리
2. **TDD 기반 코드 생성**: 테스트가 먼저, 코드는 테스트를 통과하도록 생성
3. **Codex 최적화**: `gpt-5.2-codex` 모델의 코드 생성 능력 극대화
4. **검증 가능성**: 각 요구사항에 대한 명확한 Pass/Fail 추적

---

## 2. Current Pipeline Architecture

### 2.1 Overall Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CURRENT EXCEL TO WEBAPP PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────────┘

  Entry Points:
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  ├── main.py              → CLI 단일 파일 변환                              │
  │  └── convert_top10.py     → 배치 변환 (Top 10 데모)                         │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  src/orchestrator.py                                                         │
  │  ════════════════════                                                        │
  │  ExcelToWebAppOrchestrator - 전체 파이프라인 조율                             │
  │  convert_excel_to_webapp() - 메인 변환 함수                                  │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
            ▼                           ▼                           ▼
  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │ PHASE 1: ANALYZE │    │ PHASE 2: TEST    │    │ PHASE 3: PLAN    │
  │ [10%]            │    │ [15-18%]         │    │ [30%]            │
  ├──────────────────┤    ├──────────────────┤    ├──────────────────┤
  │                  │    │                  │    │                  │
  │ analyzer_agent.py│───▶│test_generator_   │───▶│ planner_agent.py │
  │                  │    │      agent.py    │    │                  │
  │ Model: gpt-5-mini│    │ Model: gpt-5-mini│    │ Model: gpt-5.2   │
  │                  │    │                  │    │                  │
  │ Tools:           │    │ Tools:           │    │ Output:          │
  │ • analyze_excel  │    │ • extract_tests  │    │ • WebAppPlan     │
  │ • get_sheet_cells│    │ • generate_cases │    │ • Components     │
  │ • analyze_layout │    │                  │    │ • Functions      │
  │ • analyze_io     │    │ Output:          │    │ • Print Layout   │
  │ • build_deps     │    │ • TestSuite      │    │                  │
  │ • analyze_vba    │    │ • StaticTestSuite│    │                  │
  │                  │    │                  │    │                  │
  │ Output:          │    │                  │    │                  │
  │ • ExcelAnalysis  │    │                  │    │                  │
  └──────────────────┘    └──────────────────┘    └──────────────────┘
          │                       │                       │
          │   src/tools/          │   src/tools/          │
          │   excel_analyzer.py   │   test_generator.py   │
          │                       │                       │
          └───────────────────────┴───────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  PHASE 4: GENERATE → TEST → IMPROVE LOOP [50% - 95%]                         │
  │                                                                              │
  │  ┌─────────────────────────────────────────────────────────────────────┐    │
  │  │                         ITERATION LOOP (max 3회)                     │    │
  │  │                                                                      │    │
  │  │   ┌──────────────────┐                                              │    │
  │  │   │ generator_agent  │ ◄──────────────────────────────────┐         │    │
  │  │   │ .py              │                                    │         │    │
  │  │   │                  │                                    │         │    │
  │  │   │ Model: gpt-5.2   │                             Feedback│         │    │
  │  │   │                  │                                    │         │    │
  │  │   │ Tools:           │                                    │         │    │
  │  │   │ • convert_formula│                                    │         │    │
  │  │   │ • check_complex  │                                    │         │    │
  │  │   │ • get_js_helpers │                                    │         │    │
  │  │   │                  │                                    │         │    │
  │  │   │ Output:          │                                    │         │    │
  │  │   │ • GeneratedWebApp│                                    │         │    │
  │  │   │   (HTML/CSS/JS)  │                                    │         │    │
  │  │   └────────┬─────────┘                                    │         │    │
  │  │            │                                              │         │    │
  │  │            ▼                                              │         │    │
  │  │   ┌──────────────────┐    ┌──────────────────┐           │         │    │
  │  │   │ STATIC TESTS     │    │ tester_agent.py  │           │         │    │
  │  │   │                  │    │ (LLM-as-a-Judge) │           │         │    │
  │  │   │ static_test_     │    │                  │           │         │    │
  │  │   │ runner.py        │    │ Model: gpt-5-mini│           │         │    │
  │  │   │                  │    │                  │           │         │    │
  │  │   │ • Node.js 실행    │    │ Tools:           │           │         │    │
  │  │   │ • 수식 검증       │    │ • validate_html  │           │         │    │
  │  │   │ • Expected vs    │    │ • validate_js    │           │         │    │
  │  │   │   Actual 비교    │    │ • validate_print │           │         │    │
  │  │   │                  │    │ • validate_korean│           │         │    │
  │  │   │ Output:          │    │ • check_formulas │           │         │    │
  │  │   │ • StaticTest     │    │                  │           │         │    │
  │  │   │   Result         │    │ Output:          │           │         │    │
  │  │   │ • Pass Rate %    │    │ • TestEvaluation │           │         │    │
  │  │   └────────┬─────────┘    │ • Pass/Fail/     │           │         │    │
  │  │            │              │   Needs Improve  │           │         │    │
  │  │            │              │ • Feedback       │           │         │    │
  │  │            │              │ • Suggested Fixes│           │         │    │
  │  │            │              └────────┬─────────┘           │         │    │
  │  │            │                       │                      │         │    │
  │  │            └───────────┬───────────┘                      │         │    │
  │  │                        │                                  │         │    │
  │  │                        ▼                                  │         │    │
  │  │               ┌─────────────────┐                        │         │    │
  │  │               │ Combined Score  │                        │         │    │
  │  │               │                 │                        │         │    │
  │  │               │ static: 40%     │                        │         │    │
  │  │               │ + LLM:  60%     │                        │         │    │
  │  │               │ ═══════════════ │                        │         │    │
  │  │               │ = pass_rate     │                        │         │    │
  │  │               └────────┬────────┘                        │         │    │
  │  │                        │                                  │         │    │
  │  │                        ▼                                  │         │    │
  │  │               ┌─────────────────┐     YES                │         │    │
  │  │               │ pass_rate ≥ 80% │─────────────────────────┼────┐    │    │
  │  │               │ OR iteration=3? │                        │    │    │    │
  │  │               └────────┬────────┘                        │    │    │    │
  │  │                        │ NO                               │    │    │    │
  │  │                        └──────────────────────────────────┘    │    │    │
  │  │                                                                │    │    │
  │  └────────────────────────────────────────────────────────────────┼────┘    │
  │                                                                   │         │
  └───────────────────────────────────────────────────────────────────┼─────────┘
                                                                      │
                                                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  OUTPUT [100%]                                                               │
  │  ═══════════════                                                             │
  │                                                                              │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
  │  │ demos/*.html    │  │ traces/*.json   │  │ conversion_     │              │
  │  │                 │  │                 │  │ results.json    │              │
  │  │ 생성된 웹앱      │  │ Agent 실행 로그  │  │ 변환 결과 요약   │              │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
  │                                                                              │
  │  ConversionResult:                                                           │
  │  • success: bool                                                             │
  │  • app: GeneratedWebApp (HTML/CSS/JS)                                        │
  │  • iterations_used: int                                                      │
  │  • final_pass_rate: float                                                    │
  │  • test_results: list[TestResult]                                            │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 File Mapping (Current)

```
src/
├── orchestrator.py          ← 파이프라인 조율 (메인 로직)
├── agents/
│   ├── __init__.py
│   ├── analyzer_agent.py    ← Phase 1: Excel 분석
│   ├── test_generator_agent.py ← Phase 2: 테스트 케이스 생성
│   ├── planner_agent.py     ← Phase 3: 웹앱 설계
│   ├── generator_agent.py   ← Phase 4: 코드 생성
│   └── tester_agent.py      ← Phase 4: LLM-as-a-Judge 평가
├── tools/
│   ├── __init__.py
│   ├── excel_analyzer.py    ← Excel 파싱 (openpyxl)
│   ├── formula_converter.py ← Excel 수식 → JS 변환
│   ├── vba_converter.py     ← VBA → JS 변환
│   ├── test_generator.py    ← 테스트 케이스 추출
│   ├── static_test_runner.py← Node.js 기반 정적 테스트
│   └── e2e_test_runner.py   ← Playwright E2E 테스트 (미사용)
├── models/
│   ├── __init__.py
│   ├── analysis.py          ← ExcelAnalysis 모델
│   ├── plan.py              ← WebAppPlan, GeneratedWebApp
│   ├── test_case.py         ← TestSuite, TestResult
│   └── output.py            ← ConversionResult
└── tracing/
    ├── __init__.py
    ├── conversation_hooks.py← LLM 대화 캡처
    ├── streaming_monitor.py ← 실시간 모니터링
    └── json_processor.py    ← Trace JSON 생성
```

### 2.3 Current Flow Summary

```
1. Analyze (gpt-5-mini) → Excel 구조 추출
2. Test Gen (gpt-5-mini) → 테스트 케이스 생성 (Excel 값에서 직접)
3. Plan (gpt-5.2) → 웹앱 설계
4. Generate (gpt-5.2) → HTML/CSS/JS 생성
5. Static Test (Node.js) → 수식 검증
6. Tester (gpt-5-mini) → LLM-as-a-Judge 평가
7. Loop → 80% 미만이면 피드백 → 4번으로 (최대 3회)
```

---

## 3. Proposed TDD Pipeline Architecture

### 3.1 Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               TDD-DRIVEN EXCEL-TO-WEBAPP PIPELINE (PROPOSED)                 │
│                                                                              │
│  Excel → Analyze → SPEC → TEST-FIRST → Generate → Verify → Loop             │
│                     ↑        ↑                                               │
│                    NEW!     NEW!                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Detailed Phase Diagram

```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 1: ANALYZE                                                             │
  │ Model: gpt-5-mini                                                            │
  │ File: src/agents/analyzer_agent.py                                           │
  │ Output: ExcelAnalysis                                                        │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 2: SPEC GENERATION (NEW!)                                              │
  │ Model: gpt-5.2                                                               │
  │ File: src/agents/spec_agent.py                                               │
  │                                                                              │
  │ Prompt:                                                                      │
  │ ┌─────────────────────────────────────────────────────────────────────────┐ │
  │ │ Excel 분석 결과를 바탕으로 PRD 스타일의 기능 명세서를 작성하세요.          │ │
  │ │                                                                         │ │
  │ │ 포함할 내용:                                                             │ │
  │ │ 1. 기능 요구사항 (FR-XXX): 각 수식/계산에 대한 명확한 정의               │ │
  │ │    - 입력 정의 (타입, 범위, 제약조건)                                    │ │
  │ │    - 출력 정의 (계산식, 포맷)                                            │ │
  │ │    - 비즈니스 로직 설명                                                  │ │
  │ │    - 예시 (input → expected output)                                     │ │
  │ │ 2. 비기능 요구사항 (NFR-XXX): UI/UX, 인쇄, 성능                          │ │
  │ │ 3. 엣지 케이스 및 에러 처리                                              │ │
  │ └─────────────────────────────────────────────────────────────────────────┘ │
  │                                                                              │
  │ Output: WebAppSpec (PRD-style document)                                      │
  │                                                                              │
  │ Example Output:                                                              │
  │ ┌─────────────────────────────────────────────────────────────────────────┐ │
  │ │ # 웹앱 기능 명세서 (PRD)                                                 │ │
  │ │                                                                         │ │
  │ │ ## 1. 개요                                                              │ │
  │ │ - 앱 이름: 4대보험 자동계산기                                            │ │
  │ │ - 목적: 급여 기반 4대보험료 자동 계산                                     │ │
  │ │                                                                         │ │
  │ │ ## 2. 기능 요구사항                                                      │ │
  │ │ ### FR-001: 국민연금 계산                                                │ │
  │ │ - 입력: 월급여 (number, 원)                                              │ │
  │ │ - 출력: 국민연금료 = 월급여 × 4.5%                                       │ │
  │ │ - 제약: 최소 330,000원, 최대 5,530,000원 기준소득월액                     │ │
  │ │ - 예시: 3,000,000원 → 135,000원                                         │ │
  │ │                                                                         │ │
  │ │ ### FR-002: 건강보험 계산                                                │ │
  │ │ - 입력: 월급여                                                           │ │
  │ │ - 출력: 건강보험료 = 월급여 × 3.545%                                     │ │
  │ │ - 예시: 3,000,000원 → 106,350원                                         │ │
  │ │                                                                         │ │
  │ │ ## 3. 비기능 요구사항                                                    │ │
  │ │ - NFR-001: 숫자 포맷 (1,000 단위 콤마)                                   │ │
  │ │ - NFR-002: 인쇄 시 A4 세로                                              │ │
  │ │                                                                         │ │
  │ │ ## 4. 테스트 시나리오                                                    │ │
  │ │ - TC-001: 기본 계산 (3,000,000원 입력)                                   │ │
  │ │ - TC-002: 최소값 경계 (330,000원 이하)                                   │ │
  │ │ - TC-003: 최대값 경계 (5,530,000원 이상)                                 │ │
  │ └─────────────────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 3: TEST-FIRST GENERATION (TDD RED PHASE) (NEW!)                        │
  │ Model: gpt-5.2-codex (or gpt-5.1-codex fallback)                             │
  │ File: src/agents/test_spec_agent.py                                          │
  │                                                                              │
  │ Prompt:                                                                      │
  │ ┌─────────────────────────────────────────────────────────────────────────┐ │
  │ │ 다음 스펙에 대한 테스트 코드를 먼저 작성하세요.                            │ │
  │ │                                                                         │ │
  │ │ 각 FR에 대해:                                                            │ │
  │ │ 1. 단위 테스트 함수 (JavaScript)                                         │ │
  │ │ 2. 입력값 → 기대 출력값 assertion                                        │ │
  │ │ 3. 경계값 테스트                                                         │ │
  │ │ 4. 에러 케이스 테스트                                                    │ │
  │ │                                                                         │ │
  │ │ 테스트는 Node.js에서 실행 가능해야 합니다.                                │ │
  │ │ 테스트 함수명: test_FR001_기본계산(), test_FR001_경계값() 등              │ │
  │ └─────────────────────────────────────────────────────────────────────────┘ │
  │                                                                              │
  │ Output: TestSpecification (executable test code)                             │
  │                                                                              │
  │ Example Output:                                                              │
  │ ┌─────────────────────────────────────────────────────────────────────────┐ │
  │ │ // test_spec.js                                                         │ │
  │ │ const tests = [                                                         │ │
  │ │   {                                                                     │ │
  │ │     id: "FR-001-01",                                                    │ │
  │ │     name: "국민연금 기본 계산",                                          │ │
  │ │     fn: "calculatePension",                                             │ │
  │ │     inputs: { salary: 3000000 },                                        │ │
  │ │     expected: { pension: 135000 },                                      │ │
  │ │     assertion: (result) => result.pension === 135000                    │ │
  │ │   },                                                                    │ │
  │ │   {                                                                     │ │
  │ │     id: "FR-001-02",                                                    │ │
  │ │     name: "국민연금 최소 기준소득",                                       │ │
  │ │     fn: "calculatePension",                                             │ │
  │ │     inputs: { salary: 300000 },                                         │ │
  │ │     expected: { pension: 14850 },  // 330000 * 0.045                    │ │
  │ │     assertion: (result) => result.pension === 14850                     │ │
  │ │   },                                                                    │ │
  │ │   // ... more tests                                                     │ │
  │ │ ];                                                                      │ │
  │ │                                                                         │ │
  │ │ module.exports = { tests };                                             │ │
  │ └─────────────────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 4: CODE GENERATION (TDD GREEN PHASE)                                   │
  │ Model: gpt-5.2-codex                                                         │
  │ File: src/agents/generator_agent.py (modified)                               │
  │                                                                              │
  │ Prompt:                                                                      │
  │ ┌─────────────────────────────────────────────────────────────────────────┐ │
  │ │ ## TDD 코드 생성                                                         │ │
  │ │                                                                         │ │
  │ │ 아래 테스트를 모두 통과하는 웹 애플리케이션 코드를 작성하세요.              │ │
  │ │                                                                         │ │
  │ │ ### 테스트 명세:                                                         │ │
  │ │ {test_spec_json}                                                        │ │
  │ │                                                                         │ │
  │ │ ### 요구사항:                                                            │ │
  │ │ 1. 각 테스트의 assertion이 통과해야 함                                   │ │
  │ │ 2. 함수명은 테스트에서 지정한 대로 사용                                   │ │
  │ │ 3. 입력/출력 타입 준수                                                   │ │
  │ │                                                                         │ │
  │ │ ### 기술 스택:                                                           │ │
  │ │ - HTML5 + Bootstrap 5                                                   │ │
  │ │ - Alpine.js (reactivity)                                                │ │
  │ │ - 순수 JavaScript (함수들)                                               │ │
  │ │                                                                         │ │
  │ │ 테스트를 먼저 확인하고, 테스트를 통과하는 최소한의 코드를 작성하세요.       │ │
  │ └─────────────────────────────────────────────────────────────────────────┘ │
  │                                                                              │
  │ Output: GeneratedWebApp (HTML with embedded JS functions)                    │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ PHASE 5: TEST EXECUTION (TDD VERIFY)                                         │
  │                                                                              │
  │ 1. Extract JS functions from generated HTML                                  │
  │ 2. Run tests against functions (Node.js)                                     │
  │ 3. Generate coverage report                                                  │
  │                                                                              │
  │ ┌─────────────────────────────────────────────────────────────────────────┐ │
  │ │ Test Results:                                                           │ │
  │ │ ✅ FR-001-01: 국민연금 기본 계산 - PASS                                  │ │
  │ │ ✅ FR-001-02: 국민연금 최소 기준소득 - PASS                               │ │
  │ │ ❌ FR-002-01: 건강보험 기본 계산 - FAIL                                  │ │
  │ │    Expected: 106350, Got: 106000                                        │ │
  │ │ ✅ FR-002-02: 건강보험 경계값 - PASS                                     │ │
  │ │                                                                         │ │
  │ │ Coverage: 15/16 tests passed (93.75%)                                   │ │
  │ └─────────────────────────────────────────────────────────────────────────┘ │
  │                                                                              │
  │ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
  │ │ Static Tests    │    │ Spec Compliance │    │ LLM-as-a-Judge │          │
  │ │ (Node.js)       │    │ (요구사항 추적)  │    │ (품질 평가)     │          │
  │ └────────┬────────┘    └────────┬────────┘    └────────┬────────┘          │
  │          │                      │                      │                    │
  │          └──────────────────────┴──────────────────────┘                    │
  │                                 │                                            │
  │                                 ▼                                            │
  │                    ┌─────────────────────────┐                              │
  │                    │ Verification Report     │                              │
  │                    │ - FR-001: ✅ PASS       │                              │
  │                    │ - FR-002: ❌ FAIL       │                              │
  │                    │ - NFR-001: ✅ PASS      │                              │
  │                    │ Coverage: 85%          │                              │
  │                    └─────────────────────────┘                              │
  └─────────────────────────────────────────────────────────────────────────────┘
                                        │
                             ┌──────────┴──────────┐
                             │                     │
                       PASS (≥90%)           FAIL (<90%)
                             │                     │
                             ▼                     ▼
                      ┌─────────────┐    ┌─────────────────────────┐
                      │ COMPLETE    │    │ PHASE 6: REFACTOR (TDD) │
                      │             │    │                         │
                      │ Output HTML │    │ Feedback to Generator:  │
                      └─────────────┘    │ "다음 테스트가 실패함:    │
                                         │  - FR-002-01: ...       │
                                         │  수정하세요"             │
                                         └────────────┬────────────┘
                                                      │
                                                      └──────▶ PHASE 4 (반복)
```

---

## 4. Model Selection

### 4.1 OpenAI Models Reference

| Model ID | Type | Use Case | API Status |
|----------|------|----------|------------|
| `gpt-5-mini` | Reasoning | 분석, 테스트 생성, 평가 | ✅ Available |
| `gpt-5.2` | Reasoning | 설계, 스펙 작성, 복잡한 추론 | ✅ Available |
| `gpt-5-codex` | Code Gen | 코드 생성 최적화 | ✅ Responses API |
| `gpt-5.1-codex` | Code Gen | 코드 생성 최적화 | ✅ Responses API |
| `gpt-5.2-codex` | Code Gen | 장기 에이전트 코딩 (최신) | ⏳ "coming weeks" |

### 4.2 Agent Model Assignment (Proposed)

```python
# Agent → Model Mapping
AGENT_MODELS = {
    "analyzer_agent": "gpt-5-mini",       # 비용 최적화, 단순 구조 추출
    "spec_agent": "gpt-5.2",              # PRD 스타일 문서 작성 (추론 필요)
    "test_spec_agent": "gpt-5.2-codex",   # TDD 테스트 코드 생성
    "generator_agent": "gpt-5.2-codex",   # 웹앱 코드 생성
    "tester_agent": "gpt-5-mini",         # LLM-as-a-Judge 평가
}

# Fallback when gpt-5.2-codex unavailable
FALLBACK_MODELS = {
    "gpt-5.2-codex": "gpt-5.1-codex",     # gpt-5.2-codex → gpt-5.1-codex
    "gpt-5.1-codex": "gpt-5.2",           # gpt-5.1-codex → gpt-5.2
}
```

---

## 5. Data Models (Proposed)

### 5.1 WebAppSpec (NEW)

```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class RequirementType(str, Enum):
    FUNCTIONAL = "FR"
    NON_FUNCTIONAL = "NFR"

class Requirement(BaseModel):
    """Single requirement definition."""
    id: str                           # e.g., "FR-001", "NFR-002"
    type: RequirementType
    title: str                        # e.g., "국민연금 계산"
    description: str                  # Detailed description
    inputs: list[dict]                # [{name, type, constraints}]
    outputs: list[dict]               # [{name, type, formula}]
    examples: list[dict]              # [{inputs, expected_outputs}]
    edge_cases: list[str]             # Edge case descriptions
    priority: int = 1                 # 1=Critical, 2=High, 3=Medium

class TestScenario(BaseModel):
    """Test scenario linked to requirements."""
    id: str                           # e.g., "TC-001"
    requirement_ids: list[str]        # ["FR-001", "FR-002"]
    description: str
    test_type: str                    # "unit", "integration", "boundary"

class WebAppSpec(BaseModel):
    """PRD-style specification document."""
    app_name: str
    purpose: str
    requirements: list[Requirement]
    test_scenarios: list[TestScenario]
    tech_stack: dict                  # {html, css, js, libs}
    ui_guidelines: dict               # {language, print_layout, styling}
```

### 5.2 TestSpecification (NEW)

```python
class TestCase(BaseModel):
    """Executable test case."""
    id: str                           # e.g., "FR-001-01"
    requirement_id: str               # e.g., "FR-001"
    name: str                         # e.g., "국민연금 기본 계산"
    function_name: str                # e.g., "calculatePension"
    inputs: dict                      # {salary: 3000000}
    expected: dict                    # {pension: 135000}
    assertion_code: str               # JS assertion code
    test_type: str                    # "basic", "boundary", "error"

class TestSpecification(BaseModel):
    """Collection of executable tests."""
    spec_id: str                      # Reference to WebAppSpec
    test_cases: list[TestCase]
    setup_code: Optional[str]         # Common setup code
    teardown_code: Optional[str]      # Common cleanup code
```

### 5.3 VerificationReport (NEW)

```python
class RequirementStatus(BaseModel):
    """Status of a single requirement."""
    requirement_id: str
    status: str                       # "PASS", "FAIL", "PARTIAL"
    test_results: list[dict]          # [{test_id, passed, message}]
    coverage: float                   # 0.0 to 1.0

class VerificationReport(BaseModel):
    """Complete verification report with traceability."""
    spec_id: str
    timestamp: str
    overall_pass_rate: float
    requirements: list[RequirementStatus]
    failing_tests: list[str]
    suggested_fixes: list[str]

    def get_traceability_matrix(self) -> dict:
        """Generate requirement → test → result matrix."""
        matrix = {}
        for req in self.requirements:
            matrix[req.requirement_id] = {
                "status": req.status,
                "tests": req.test_results,
                "coverage": req.coverage,
            }
        return matrix
```

---

## 6. Implementation Plan

### 6.1 New Files to Create

```
src/
├── agents/
│   ├── spec_agent.py           # NEW: PRD 스펙 생성
│   └── test_spec_agent.py      # NEW: TDD 테스트 생성 (기존 test_generator_agent.py 대체)
├── models/
│   ├── spec.py                 # NEW: WebAppSpec, Requirement
│   ├── test_spec.py            # NEW: TestSpecification, TestCase
│   └── verification.py         # NEW: VerificationReport
└── tools/
    └── spec_test_runner.py     # NEW: Spec-based test runner
```

### 6.2 Files to Modify

```
src/
├── orchestrator.py             # TDD 파이프라인 통합
├── agents/
│   └── generator_agent.py      # 모델 → gpt-5.2-codex, TDD 프롬프트
└── tools/
    └── static_test_runner.py   # Spec-based test 지원
```

### 6.3 Implementation Phases

#### Phase 1: Spec Agent (spec_agent.py)
```python
from agents import Agent, Runner
from src.models.spec import WebAppSpec

spec_agent = Agent(
    name="SpecAgent",
    model="gpt-5.2",
    instructions="""
    Excel 분석 결과를 PRD 스타일의 기능 명세서로 변환합니다.

    각 수식, 입력, 출력에 대해 명확한 요구사항을 정의합니다:
    - FR-XXX: 기능 요구사항 (계산 로직)
    - NFR-XXX: 비기능 요구사항 (UI, 인쇄, 포맷)

    각 요구사항에는 예시와 엣지 케이스를 포함합니다.
    """,
    output_type=WebAppSpec,
)
```

#### Phase 2: Test Spec Agent (test_spec_agent.py)
```python
from agents import Agent, Runner
from src.models.test_spec import TestSpecification

test_spec_agent = Agent(
    name="TestSpecAgent",
    model="gpt-5.2-codex",  # or fallback to gpt-5.1-codex
    instructions="""
    스펙 문서에 대한 TDD 테스트를 생성합니다.

    각 요구사항(FR)에 대해:
    1. 기본 테스트 케이스 (정상 동작)
    2. 경계값 테스트 (min, max, edge)
    3. 에러 케이스 테스트 (invalid input)

    테스트는 Node.js에서 실행 가능한 JavaScript로 작성합니다.
    함수명은 test_{FR_ID}_{테스트유형}() 형식을 사용합니다.
    """,
    output_type=TestSpecification,
)
```

#### Phase 3: Generator Agent Update
```python
# generator_agent.py 수정
generator_agent = Agent(
    name="GeneratorAgent",
    model="gpt-5.2-codex",  # 모델 변경
    instructions="""
    ## TDD 코드 생성기

    테스트 명세를 받아 모든 테스트를 통과하는 웹앱 코드를 생성합니다.

    원칙:
    1. 테스트 명세의 함수명을 정확히 사용
    2. 테스트의 input → expected output을 만족하는 최소한의 코드
    3. 추가 기능은 테스트가 요구할 때만 구현

    기술 스택: HTML5 + Bootstrap 5 + Alpine.js + 순수 JS
    """,
    output_type=GeneratedWebApp,
)
```

---

## 7. Orchestrator Update

### 7.1 TDD Pipeline Flow

```python
# orchestrator.py 수정안

async def convert_with_tdd(self, excel_path: str) -> ConversionResult:
    """TDD-driven conversion pipeline."""

    # Phase 1: Analyze (existing)
    analysis = await self._analyze(excel_path, hooks)

    # Phase 2: Generate Spec (NEW)
    spec = await self._generate_spec(analysis, hooks)

    # Phase 3: Generate Tests First (TDD RED)
    test_spec = await self._generate_test_spec(spec, hooks)

    # Phase 4: Generate Code (TDD GREEN)
    for iteration in range(1, self.max_iterations + 1):
        webapp = await self._generate_from_spec(
            spec, test_spec, hooks,
            previous_feedback=feedback,
        )

        # Phase 5: Verify (TDD VERIFY)
        report = await self._verify_against_spec(webapp, test_spec)

        if report.overall_pass_rate >= 0.9:
            break

        # Prepare feedback for next iteration
        feedback = self._build_feedback(report)

    return ConversionResult(
        success=report.overall_pass_rate >= 0.8,
        app=webapp,
        verification_report=report,
    )
```

---

## 8. References

### 8.1 Official Documentation
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [OpenAI Codex Models](https://platform.openai.com/docs/models)
- Local Reference: `refs/openai-agents-python/`

### 8.2 Related Documents
- `docs/ARCHITECTURE.md` - Current architecture
- `docs/PRD.md` - Product requirements
- `docs/openai_agents_sdk_reference.md` - SDK reference

### 8.3 Model Availability Sources
- https://openai.com/index/introducing-gpt-5-2-codex/
- https://developers.openai.com/codex/models/

---

## Appendix A: Migration Checklist

- [ ] Create `src/models/spec.py` with WebAppSpec model
- [ ] Create `src/models/test_spec.py` with TestSpecification model
- [ ] Create `src/models/verification.py` with VerificationReport model
- [ ] Create `src/agents/spec_agent.py`
- [ ] Create `src/agents/test_spec_agent.py`
- [ ] Update `src/agents/generator_agent.py` for Codex model
- [ ] Update `src/orchestrator.py` for TDD pipeline
- [ ] Update `src/tools/static_test_runner.py` for spec-based tests
- [ ] Add integration tests for new pipeline
- [ ] Update CLAUDE.md with new model references
