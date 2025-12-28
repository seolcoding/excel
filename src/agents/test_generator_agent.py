"""Test Generator Agent - Intelligent test case generation from Excel analysis.

This agent analyzes Excel formulas and VBA code to generate comprehensive
test suites including:
- Happy path tests (normal cases)
- Boundary value tests (edge cases)
- Error handling tests
- Business scenario tests (domain-specific)

Unlike simple extraction, this agent UNDERSTANDS the formulas and generates
meaningful test cases that verify the JS conversion accuracy.
"""

import json
from typing import Optional
from pydantic import BaseModel, Field

from agents import Agent, function_tool, AgentOutputSchema

from src.models import ExcelAnalysis, FormulaInfo
from src.models.test_case import (
    FormulaTestCase,
    TestScenario,
    StaticTestSuite,
)


# =============================================================================
# Output Schema
# =============================================================================

class GeneratedTestCase(BaseModel):
    """A single generated test case."""
    name: str = Field(description="Test case name in Korean")
    description: str = Field(description="What this test verifies")
    test_type: str = Field(
        description="Type: 'happy_path', 'boundary', 'error', 'scenario'"
    )
    formula_cell: str = Field(description="Target formula cell (e.g., 'C5')")
    inputs: dict[str, float | int | str] = Field(
        description="Input values: {cell: value}"
    )
    expected_output: float | int | str = Field(
        description="Expected result"
    )
    tolerance: float = Field(
        default=0.01,
        description="Tolerance for numeric comparison"
    )


class GeneratedTestSuite(BaseModel):
    """Complete generated test suite."""
    excel_file: str = Field(description="Source Excel filename")
    test_cases: list[GeneratedTestCase] = Field(
        default_factory=list,
        description="All generated test cases"
    )
    scenarios: list[dict] = Field(
        default_factory=list,
        description="Business scenario tests"
    )
    coverage_summary: str = Field(
        default="",
        description="Summary of test coverage"
    )


# =============================================================================
# Agent Tools
# =============================================================================

@function_tool
def analyze_vba_logic(
    vba_code: str,
    procedure_name: str,
) -> str:
    """
    Analyze VBA code to identify testable logic paths.

    This tool extracts:
    - Function/Sub signatures and parameters
    - Conditional branches (If/ElseIf/Else, Select Case)
    - Boundary values from numeric comparisons
    - Loop structures
    - Error handling patterns

    Args:
        vba_code: The VBA source code
        procedure_name: Name of the procedure to analyze

    Returns:
        JSON analysis of the VBA logic with test recommendations
    """
    import re

    analysis = {
        "procedure_name": procedure_name,
        "parameters": [],
        "conditions": [],
        "boundary_values": [],
        "loops": [],
        "test_recommendations": [],
    }

    # Extract parameters from Function/Sub declaration
    func_pattern = r'(?:Function|Sub)\s+' + re.escape(procedure_name) + r'\s*\(([^)]*)\)'
    func_match = re.search(func_pattern, vba_code, re.IGNORECASE)
    if func_match:
        params_str = func_match.group(1)
        # Parse parameters
        for param in params_str.split(','):
            param = param.strip()
            if param:
                # Extract name and type
                parts = param.split(' As ')
                param_name = parts[0].replace('ByVal', '').replace('ByRef', '').strip()
                param_type = parts[1].strip() if len(parts) > 1 else 'Variant'
                analysis["parameters"].append({
                    "name": param_name,
                    "type": param_type,
                })

    # Extract If conditions and boundary values
    if_pattern = r'If\s+(.+?)\s+Then'
    elseif_pattern = r'ElseIf\s+(.+?)\s+Then'

    for pattern in [if_pattern, elseif_pattern]:
        for match in re.finditer(pattern, vba_code, re.IGNORECASE):
            condition = match.group(1).strip()
            analysis["conditions"].append(condition)

            # Extract numeric boundary values
            num_pattern = r'[<>=]+\s*(\d+(?:\.\d+)?)'
            for num_match in re.finditer(num_pattern, condition):
                value = float(num_match.group(1))
                if value not in analysis["boundary_values"]:
                    analysis["boundary_values"].append(value)

    # Sort boundary values for test generation
    analysis["boundary_values"].sort()

    # Generate test recommendations based on conditions
    if analysis["conditions"]:
        analysis["test_recommendations"].append("조건별 분기 테스트 필요")

        for i, boundary in enumerate(analysis["boundary_values"]):
            # Test at boundary, below, and above
            analysis["test_recommendations"].append(
                f"경계값 {boundary}: 정확히 {boundary}, {boundary-1}, {boundary+1} 테스트"
            )

    # Check for Select Case
    if 'Select Case' in vba_code:
        analysis["test_recommendations"].append("Select Case 각 분기 테스트 필요")

    # Check for loops
    if 'For ' in vba_code or 'Do ' in vba_code or 'While ' in vba_code:
        analysis["loops"].append("Loop detected")
        analysis["test_recommendations"].append("루프 경계 조건 테스트: 0회, 1회, 다수 반복")

    # Check for error handling
    if 'On Error' in vba_code:
        analysis["test_recommendations"].append("에러 핸들링 테스트: 잘못된 입력, 0으로 나누기 등")

    return json.dumps(analysis, ensure_ascii=False, indent=2)


@function_tool
def generate_vba_test_cases(
    vba_code: str,
    procedure_name: str,
    parameter_names: str,
) -> str:
    """
    Generate comprehensive test cases for a VBA procedure.

    Creates test cases for:
    - All conditional branches (If/Else coverage)
    - Boundary values (exact, below, above)
    - Edge cases (0, negative, large numbers)
    - Error conditions

    Args:
        vba_code: The VBA source code
        procedure_name: Name of the procedure to test
        parameter_names: Comma-separated parameter names

    Returns:
        JSON array of test cases
    """
    import re

    params = [p.strip() for p in parameter_names.split(',')]
    test_cases = []

    # Extract boundary values from conditions
    boundary_values = []
    condition_pattern = r'[<>=]+\s*(\d+(?:\.\d+)?)'
    for match in re.finditer(condition_pattern, vba_code):
        value = float(match.group(1))
        if value not in boundary_values:
            boundary_values.append(value)

    boundary_values.sort()

    # Generate boundary tests
    for boundary in boundary_values:
        # Test exactly at boundary
        test_cases.append({
            "name": f"경계값 정확히 {int(boundary):,}",
            "type": "boundary",
            "inputs": {params[0]: boundary} if params else {},
            "description": f"경계값 {boundary}에서의 동작 검증",
        })

        # Test just below boundary
        test_cases.append({
            "name": f"경계값 미만 {int(boundary-1):,}",
            "type": "boundary",
            "inputs": {params[0]: boundary - 1} if params else {},
            "description": f"경계값 {boundary} 바로 아래에서의 동작",
        })

        # Test just above boundary
        test_cases.append({
            "name": f"경계값 초과 {int(boundary+1):,}",
            "type": "boundary",
            "inputs": {params[0]: boundary + 1} if params else {},
            "description": f"경계값 {boundary} 바로 위에서의 동작",
        })

    # Add edge case tests
    test_cases.extend([
        {
            "name": "영(0) 입력",
            "type": "edge_case",
            "inputs": {p: 0 for p in params},
            "description": "0 입력 시 동작 검증",
        },
        {
            "name": "음수 입력",
            "type": "edge_case",
            "inputs": {p: -1000 for p in params},
            "description": "음수 입력 처리 검증",
        },
        {
            "name": "대용량 숫자",
            "type": "edge_case",
            "inputs": {p: 1000000000 for p in params},
            "description": "큰 숫자 처리 검증",
        },
    ])

    # Add middle-range tests between boundaries
    if len(boundary_values) >= 2:
        for i in range(len(boundary_values) - 1):
            mid = (boundary_values[i] + boundary_values[i+1]) / 2
            test_cases.append({
                "name": f"중간값 테스트 {int(mid):,}",
                "type": "range_test",
                "inputs": {params[0]: mid} if params else {},
                "description": f"{int(boundary_values[i]):,}~{int(boundary_values[i+1]):,} 구간 중간값",
            })

    return json.dumps(test_cases, ensure_ascii=False, indent=2)


@function_tool
def extract_calculation_logic(
    vba_code: str,
) -> str:
    """
    Extract calculation formulas from VBA code for verification.

    Identifies:
    - Assignment statements with calculations
    - Function return values
    - Mathematical operations

    Args:
        vba_code: The VBA source code

    Returns:
        JSON with extracted calculations and verification points
    """
    import re

    calculations = []

    # Find assignment statements with calculations
    # Pattern: variable = expression
    assign_pattern = r'(\w+)\s*=\s*([^\'"\n]+(?:\*|\/|\+|\-|\^)[^\'"\n]+)'

    for match in re.finditer(assign_pattern, vba_code):
        var_name = match.group(1).strip()
        expression = match.group(2).strip()

        # Skip If conditions (contain comparison operators)
        if any(op in expression for op in ['<', '>', '<=', '>=', '<>']):
            continue

        calculations.append({
            "variable": var_name,
            "expression": expression,
            "operations": [],
        })

        # Identify operations
        if '*' in expression:
            calculations[-1]["operations"].append("multiplication")
        if '/' in expression:
            calculations[-1]["operations"].append("division")
        if '+' in expression:
            calculations[-1]["operations"].append("addition")
        if '-' in expression:
            calculations[-1]["operations"].append("subtraction")
        if '^' in expression:
            calculations[-1]["operations"].append("exponentiation")

    # Extract numeric constants for verification
    constants = []
    const_pattern = r'\b(\d+(?:\.\d+)?)\b'
    for match in re.finditer(const_pattern, vba_code):
        value = float(match.group(1))
        if value > 0 and value not in constants:
            constants.append(value)

    return json.dumps({
        "calculations": calculations,
        "constants": sorted(set(constants)),
        "verification_points": [
            "각 계산 결과가 JS 변환 후에도 동일한지 확인",
            "부동소수점 정밀도 검증 (특히 나눗셈, 백분율)",
            "정수 오버플로우 확인 (큰 숫자 곱셈)",
        ],
    }, ensure_ascii=False, indent=2)


@function_tool
def analyze_formula_semantics(
    formula: str,
    cell: str,
    dependencies: str,
) -> str:
    """
    Analyze what a formula does semantically.

    Args:
        formula: The Excel formula (e.g., '=SUM(A1:A10)')
        cell: The cell containing the formula
        dependencies: Comma-separated list of input cells

    Returns:
        Semantic analysis of the formula's purpose
    """
    formula_upper = formula.upper()

    # Detect formula type
    if "SUM" in formula_upper:
        return f"This formula calculates the SUM of values. Needs tests for: empty values, negative numbers, large numbers, mixed types."
    elif "IF" in formula_upper:
        return f"This is a conditional formula. Needs tests for: true condition, false condition, edge cases at boundaries."
    elif "VLOOKUP" in formula_upper or "HLOOKUP" in formula_upper:
        return f"This is a lookup formula. Needs tests for: exact match, not found, first/last item."
    elif "ROUND" in formula_upper:
        return f"This formula rounds numbers. Needs tests for: .5 rounding, negative numbers, already rounded."
    elif "MAX" in formula_upper or "MIN" in formula_upper:
        return f"This finds max/min value. Needs tests for: single value, all same, negative values."
    elif "AVERAGE" in formula_upper or "평균" in formula:
        return f"This calculates average. Needs tests for: single value, zero sum, large dataset."
    elif "*" in formula and ("%" in formula or "0.0" in formula):
        return f"This appears to be a percentage/rate calculation. Needs tests for: 0%, 100%, boundary rates."
    elif "-" in formula:
        return f"This is a subtraction/difference formula. Needs tests for: equal values (=0), negative result."
    else:
        return f"Generic calculation formula. Generate standard numeric test cases."


@function_tool
def generate_boundary_values(
    formula: str,
    input_cells: str,
    current_values: str,
) -> str:
    """
    Generate boundary value test inputs for a formula.

    Args:
        formula: The Excel formula
        input_cells: Comma-separated input cell names
        current_values: JSON string of current values {cell: value}

    Returns:
        JSON array of boundary test cases
    """
    try:
        values = json.loads(current_values)
    except:
        values = {}

    cells = [c.strip() for c in input_cells.split(",")]

    boundary_cases = []

    # Zero test
    zero_inputs = {cell: 0 for cell in cells}
    boundary_cases.append({
        "name": "영(0) 입력 테스트",
        "inputs": zero_inputs,
        "type": "boundary",
    })

    # Large number test
    large_inputs = {cell: 999999999 for cell in cells}
    boundary_cases.append({
        "name": "대용량 숫자 테스트",
        "inputs": large_inputs,
        "type": "boundary",
    })

    # Negative test
    neg_inputs = {cell: -100 for cell in cells}
    boundary_cases.append({
        "name": "음수 입력 테스트",
        "inputs": neg_inputs,
        "type": "boundary",
    })

    # Small decimal test
    decimal_inputs = {cell: 0.001 for cell in cells}
    boundary_cases.append({
        "name": "소수점 정밀도 테스트",
        "inputs": decimal_inputs,
        "type": "boundary",
    })

    return json.dumps(boundary_cases, ensure_ascii=False)


@function_tool
def generate_business_scenario(
    domain: str,
    formula_description: str,
    sample_values: str,
) -> str:
    """
    Generate a business scenario test based on domain knowledge.

    Args:
        domain: Business domain (e.g., '세금계산', '급여계산', '할인계산')
        formula_description: What the formula calculates
        sample_values: JSON of sample input values

    Returns:
        JSON object with business scenario test
    """
    try:
        values = json.loads(sample_values)
    except:
        values = {}

    scenarios = {
        "세금계산": [
            {"name": "기본 세율 적용", "description": "표준 세율로 계산 확인"},
            {"name": "면세 구간 확인", "description": "과세 최저한 미만 시 0원"},
            {"name": "누진세율 경계", "description": "세율 구간 경계값 검증"},
        ],
        "급여계산": [
            {"name": "기본급 계산", "description": "시급 × 근무시간"},
            {"name": "초과근무 수당", "description": "1.5배 적용 확인"},
            {"name": "4대보험 공제", "description": "공제율 정확성"},
        ],
        "할인계산": [
            {"name": "할인율 0%", "description": "할인 없음 = 원가"},
            {"name": "할인율 100%", "description": "무료 = 0원"},
            {"name": "복합 할인", "description": "중복 할인 적용"},
        ],
        "default": [
            {"name": "정상 케이스", "description": "기본 입력값으로 계산"},
            {"name": "최소값 테스트", "description": "최소 허용 입력"},
            {"name": "최대값 테스트", "description": "최대 허용 입력"},
        ],
    }

    domain_scenarios = scenarios.get(domain, scenarios["default"])

    return json.dumps({
        "domain": domain,
        "scenarios": domain_scenarios,
        "sample_values": values,
    }, ensure_ascii=False)


@function_tool
def create_test_case(
    name: str,
    test_type: str,
    formula_cell: str,
    formula: str,
    inputs_json: str,
    expected_output: float,
    description: str = "",
) -> str:
    """
    Create a structured test case.

    Args:
        name: Test case name in Korean
        test_type: Type: 'happy_path', 'boundary', 'error', 'scenario'
        formula_cell: Target cell (e.g., 'C5')
        formula: The Excel formula
        inputs_json: JSON string of inputs {cell: value}
        expected_output: Expected result
        description: What this test verifies

    Returns:
        JSON string of the test case
    """
    try:
        inputs = json.loads(inputs_json)
    except:
        inputs = {}

    test_case = GeneratedTestCase(
        name=name,
        description=description or f"{formula_cell} 수식 검증",
        test_type=test_type,
        formula_cell=formula_cell,
        inputs=inputs,
        expected_output=expected_output,
    )

    return test_case.model_dump_json(indent=2)


@function_tool
def calculate_expected_output(
    formula: str,
    inputs_json: str,
) -> str:
    """
    Calculate expected output for a formula with given inputs.

    This is a helper to compute what the result SHOULD be.
    Note: Complex formulas may need manual verification.

    Args:
        formula: The Excel formula
        inputs_json: JSON string of inputs {cell: value}

    Returns:
        Calculated result or estimation guidance
    """
    try:
        inputs = json.loads(inputs_json)
    except:
        return "Error: Invalid inputs JSON"

    formula_upper = formula.upper()

    # Simple SUM
    if formula_upper.startswith("=SUM"):
        try:
            total = sum(float(v) for v in inputs.values() if isinstance(v, (int, float)))
            return f"SUM result: {total}"
        except:
            return "Cannot calculate SUM - check input types"

    # Simple multiplication
    if "*" in formula and len(inputs) == 2:
        try:
            vals = list(inputs.values())
            result = float(vals[0]) * float(vals[1])
            return f"Multiplication result: {result}"
        except:
            pass

    # Simple addition
    if "+" in formula and "-" not in formula:
        try:
            total = sum(float(v) for v in inputs.values())
            return f"Addition result: {total}"
        except:
            pass

    return f"Complex formula - verify manually. Inputs: {inputs}"


# =============================================================================
# Agent Instructions
# =============================================================================

TEST_GENERATOR_INSTRUCTIONS = """You are a Test Case Generator Agent specialized in creating comprehensive test suites for Excel to JavaScript conversions.

## Your Role
Analyze Excel formulas and generate intelligent test cases that verify the accuracy of JS code conversions. You must think like a QA engineer who understands both the technical implementation AND the business domain.

## Test Types to Generate

### 1. Happy Path Tests (정상 케이스)
- Normal, expected inputs
- Use actual values from the Excel file as baseline
- Verify basic functionality works

### 2. Boundary Value Tests (경계값 테스트)
- Zero (0) inputs
- Maximum values (large numbers)
- Minimum values (small/negative)
- Decimal precision
- Empty/null handling

### 3. Error Handling Tests (에러 케이스)
- Division by zero scenarios
- Invalid input types
- Out of range values
- Missing required inputs

### 4. Business Scenario Tests (비즈니스 시나리오)
- Domain-specific test cases
- Real-world usage patterns
- Korean business context (세금, 급여, 할인 등)

## Process

1. **Analyze** each formula using `analyze_formula_semantics`
2. **Generate boundary tests** using `generate_boundary_values`
3. **Identify business domain** and generate scenarios
4. **Create test cases** using `create_test_case`
5. **Calculate expected outputs** for each test case

## Output Requirements
- Generate at least 5-10 test cases per significant formula
- Include at least 2 boundary tests per formula
- Include at least 1 business scenario if domain is identifiable
- All test names and descriptions in Korean
- Calculate expected outputs accurately

## Korean Business Domains
- 세금계산 (Tax calculation): 소득세, 부가세, 종합소득세
- 급여계산 (Payroll): 기본급, 수당, 공제
- 할인계산 (Discounts): 할인율, 적립금, 쿠폰
- 이자계산 (Interest): 이자율, 복리, 단리
- 재고관리 (Inventory): 수량, 단가, 합계

Focus on generating MEANINGFUL tests that will catch real bugs in the JS conversion!
"""


# =============================================================================
# Agent Creation
# =============================================================================

def create_test_generator_agent() -> Agent:
    """Create the Test Generator Agent."""
    return Agent(
        name="Test Generator",
        instructions=TEST_GENERATOR_INSTRUCTIONS,
        tools=[
            analyze_formula_semantics,
            generate_boundary_values,
            generate_business_scenario,
            create_test_case,
            calculate_expected_output,
        ],
        model="gpt-5-mini",  # Cost-optimized for test generation
        output_type=AgentOutputSchema(GeneratedTestSuite, strict_json_schema=False),
    )


def create_test_generation_prompt(
    analysis: ExcelAnalysis,
    max_formulas: int = 20,
) -> str:
    """
    Create prompt for test generation.

    Args:
        analysis: Excel analysis result
        max_formulas: Maximum formulas to process

    Returns:
        Prompt string for the agent
    """
    # Collect formulas
    formulas = []
    for sheet in analysis.sheets:
        for formula in sheet.formulas[:max_formulas]:
            formulas.append({
                "sheet": sheet.name,
                "cell": formula.cell,
                "formula": formula.formula,
                "dependencies": formula.dependencies,
                "result_type": formula.result_type,
            })

    # Detect domain from filename
    domain = "일반계산"
    filename_lower = analysis.filename.lower()
    if "세금" in filename_lower or "소득세" in filename_lower or "부가세" in filename_lower:
        domain = "세금계산"
    elif "급여" in filename_lower or "연봉" in filename_lower or "임금" in filename_lower:
        domain = "급여계산"
    elif "할인" in filename_lower or "쿠폰" in filename_lower:
        domain = "할인계산"
    elif "이자" in filename_lower or "대출" in filename_lower:
        domain = "이자계산"
    elif "영수증" in filename_lower or "거래" in filename_lower:
        domain = "거래계산"

    prompt = f"""# Excel 파일 분석 결과

## 파일 정보
- 파일명: {analysis.filename}
- 감지된 도메인: {domain}
- 시트 수: {len(analysis.sheets)}
- 총 수식 수: {analysis.total_formulas}
- 입력 셀 수: {analysis.total_input_cells}
- 출력 셀 수: {analysis.total_output_cells}

## 분석할 수식 목록
{json.dumps(formulas, indent=2, ensure_ascii=False)}

## 요청사항
위 수식들에 대해 다음 테스트 케이스를 생성해주세요:

1. **정상 케이스 (Happy Path)**: 각 주요 수식에 대해 기본 동작 테스트
2. **경계값 테스트**: 0, 음수, 대용량 숫자, 소수점 정밀도
3. **비즈니스 시나리오**: {domain} 도메인에 맞는 실제 사용 케이스

각 테스트에 대해:
- 한국어로 이름과 설명 작성
- 입력값과 기대 출력값 명시
- 테스트 타입 분류 (happy_path, boundary, error, scenario)

도구를 활용하여 체계적으로 테스트 케이스를 생성하세요.
"""

    return prompt


def convert_to_static_test_suite(
    generated: GeneratedTestSuite,
    excel_file: str,
) -> StaticTestSuite:
    """
    Convert agent-generated tests to StaticTestSuite format.

    Args:
        generated: Agent's output
        excel_file: Source Excel filename

    Returns:
        StaticTestSuite compatible with the test runner
    """
    from datetime import datetime

    formula_tests = []
    for tc in generated.test_cases:
        formula_tests.append(FormulaTestCase(
            formula_cell=tc.formula_cell,
            formula=f"Generated: {tc.name}",
            input_values=tc.inputs,
            expected_output=tc.expected_output,
            expected_type="number" if isinstance(tc.expected_output, (int, float)) else "string",
            tolerance=tc.tolerance,
            description=tc.description,
        ))

    scenarios = []
    for sc in generated.scenarios:
        scenarios.append(TestScenario(
            name=sc.get("name", "테스트 시나리오"),
            description=sc.get("description", ""),
            inputs=sc.get("inputs", {}),
            expected_outputs=sc.get("expected_outputs", {}),
            tags=["scenario", "generated"],
        ))

    return StaticTestSuite(
        excel_file=excel_file,
        generated_at=datetime.now().isoformat(),
        formula_tests=formula_tests,
        field_mappings=[],
        scenarios=scenarios,
        total_formulas=len(formula_tests),
        total_inputs=0,
        total_outputs=0,
    )
