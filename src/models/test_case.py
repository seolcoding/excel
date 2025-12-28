"""Test case models for Excel to WebApp validation.

Automatically generates deterministic test cases from Excel files:
- Input cells → expected input values
- Formula cells → expected output values
- Test suite for automated validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from enum import Enum


class CellValue(BaseModel):
    """A cell's address and its value."""
    cell: str  # e.g., 'A1'
    value: Any  # The actual value (number, string, bool, etc.)
    data_type: str  # 'number', 'string', 'boolean', 'date'


class FormulaTestCase(BaseModel):
    """
    A test case for a single formula.

    Given specific input values, the formula should produce the expected output.
    This enables deterministic testing of Excel → JS conversion accuracy.
    """
    formula_cell: str = Field(description="Cell containing the formula (e.g., 'C5')")
    formula: str = Field(description="The Excel formula (e.g., '=SUM(A1:A3)')")

    # Input values that produce the expected output
    input_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of input cell → value (e.g., {'A1': 10, 'A2': 20})"
    )

    # Expected output when formula is evaluated with given inputs
    expected_output: Any = Field(description="Expected result value")
    expected_type: str = Field(
        default="number",
        description="Expected result type: 'number', 'string', 'boolean', 'date'"
    )

    # Tolerance for numeric comparisons
    tolerance: float = Field(
        default=0.0001,
        description="Tolerance for floating point comparisons"
    )

    # Optional metadata
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of what this test verifies"
    )

    def generate_js_test(self, js_function_name: str = "calculate") -> str:
        """Generate JavaScript test code for this test case."""
        inputs_js = ", ".join(
            f"{v}" if isinstance(v, (int, float, bool))
            else f"'{v}'" if isinstance(v, str)
            else "null"
            for v in self.input_values.values()
        )

        expected_js = (
            f"{self.expected_output}" if isinstance(self.expected_output, (int, float, bool))
            else f"'{self.expected_output}'" if isinstance(self.expected_output, str)
            else "null"
        )

        return f"""
// Test: {self.formula_cell} = {self.formula}
// Inputs: {self.input_values}
test('{self.formula_cell}: {self.formula}', () => {{
    const result = {js_function_name}({inputs_js});
    expect(result).toBeCloseTo({expected_js}, {int(-1 * __import__('math').log10(self.tolerance))});
}});
"""


class InputOutputMapping(BaseModel):
    """
    Mapping between Excel input cells and WebApp form fields.

    Used to:
    1. Set input values in the web form
    2. Read output values from the web form
    3. Compare with expected values
    """
    # Input field mapping
    excel_input_cell: str = Field(description="Excel cell for input (e.g., 'B2')")
    webapp_field_id: Optional[str] = Field(
        default=None,
        description="WebApp form field ID (e.g., 'input_price')"
    )
    field_label: Optional[str] = Field(
        default=None,
        description="Korean label for the field (e.g., '단가')"
    )
    sample_value: Any = Field(description="Sample value for testing")

    # For output cells
    excel_output_cell: Optional[str] = Field(
        default=None,
        description="Excel cell for output (e.g., 'D5')"
    )
    expected_value: Optional[Any] = Field(
        default=None,
        description="Expected output value"
    )


class TestScenario(BaseModel):
    """
    A complete test scenario with multiple inputs and expected outputs.

    Represents a single "row" of test data that exercises the full
    calculation flow of the web application.
    """
    name: str = Field(description="Scenario name (e.g., '기본 계산 테스트')")
    description: Optional[str] = Field(default=None)

    # All input values for this scenario
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of field_id/cell → input value"
    )

    # All expected outputs for this scenario
    expected_outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of field_id/cell → expected output value"
    )

    # Tags for filtering
    tags: list[str] = Field(
        default_factory=list,
        description="Tags like ['smoke', 'edge_case', 'regression']"
    )


class StaticTestSuite(BaseModel):
    """
    Complete test suite automatically generated from Excel analysis.

    Contains:
    - Formula test cases for each Excel formula
    - Input/output mappings for web form testing
    - Test scenarios covering various input combinations
    """
    excel_file: str = Field(description="Source Excel filename")
    generated_at: str = Field(description="ISO timestamp of generation")

    # Individual formula tests
    formula_tests: list[FormulaTestCase] = Field(
        default_factory=list,
        description="Test cases for each formula"
    )

    # Input/output field mappings
    field_mappings: list[InputOutputMapping] = Field(
        default_factory=list,
        description="Mappings between Excel cells and WebApp fields"
    )

    # Complete test scenarios
    scenarios: list[TestScenario] = Field(
        default_factory=list,
        description="Full test scenarios with multiple inputs/outputs"
    )

    # Summary
    total_formulas: int = Field(default=0)
    total_inputs: int = Field(default=0)
    total_outputs: int = Field(default=0)

    def get_smoke_tests(self) -> list[FormulaTestCase]:
        """Get basic smoke tests (first few formulas)."""
        return self.formula_tests[:5]

    def get_all_tests(self) -> list[FormulaTestCase]:
        """Get all formula tests."""
        return self.formula_tests

    def generate_playwright_script(self) -> str:
        """Generate Playwright E2E test script."""
        script_lines = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"// Auto-generated tests for: {self.excel_file}",
            "",
        ]

        for i, scenario in enumerate(self.scenarios):
            script_lines.append(f"test('{scenario.name}', async ({{ page }}) => {{")
            script_lines.append("    await page.goto('/');")
            script_lines.append("")

            # Fill inputs
            for field_id, value in scenario.inputs.items():
                if isinstance(value, (int, float)):
                    script_lines.append(f"    await page.fill('#{field_id}', '{value}');")
                elif isinstance(value, str):
                    script_lines.append(f"    await page.fill('#{field_id}', '{value}');")

            script_lines.append("")
            script_lines.append("    // Trigger calculation")
            script_lines.append("    await page.click('button:has-text(\"계산\")');")
            script_lines.append("")

            # Check outputs
            for field_id, expected in scenario.expected_outputs.items():
                script_lines.append(f"    await expect(page.locator('#{field_id}')).toHaveValue('{expected}');")

            script_lines.append("});")
            script_lines.append("")

        return "\n".join(script_lines)


class TestExecutionResult(BaseModel):
    """Result of executing a single test case."""
    test_name: str
    passed: bool
    expected: Any
    actual: Any
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class StaticTestResult(BaseModel):
    """Result of running the complete static test suite."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float

    results: list[TestExecutionResult] = Field(default_factory=list)

    # Detailed failure info
    failures: list[str] = Field(
        default_factory=list,
        description="Detailed failure messages"
    )

    def is_passing(self, min_rate: float = 0.8) -> bool:
        """Check if test suite passes minimum threshold."""
        return self.pass_rate >= min_rate
