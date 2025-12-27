# Product Requirements Document (PRD)

## Excel → Web App Converter Agent

> **Version**: 1.0
> **Date**: 2025-12-27
> **Status**: POC (Proof of Concept)

---

## 1. Executive Summary

### 1.1 제품 비전

**"엑셀 기반 비즈니스 도구를 코딩 없이 웹앱으로 변환"**

기업과 개인이 사용하는 엑셀 기반 계산기, 서식, 템플릿을 AI 에이전트가 자동으로 분석하여 독립 실행 가능한 웹 애플리케이션으로 변환합니다.

### 1.2 핵심 가치 제안

| 기존 문제 | 해결책 |
|----------|--------|
| 엑셀 파일 공유/배포 어려움 | 웹 URL로 누구나 접근 가능 |
| 엑셀 설치 필요 | 브라우저만 있으면 동작 |
| VBA 호환성 문제 | JavaScript로 완벽 변환 |
| 모바일 사용 불가 | 반응형 웹앱으로 어디서든 사용 |
| 인쇄 레이아웃 깨짐 | 엑셀과 동일한 인쇄 출력 |

### 1.3 타겟 사용자

**비개발자 / 비즈니스 사용자**

- 경리/회계 담당자
- 인사/총무 담당자
- 영업/마케팅 담당자
- 소규모 사업자
- 프리랜서

**사용자 특성:**
- 코드 작성 불가
- 엑셀 사용에 익숙
- 웹 기술 이해도 낮음
- 결과물의 정확성 중시

---

## 2. Problem Statement

### 2.1 현재 상황

조직 내에서 수백 개의 엑셀 기반 도구가 사용되고 있음:

| 카테고리 | 예시 | 현재 문제점 |
|----------|------|------------|
| **계산기** | 4대보험 계산기, 종합소득세 계산기 | 수식 오류 시 추적 어려움 |
| **서식/템플릿** | 견적서, 영수증, 계약서 | 버전 관리 어려움 |
| **비즈니스 로직** | 재고관리, 매출분석 | VBA 호환성 문제 |
| **인쇄 양식** | 교육일지, 업무보고서 | 레이아웃 깨짐 |

### 2.2 Pain Points

1. **배포의 어려움**: 엑셀 파일을 이메일로 공유, 버전 충돌
2. **접근성 제한**: 엑셀 미설치 환경에서 사용 불가
3. **VBA 호환성**: Mac, 모바일에서 매크로 동작 안 함
4. **인쇄 품질**: 다른 프린터/환경에서 레이아웃 다름
5. **데이터 보안**: 파일 복사로 인한 정보 유출

---

## 3. Solution Overview

### 3.1 제품 개요

AI 에이전트가 엑셀 파일을 분석하여:

1. **데이터 구조** 파악
2. **수식/VBA 로직** 추출 및 JavaScript 변환
3. **입력 폼** 자동 생성
4. **인쇄 최적화 레이아웃** 구현
5. **독립 실행 웹앱** 생성

### 3.2 핵심 워크플로우

```
┌──────────────────┐
│   Excel Upload   │
│  (.xlsx, .xlsm)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   AI Analysis    │
│  - 구조 분석     │
│  - 수식 파싱     │
│  - VBA 추출      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Code Generate  │
│  - 입력 폼       │
│  - 계산 로직     │
│  - 인쇄 레이아웃 │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Web App Output │
│  - Single HTML   │
│  - 프리뷰        │
│  - 다운로드      │
└──────────────────┘
```

---

## 4. Functional Requirements

### 4.1 입력 (Excel 파일)

#### 4.1.1 지원 파일 형식

| 형식 | 우선순위 | 설명 |
|------|---------|------|
| `.xlsx` | P0 (필수) | Excel 2007+ 표준 |
| `.xlsm` | P0 (필수) | VBA 매크로 포함 |
| `.xls` | P1 (권장) | Excel 97-2003 레거시 |

#### 4.1.2 지원 기능

| 기능 | 우선순위 | POC 범위 |
|------|---------|---------|
| 셀 데이터 (텍스트, 숫자, 날짜) | P0 | ✅ 포함 |
| 기본 수식 (SUM, IF, AVERAGE 등) | P0 | ✅ 포함 |
| 복잡한 수식 (VLOOKUP, INDEX/MATCH) | P0 | ✅ 포함 |
| VBA 매크로 | P0 | ✅ 포함 |
| 셀 서식 (폰트, 색상, 테두리) | P0 | ✅ 포함 |
| 병합 셀 | P0 | ✅ 포함 |
| 인쇄 영역 설정 | P0 | ✅ 포함 |
| 조건부 서식 | P2 | ❌ 제외 |
| 차트 | P2 | ❌ 제외 |
| 피벗 테이블 | P2 | ❌ 제외 |
| 외부 데이터 연결 | P2 | ❌ 제외 |

#### 4.1.3 입력 셀 자동 감지

시스템은 다음 패턴으로 "입력 셀"을 자동 감지:

- 빈 셀 중 수식에서 참조되는 셀
- 셀 보호가 해제된 셀
- 특정 색상/서식이 적용된 셀 (예: 노란색 배경)
- VBA에서 참조하는 입력 셀

### 4.2 출력 (Web App)

#### 4.2.1 생성 결과물

```
output/
├── index.html      # 단일 HTML 파일 (모든 것 포함)
└── (선택적)
    ├── style.css   # 분리된 스타일
    └── app.js      # 분리된 로직
```

**단일 HTML 원칙**: 모든 CSS, JS를 인라인으로 포함하여 파일 하나만으로 동작

#### 4.2.2 UI 구성

```
┌─────────────────────────────────────────────────────────┐
│  [로고/제목]                              [인쇄] [리셋] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              입력 폼 영역                        │   │
│  │                                                  │   │
│  │  이름: [_______________]                        │   │
│  │  금액: [_______________]                        │   │
│  │  날짜: [_______________]                        │   │
│  │                                                  │   │
│  │            [계산하기]                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              결과/인쇄 영역                      │   │
│  │                                                  │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │         (엑셀 레이아웃 그대로)           │   │   │
│  │  │                                          │   │   │
│  │  │    견 적 서                              │   │   │
│  │  │    ─────────────────                     │   │   │
│  │  │    품목: ...                             │   │   │
│  │  │    금액: ₩1,000,000                     │   │   │
│  │  │                                          │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  │                                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 4.2.3 핵심 기능

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| **입력 폼** | 엑셀 입력 셀을 웹 폼 필드로 변환 | P0 |
| **실시간 계산** | 입력 시 수식 자동 재계산 | P0 |
| **인쇄 미리보기** | 엑셀과 동일한 레이아웃 표시 | P0 |
| **인쇄 기능** | 브라우저 인쇄 (Ctrl+P) 최적화 | P0 |
| **입력 검증** | 숫자/날짜/텍스트 타입 검증 | P1 |
| **로컬 저장** | 입력값 브라우저 저장 (LocalStorage) | P1 |
| **리셋 기능** | 모든 입력값 초기화 | P0 |

#### 4.2.4 인쇄 요구사항

| 요구사항 | 상세 |
|----------|------|
| 페이지 크기 | A4 기본, 원본 설정 반영 |
| 여백 | 엑셀 인쇄 설정과 동일 |
| 레이아웃 | 셀 병합, 테두리, 폰트 정확히 재현 |
| 헤더/푸터 | 페이지 번호, 날짜 등 |
| 페이지 나눔 | 원본 페이지 구분 유지 |

**성공 기준**: 엑셀에서 인쇄한 결과와 웹앱에서 인쇄한 결과가 **육안으로 구분 불가능**해야 함

### 4.3 VBA 변환

#### 4.3.1 지원 VBA 기능

| VBA 기능 | JavaScript 변환 | 우선순위 |
|----------|----------------|---------|
| 변수, 상수 | `let`, `const` | P0 |
| 조건문 (If/Then/Else) | `if/else` | P0 |
| 반복문 (For, While) | `for`, `while` | P0 |
| 함수/프로시저 | `function` | P0 |
| Range 조작 | DOM 조작 | P0 |
| 셀 값 읽기/쓰기 | Input/Output 바인딩 | P0 |
| MsgBox | `alert()` 또는 모달 | P1 |
| InputBox | HTML input 또는 모달 | P1 |
| 워크시트 함수 호출 | JS 함수 구현 | P0 |
| 사용자 정의 함수 | JS 함수 변환 | P0 |
| 이벤트 핸들러 | DOM 이벤트 | P1 |
| 외부 파일 접근 | ❌ 미지원 | - |
| ActiveX 컨트롤 | ❌ 미지원 | - |

#### 4.3.2 VBA 변환 예시

**원본 VBA:**
```vba
Sub Calculate()
    Dim total As Double
    total = Range("B2").Value * Range("B3").Value
    If total > 10000 Then
        Range("B4").Value = total * 0.9  ' 10% 할인
    Else
        Range("B4").Value = total
    End If
End Sub
```

**변환된 JavaScript:**
```javascript
function calculate() {
    const b2 = parseFloat(document.getElementById('input-B2').value) || 0;
    const b3 = parseFloat(document.getElementById('input-B3').value) || 0;
    let total = b2 * b3;

    if (total > 10000) {
        total = total * 0.9;  // 10% 할인
    }

    document.getElementById('output-B4').textContent = formatNumber(total);
}
```

---

## 5. Non-Functional Requirements

### 5.1 성능

| 메트릭 | 목표 |
|--------|------|
| 파일 분석 시간 | < 30초 (10MB 이하 파일) |
| 코드 생성 시간 | < 60초 |
| 웹앱 로딩 시간 | < 2초 |
| 계산 반응 시간 | < 100ms |

### 5.2 정확성

| 항목 | 기준 |
|------|------|
| 수식 계산 | 엑셀과 100% 동일한 결과 |
| VBA 로직 | 동일한 입력 → 동일한 출력 |
| 인쇄 레이아웃 | 육안 구분 불가 수준 |
| 숫자 포맷 | 원본 서식 유지 (천단위, 소수점 등) |

### 5.3 호환성

| 브라우저 | 지원 |
|----------|------|
| Chrome (최신) | ✅ |
| Safari (최신) | ✅ |
| Firefox (최신) | ✅ |
| Edge (최신) | ✅ |
| IE 11 | ❌ |

| 디바이스 | 지원 |
|----------|------|
| Desktop | ✅ (인쇄 최적화) |
| Tablet | ✅ (입력/조회) |
| Mobile | ✅ (입력/조회) |

---

## 6. User Stories

### 6.1 핵심 사용자 스토리

#### US-01: 엑셀 계산기 변환
```
AS A 경리 담당자
I WANT TO 4대보험 계산기 엑셀을 웹앱으로 변환
SO THAT 직원들이 엑셀 없이도 보험료를 계산할 수 있다

Acceptance Criteria:
- 급여 입력 시 4대보험료 자동 계산
- 계산 결과가 엑셀과 100% 동일
- 모바일에서도 사용 가능
```

#### US-02: 견적서 템플릿 변환
```
AS A 영업 담당자
I WANT TO 견적서 엑셀 템플릿을 웹앱으로 변환
SO THAT 현장에서 바로 견적서를 작성하고 인쇄할 수 있다

Acceptance Criteria:
- 품목, 수량, 단가 입력 폼
- 합계/부가세 자동 계산
- A4 인쇄 시 엑셀 견적서와 동일한 레이아웃
```

#### US-03: VBA 자동화 도구 변환
```
AS A 재고 관리자
I WANT TO VBA 기반 재고관리 엑셀을 웹앱으로 변환
SO THAT Mac 사용자도 재고 관리 기능을 사용할 수 있다

Acceptance Criteria:
- 입고/출고 버튼 클릭 시 VBA 로직 동작
- 재고 현황 실시간 업데이트
- 재고 부족 경고 표시
```

#### US-04: 인쇄 양식 변환
```
AS A 인사 담당자
I WANT TO 근로계약서 양식을 웹앱으로 변환
SO THAT 입력 후 바로 인쇄하여 서명받을 수 있다

Acceptance Criteria:
- 직원 정보 입력 폼
- 인쇄 미리보기에서 레이아웃 확인
- 인쇄 시 A4 용지에 정확히 맞춤
```

---

## 7. Success Metrics

### 7.1 POC 성공 기준

| 기준 | 측정 방법 | 목표 |
|------|----------|------|
| **수식 정확도** | 10개 테스트 파일의 계산 결과 비교 | 100% 일치 |
| **VBA 변환율** | 샘플 VBA 코드의 기능 동작 | 90% 이상 동작 |
| **인쇄 품질** | 엑셀 vs 웹앱 인쇄 결과 육안 비교 | 구분 불가 |
| **입력-출력 매핑** | 입력 셀 자동 감지 정확도 | 95% 이상 |

### 7.2 테스트 파일 목록

| 파일명 | 테스트 항목 |
|--------|------------|
| `4대보험_자동계산기_엑셀템플릿.xlsx` | 수식 계산 |
| `종합소득세 엑셀 간이 계산기 v2.1.xlsx` | 복잡한 수식 |
| `엑셀 자동화 견적서 v1.0.xlsm` | VBA 매크로 |
| `재고관리 프로그램 5일차(최종).xlsm` | 복잡한 VBA |
| `엑셀 간이영수증 표준 양식 v2.0.xlsx` | 인쇄 레이아웃 |
| `엑셀 표준 근로계약서 양식 v2.0.xlsx` | 폼 + 인쇄 |
| `교육일지 양식 01.xlsx` | 단순 템플릿 |

---

## 8. Technical Constraints

### 8.1 기술 스택 (확정)

| 레이어 | 기술 | 이유 |
|--------|------|------|
| Backend | Python + FastAPI | Agents SDK, 엑셀 라이브러리 |
| Agent | OpenAI Agents SDK | 멀티 에이전트 오케스트레이션 |
| Excel 파싱 | openpyxl + pandas | 구조/데이터 추출 |
| 수식 변환 | formulas | Excel → Python/JS |
| VBA 추출 | oletools | 매크로 코드 추출 |
| 생성 웹앱 | Vanilla HTML + Bootstrap + Alpine.js | LLM 최적 |
| 인쇄 CSS | @media print | 인쇄 레이아웃 |

### 8.2 제약 사항

| 제약 | 설명 |
|------|------|
| 파일 크기 | 최대 10MB |
| 시트 수 | 최대 10개 시트 |
| VBA 복잡도 | 외부 참조, ActiveX 미지원 |
| 실시간 협업 | 지원 안 함 (단일 사용자) |
| 데이터 저장 | 서버 저장 없음 (로컬만) |

---

## 9. Out of Scope (POC)

다음 기능은 POC 범위에서 **제외**:

- ❌ 차트 변환
- ❌ 피벗 테이블 변환
- ❌ 조건부 서식
- ❌ 다중 사용자/협업
- ❌ 서버 데이터 저장
- ❌ 사용자 인증
- ❌ 버전 관리
- ❌ 템플릿 마켓플레이스

---

## 10. Iterative Improvement Loop

### 10.1 에이전트 출력의 특성

AI 에이전트는 **휴리스틱(heuristic)** 출력을 생성하므로:

- 동일 입력에도 다른 결과 가능
- 100% 정확성 보장 불가
- **반복 개선(iteration)이 필수**

### 10.2 테스트 기반 개선 루프

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPROVEMENT LOOP                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │  1. GENERATE │ ← Agent가 웹앱 코드 생성                       │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  2. TEST     │ ← 자동화된 테스트 실행                         │
│  │              │   - 수식 계산 검증                             │
│  │              │   - VBA 로직 검증                              │
│  │              │   - 인쇄 레이아웃 비교                         │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  3. EVALUATE │ ← 테스트 결과 평가                             │
│  │              │   - Pass: 완료                                │
│  │              │   - Fail: 피드백 생성                          │
│  └──────┬───────┘                                               │
│         │                                                       │
│    ┌────┴────┐                                                  │
│    │  Pass?  │                                                  │
│    └────┬────┘                                                  │
│    Yes  │  No                                                   │
│    │    │                                                       │
│    ▼    ▼                                                       │
│  ┌────┐ ┌──────────────┐                                        │
│  │DONE│ │ 4. FEEDBACK  │ ← 오류 내용을 Agent에게 전달            │
│  └────┘ │              │   - 어떤 셀이 틀렸는지                   │
│         │              │   - 기대값 vs 실제값                     │
│         └──────┬───────┘                                        │
│                │                                                │
│                ▼                                                │
│         ┌──────────────┐                                        │
│         │ 5. REGENERATE│ ← 피드백 반영하여 재생성                 │
│         └──────┬───────┘                                        │
│                │                                                │
│                └──────────────────┐                             │
│                                   │ (최대 N회 반복)              │
│  ┌────────────────────────────────┘                             │
│  │                                                              │
│  └──→ [2. TEST로 돌아감]                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 자동화된 테스트 항목

#### 10.3.1 수식 검증 테스트

```python
class FormulaTest:
    """엑셀 수식 결과와 웹앱 계산 결과 비교"""

    def test_calculation(self, excel_file, webapp_html):
        # 1. 엑셀에서 테스트 케이스 추출
        test_cases = extract_test_cases(excel_file)

        # 2. 웹앱에 입력값 주입
        for case in test_cases:
            inject_inputs(webapp_html, case.inputs)

        # 3. 결과 비교
        for case in test_cases:
            expected = case.expected_outputs
            actual = get_webapp_outputs(webapp_html)

            assert actual == expected, f"""
                Cell {case.cell}:
                Expected: {expected}
                Actual: {actual}
            """
```

#### 10.3.2 VBA 로직 검증 테스트

```python
class VBALogicTest:
    """VBA 동작과 JavaScript 동작 비교"""

    def test_vba_function(self, vba_code, js_code, test_inputs):
        # 1. VBA 실행 결과 (사전 기록 또는 xlwings)
        vba_result = run_vba(vba_code, test_inputs)

        # 2. JavaScript 실행 결과
        js_result = run_js(js_code, test_inputs)

        # 3. 비교
        assert vba_result == js_result
```

#### 10.3.3 인쇄 레이아웃 검증 테스트

```python
class PrintLayoutTest:
    """엑셀 인쇄 vs 웹앱 인쇄 레이아웃 비교"""

    def test_print_layout(self, excel_pdf, webapp_pdf):
        # 1. PDF를 이미지로 변환
        excel_img = pdf_to_image(excel_pdf)
        webapp_img = pdf_to_image(webapp_pdf)

        # 2. 이미지 유사도 비교 (SSIM)
        similarity = compare_images(excel_img, webapp_img)

        # 3. 95% 이상 유사해야 통과
        assert similarity >= 0.95, f"Layout similarity: {similarity}"
```

### 10.4 피드백 생성 전략

| 테스트 실패 유형 | 피드백 내용 |
|-----------------|------------|
| 수식 계산 오류 | "셀 B5의 계산이 틀림. 기대값: 10000, 실제값: 9000. 수식: =B3*B4" |
| VBA 로직 오류 | "Calculate 함수 실행 후 C10이 업데이트되지 않음" |
| 레이아웃 오류 | "3열의 너비가 좁음. 텍스트가 잘림" |
| 입력 필드 누락 | "셀 A2가 입력 필드로 인식되지 않음" |

### 10.5 개선 루프 설정

```python
class ImprovementLoop:
    MAX_ITERATIONS = 5  # 최대 반복 횟수
    PASS_THRESHOLD = 0.95  # 95% 이상 테스트 통과 시 성공

    async def run(self, excel_file):
        for iteration in range(self.MAX_ITERATIONS):
            # 1. 생성
            webapp = await self.generate(excel_file, feedback=self.feedback)

            # 2. 테스트
            test_results = await self.test(webapp)

            # 3. 평가
            pass_rate = test_results.pass_count / test_results.total

            if pass_rate >= self.PASS_THRESHOLD:
                return webapp  # 성공!

            # 4. 피드백 생성
            self.feedback = self.generate_feedback(test_results.failures)

            print(f"Iteration {iteration + 1}: {pass_rate:.1%} pass rate")

        raise Exception("Max iterations reached without passing")
```

### 10.6 휴먼 인 더 루프 (선택적)

자동 테스트로 검증 불가능한 경우:

```
┌─────────────────────────────────────────────────────┐
│  [자동 테스트 통과]                                  │
│         │                                           │
│         ▼                                           │
│  ┌──────────────┐                                   │
│  │ HUMAN REVIEW │ ← 인쇄 미리보기 확인               │
│  │              │   - "레이아웃이 맞나요?" [Y/N]    │
│  │              │   - "수정 필요한 부분?" [입력]    │
│  └──────┬───────┘                                   │
│         │                                           │
│    Approve / Request Changes                        │
│         │                                           │
│         ▼                                           │
│    [완료] 또는 [재생성]                              │
└─────────────────────────────────────────────────────┘
```

---

## 11. Milestones

### Phase 1: Foundation (Week 1)
- [x] 아키텍처 설계
- [x] PRD 작성
- [ ] 프로젝트 세팅
- [ ] 기본 Excel 파싱 도구 구현
- [ ] Analyzer Agent 구현

### Phase 2: Core Features (Week 2)
- [ ] 수식 파싱 및 JS 변환
- [ ] 입력 폼 자동 생성
- [ ] 기본 인쇄 레이아웃
- [ ] Table/Form Generator 구현

### Phase 3: VBA & Print (Week 3)
- [ ] VBA 추출 및 분석
- [ ] VBA → JavaScript 변환
- [ ] 인쇄 CSS 최적화
- [ ] Calculator Generator 구현

### Phase 4: Polish & Test (Week 4)
- [ ] Maker-Checker 루프 구현
- [ ] 7개 테스트 파일 검증
- [ ] 버그 수정 및 개선
- [ ] POC 데모 준비

---

## 11. Appendix

### A. 샘플 엑셀 파일 분석

#### A.1 파일 목록 (excel_files/)

```
excel_files/
├── 4대보험_자동계산기_엑셀템플릿.xlsx     # 계산기
├── 종합소득세 엑셀 간이 계산기 v2.1.xlsx  # 계산기
├── 엑셀 자동화 견적서 v1.0.xlsm          # VBA 템플릿
├── 엑셀 간이영수증 표준 양식 v2.0.xlsx    # 인쇄 양식
├── 엑셀 표준 근로계약서 양식 v2.0.xlsx    # 인쇄 양식
├── 교육일지 양식 01~06.xlsx              # 템플릿
├── 주간업무보고 표준양식.xlsx            # 템플릿
├── VBA프로젝트.../
│   └── 재고관리 프로그램 1~5일차.xlsm    # VBA 프로그램
└── 엑셀서식(20160517)/                   # 450+ 서식
    ├── 간이영수증/
    ├── 거래명세서/
    ├── 견적서/
    └── ...
```

#### A.2 복잡도 분류

| 복잡도 | 파일 유형 | 예상 변환 난이도 |
|--------|----------|-----------------|
| **Low** | 단순 템플릿 (교육일지, 업무보고) | 쉬움 |
| **Medium** | 수식 포함 (계산기, 견적서) | 보통 |
| **High** | VBA 포함 (재고관리, 자동화) | 어려움 |

### B. 엑셀 수식 → JavaScript 매핑

| Excel 함수 | JavaScript 구현 |
|-----------|----------------|
| `SUM(range)` | `arr.reduce((a,b) => a+b, 0)` |
| `AVERAGE(range)` | `arr.reduce((a,b) => a+b) / arr.length` |
| `IF(cond, t, f)` | `cond ? t : f` |
| `VLOOKUP(v, r, i, 0)` | `lookup(v, table, i)` |
| `ROUND(n, d)` | `Math.round(n * 10**d) / 10**d` |
| `TODAY()` | `new Date()` |
| `CONCATENATE(...)` | `[...args].join('')` |

### C. 인쇄 CSS 가이드

```css
@media print {
    @page {
        size: A4;
        margin: 20mm;
    }

    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    .no-print {
        display: none !important;
    }

    .print-area {
        width: 100%;
        page-break-inside: avoid;
    }

    table {
        border-collapse: collapse;
    }

    td, th {
        border: 1px solid #000;
        padding: 4px 8px;
    }
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-27 | AI Agent | Initial PRD |
