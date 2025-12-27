# Excel → Web App Agent: Tool Stack Research

> 조사 일자: 2025-12-27

## 1. Excel 파싱 라이브러리 (Python)

### 1.1 기본 파싱

| 라이브러리 | 용도 | 장점 | 단점 |
|-----------|------|------|------|
| **[openpyxl](https://openpyxl.readthedocs.io/)** | .xlsx 읽기/쓰기 | 차트, 수식, 서식 지원 | 메모리 사용량 높음 (원본의 50배) |
| **[pandas](https://pandas.pydata.org/)** | 데이터 분석 | 대용량 처리, DataFrame 구조 | 서식/차트 미지원 |
| **[xlrd](https://github.com/python-excel/xlrd)** | .xls (레거시) | 구형 파일 지원 | .xlsx 미지원 |

**권장**: `openpyxl` + `pandas` 조합
- openpyxl: 구조/수식/차트 메타데이터 추출
- pandas: 실제 데이터 처리

### 1.2 수식 파싱 및 평가

| 라이브러리 | 설명 | 특징 |
|-----------|------|------|
| **[formulas](https://formulas.readthedocs.io/)** | Excel 수식 인터프리터 | AST 생성, Python 코드 변환 |
| **[xlcalculator](https://github.com/bradbase/xlcalculator)** | Excel 수식 → Python 변환 | COUNTIF, SUMIFS 등 지원 |
| **[xlcalcmodel](https://pypi.org/project/xlcalcmodel/)** | 고성능 계산 엔진 | JSON 기반 모델, NumPy 백엔드 |

**권장**: `formulas` 또는 `xlcalculator`
```python
from formulas import Parser

# 수식 파싱 → AST → 평가
parser = Parser()
ast = parser.ast('=SUM(A1:A10) + IF(B1>0, C1, D1)')
```

### 1.3 VBA 매크로 추출

| 라이브러리 | 설명 | 특징 |
|-----------|------|------|
| **[oletools (olevba)](https://github.com/decalage2/oletools)** | VBA 코드 추출 | 난독화 해제, 보안 분석용 |
| **[xlwings](https://www.xlwings.org/)** | Excel ↔ Python 통합 | VBA 실행 가능 (Excel 필요) |

**권장**: `oletools.olevba`
```python
from oletools.olevba import VBA_Parser

vbaparser = VBA_Parser('file.xlsm')
for (filename, stream_path, vba_code) in vbaparser.extract_macros():
    print(vba_code)  # VBA 소스코드 추출
```

### 1.4 차트 추출

| 라이브러리 | 설명 |
|-----------|------|
| **openpyxl** | 차트 메타데이터 (타입, 데이터 범위, 제목) 추출 가능 |

```python
from openpyxl import load_workbook

wb = load_workbook('file.xlsx')
for sheet in wb:
    for chart in sheet._charts:
        print(chart.type)      # 'barChart', 'lineChart', etc.
        print(chart.series)    # 데이터 시리즈
```

---

## 2. 웹앱 코드 생성

### 2.1 접근 방식

| 방식 | 설명 | 추천 |
|------|------|------|
| **LLM 직접 생성** | GPT-4.1이 HTML/CSS/JS 코드 직접 생성 | ✅ 추천 |
| **Jinja2 템플릿** | 사전 정의된 템플릿에 데이터 삽입 | 보조적 사용 |
| **React/Vue 컴포넌트** | LLM이 컴포넌트 코드 생성 | 복잡한 앱용 |

### 2.2 추천 스택

```
[LLM (GPT-4.1)]
    ↓ 생성
[HTML + Tailwind CSS + Vanilla JS]
    ↓ (필요시)
[Chart.js / ECharts] - 차트 렌더링
```

**Tailwind CSS 사용 이유**:
- CDN 한 줄로 사용 가능
- LLM이 유틸리티 클래스 잘 생성함
- 번들링 불필요

### 2.3 Jinja2 (보조 템플릿)

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('dashboard.html')

html = template.render(
    title="Sales Dashboard",
    charts=chart_configs,
    data_tables=table_data
)
```

---

## 3. OpenAI Agents SDK 도구 통합

### 3.1 Function Tool 정의 패턴

```python
from agents import Agent, function_tool, RunContextWrapper
from pydantic import BaseModel
from typing import Any

# 엑셀 분석 도구
@function_tool
async def analyze_excel(file_path: str) -> dict:
    """Analyze Excel file structure, formulas, and VBA macros."""
    # openpyxl, formulas, oletools 사용
    return {
        "sheets": [...],
        "formulas": [...],
        "vba_modules": [...],
        "charts": [...]
    }

# 코드 생성 도구
@function_tool
async def generate_component(
    component_type: str,
    data_schema: dict,
    style_preferences: str
) -> str:
    """Generate HTML/CSS/JS component code."""
    # LLM 호출 또는 템플릿 렌더링
    return "<div>...</div>"

# 코드 검증 도구
@function_tool
async def validate_code(html: str, css: str, js: str) -> dict:
    """Validate generated web code for errors."""
    return {"valid": True, "errors": []}
```

### 3.2 Agent 구성

```python
from agents import Agent, ModelSettings

analyzer_agent = Agent(
    name="Excel Analyzer",
    instructions="""
    Analyze Excel files to extract:
    1. Data structure and types
    2. Formulas and their dependencies
    3. VBA macros and their functionality
    4. Charts and visualizations
    """,
    tools=[analyze_excel, parse_formula, extract_vba],
    model="gpt-4.1",
)

generator_agent = Agent(
    name="Code Generator",
    instructions="""
    Generate clean, modern web code using:
    - Semantic HTML5
    - Tailwind CSS for styling
    - Vanilla JavaScript for interactivity
    - Chart.js for data visualization
    """,
    tools=[generate_component, generate_chart_config],
    model="gpt-4.1",
    model_settings=ModelSettings(temperature=0.3),
)
```

---

## 4. 프론트엔드 프리뷰

### 4.1 Sandboxed iframe 방식

```javascript
// 안전한 코드 실행 환경
const iframe = document.createElement('iframe');
iframe.sandbox = 'allow-scripts';  // 제한된 권한

iframe.srcdoc = `
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  ${generatedHTML}
  <script>${generatedJS}</script>
</body>
</html>
`;

document.getElementById('preview').appendChild(iframe);
```

### 4.2 React 컴포넌트 (프론트엔드)

```tsx
// components/CodePreview.tsx
import { useEffect, useRef } from 'react';

interface Props {
  html: string;
  css: string;
  js: string;
}

export function CodePreview({ html, css, js }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (iframeRef.current) {
      iframeRef.current.srcdoc = `
        <!DOCTYPE html>
        <html>
        <head>
          <style>${css}</style>
          <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body>${html}</body>
        <script>${js}</script>
        </html>
      `;
    }
  }, [html, css, js]);

  return (
    <iframe
      ref={iframeRef}
      sandbox="allow-scripts"
      className="w-full h-full border-0"
    />
  );
}
```

---

## 5. 최종 도구 스택 추천

### Backend (Python)

```
openai-agents>=0.2.9      # Agent 오케스트레이션
openpyxl>=3.1.0           # Excel 읽기/쓰기
pandas>=2.0.0             # 데이터 처리
formulas>=1.3.0           # 수식 파싱/평가
oletools>=0.60            # VBA 추출
jinja2>=3.1.0             # HTML 템플릿 (보조)
fastapi>=0.100.0          # API 서버
uvicorn>=0.23.0           # ASGI 서버
```

### Frontend (TypeScript/React)

```
next.js                   # React 프레임워크
tailwindcss               # 스타일링
@monaco-editor/react      # 코드 에디터 (선택)
chart.js / react-chartjs-2  # 차트 렌더링
```

### 외부 CDN (생성된 웹앱용)

```html
<!-- 생성된 웹앱에 포함될 CDN -->
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js"></script>
```

---

## 6. 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ File Upload  │  │ Code Editor  │  │   Live Preview       │   │
│  │ (Excel)      │  │ (Monaco)     │  │   (Sandboxed iframe) │   │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘   │
│         │                                                        │
│         ↓ API Call                                              │
└─────────────────────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + Agents)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Agent Orchestration                       │ │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │ │
│  │  │  Analyzer   │ → │  Planner    │ → │  Generator  │       │ │
│  │  │  Agent      │   │  Agent      │   │  Agents     │       │ │
│  │  └─────────────┘   └─────────────┘   └─────────────┘       │ │
│  │         ↓                                   ↓               │ │
│  │  ┌─────────────┐                   ┌─────────────┐         │ │
│  │  │  Tools      │                   │  Maker      │         │ │
│  │  │  - openpyxl │                   │  Checker    │         │ │
│  │  │  - formulas │                   │  Loop       │         │ │
│  │  │  - oletools │                   └─────────────┘         │ │
│  │  └─────────────┘                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Generated Output                             │
├─────────────────────────────────────────────────────────────────┤
│  index.html + styles.css + app.js + (assets)                    │
│  → 다운로드 가능한 ZIP 또는 라이브 프리뷰                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sources

### Excel Libraries
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [formulas Documentation](https://formulas.readthedocs.io/)
- [xlcalculator GitHub](https://github.com/bradbase/xlcalculator)
- [oletools olevba](https://github.com/decalage2/oletools/wiki/olevba)

### Code Generation
- [Using LLMs to Generate HTML, CSS, and React Code](https://meenumatharu.medium.com/using-llms-to-generate-html-css-and-react-code-with-a-real-example-0b31f8b9838c)
- [Best LLMs for Web Development 2025](https://unbundl.com/blogs/news/best-llms-for-web-development-in-2025)

### OpenAI Agents SDK
- [OpenAI Agents Python GitHub](https://github.com/openai/openai-agents-python)
- [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/)

### Preview Sandbox
- [Building Secure Code Sandbox](https://medium.com/@muyiwamighty/building-a-secure-code-sandbox-what-i-learned-about-iframe-isolation-and-postmessage-a6e1c45966df)
