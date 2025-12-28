"""Static test runner - Executes deterministic tests on generated JavaScript code.

Approaches:
1. Node.js execution with JSDOM for DOM simulation
2. Playwright browser execution for E2E testing
3. Python-based formula evaluation for quick validation
"""

import asyncio
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.models.test_case import (
    StaticTestSuite,
    StaticTestResult,
    TestExecutionResult,
    FormulaTestCase,
)


class StaticTestRunner:
    """
    Runs static tests against generated JavaScript code.

    Test Levels:
    1. Syntax validation (JS parsing)
    2. Formula execution (Node.js with JSDOM)
    3. E2E validation (Playwright)
    """

    def __init__(self, node_path: str = "node", timeout: int = 30):
        """
        Initialize the test runner.

        Args:
            node_path: Path to Node.js executable
            timeout: Test execution timeout in seconds
        """
        self.node_path = node_path
        self.timeout = timeout

    async def run_tests(
        self,
        test_suite: StaticTestSuite,
        html: str,
        css: str,
        js: str,
    ) -> StaticTestResult:
        """
        Run all static tests against the generated code.

        Args:
            test_suite: The test suite to execute
            html: Generated HTML code
            css: Generated CSS code
            js: Generated JavaScript code

        Returns:
            StaticTestResult with detailed results
        """
        results: list[TestExecutionResult] = []
        failures: list[str] = []

        # Run syntax validation first
        syntax_result = await self._validate_syntax(js)
        results.append(syntax_result)
        if not syntax_result.passed:
            failures.append(f"Syntax error: {syntax_result.error_message}")

        # Run formula tests
        for test_case in test_suite.formula_tests:
            result = await self._run_formula_test(test_case, html, js)
            results.append(result)
            if not result.passed:
                failures.append(
                    f"{test_case.formula_cell}: Expected {test_case.expected_output}, "
                    f"got {result.actual}"
                )

        # Calculate summary
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        total = len(results)

        return StaticTestResult(
            suite_name=test_suite.excel_file,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=0,
            pass_rate=passed / total if total > 0 else 0.0,
            results=results,
            failures=failures,
        )

    async def _validate_syntax(self, js_code: str) -> TestExecutionResult:
        """Validate JavaScript syntax using Node.js."""
        start_time = datetime.now()

        # Create a temp file with the JS code
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.js', delete=False
        ) as f:
            f.write(js_code)
            temp_path = f.name

        try:
            # Use Node.js to check syntax
            result = subprocess.run(
                [self.node_path, '--check', temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            if result.returncode == 0:
                return TestExecutionResult(
                    test_name="JavaScript Syntax",
                    passed=True,
                    expected="Valid syntax",
                    actual="Valid syntax",
                    execution_time_ms=elapsed,
                )
            else:
                return TestExecutionResult(
                    test_name="JavaScript Syntax",
                    passed=False,
                    expected="Valid syntax",
                    actual="Syntax error",
                    error_message=result.stderr,
                    execution_time_ms=elapsed,
                )

        except subprocess.TimeoutExpired:
            return TestExecutionResult(
                test_name="JavaScript Syntax",
                passed=False,
                expected="Valid syntax",
                actual="Timeout",
                error_message="Syntax check timed out",
            )
        except FileNotFoundError:
            return TestExecutionResult(
                test_name="JavaScript Syntax",
                passed=False,
                expected="Valid syntax",
                actual="Node.js not found",
                error_message=f"Node.js not found at {self.node_path}",
            )
        finally:
            os.unlink(temp_path)

    async def _run_formula_test(
        self,
        test_case: FormulaTestCase,
        html: str,
        js: str,
    ) -> TestExecutionResult:
        """
        Run a single formula test using Node.js with JSDOM.

        This creates a minimal test harness that:
        1. Sets up a DOM with the generated HTML
        2. Executes the JS code
        3. Sets input values
        4. Triggers calculation
        5. Reads output values
        """
        start_time = datetime.now()

        # Create test script
        test_script = self._generate_test_harness(test_case, html, js)

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.js', delete=False
        ) as f:
            f.write(test_script)
            temp_path = f.name

        try:
            result = subprocess.run(
                [self.node_path, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            # Parse output
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode == 0:
                # Try to parse the actual result from stdout
                try:
                    output = json.loads(stdout)
                    actual = output.get('result')
                    passed = output.get('passed', False)
                except json.JSONDecodeError:
                    actual = stdout
                    passed = False

                return TestExecutionResult(
                    test_name=f"{test_case.formula_cell}: {test_case.formula}",
                    passed=passed,
                    expected=test_case.expected_output,
                    actual=actual,
                    execution_time_ms=elapsed,
                )
            else:
                return TestExecutionResult(
                    test_name=f"{test_case.formula_cell}: {test_case.formula}",
                    passed=False,
                    expected=test_case.expected_output,
                    actual=None,
                    error_message=stderr or "Test execution failed",
                    execution_time_ms=elapsed,
                )

        except subprocess.TimeoutExpired:
            return TestExecutionResult(
                test_name=f"{test_case.formula_cell}: {test_case.formula}",
                passed=False,
                expected=test_case.expected_output,
                actual=None,
                error_message="Test timed out",
            )
        except Exception as e:
            return TestExecutionResult(
                test_name=f"{test_case.formula_cell}: {test_case.formula}",
                passed=False,
                expected=test_case.expected_output,
                actual=None,
                error_message=str(e),
            )
        finally:
            os.unlink(temp_path)

    def _generate_test_harness(
        self,
        test_case: FormulaTestCase,
        html: str,
        js: str,
    ) -> str:
        """Generate a Node.js test harness for a formula test."""

        # Escape strings for embedding
        html_escaped = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        js_escaped = js.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

        input_json = json.dumps(test_case.input_values)
        expected = test_case.expected_output
        tolerance = test_case.tolerance

        return f"""
const {{ JSDOM }} = require('jsdom');

// Create DOM with generated HTML
const html = `{html_escaped}`;
const dom = new JSDOM(html, {{
    runScripts: 'dangerously',
    resources: 'usable'
}});

const {{ window }} = dom;
const {{ document }} = window;

// Wait for DOM to be ready
setTimeout(() => {{
    try {{
        // Inject generated JavaScript
        const script = document.createElement('script');
        script.textContent = `{js_escaped}`;
        document.body.appendChild(script);

        // Set input values
        const inputs = {input_json};
        for (const [cell, value] of Object.entries(inputs)) {{
            // Try various selectors to find input
            const selectors = [
                `[data-cell="${{cell}}"]`,
                `#input_${{cell.toLowerCase()}}`,
                `input[name="${{cell.toLowerCase()}}"]`,
                `#${{cell.toLowerCase()}}`,
            ];

            for (const selector of selectors) {{
                const el = document.querySelector(selector);
                if (el) {{
                    el.value = value;
                    // Trigger input event
                    el.dispatchEvent(new window.Event('input', {{ bubbles: true }}));
                    break;
                }}
            }}
        }}

        // Try to trigger calculation
        const calcButtons = document.querySelectorAll('button');
        for (const btn of calcButtons) {{
            if (btn.textContent.includes('계산') || btn.textContent.toLowerCase().includes('calc')) {{
                btn.click();
                break;
            }}
        }}

        // Wait a bit for Alpine.js / reactive updates
        setTimeout(() => {{
            // Try to read result
            const outputCell = '{test_case.formula_cell}';
            const selectors = [
                `[data-cell="${{outputCell}}"]`,
                `#output_${{outputCell.toLowerCase()}}`,
                `#${{outputCell.toLowerCase()}}`,
                `[id*="${{outputCell.toLowerCase()}}"]`,
            ];

            let result = null;
            for (const selector of selectors) {{
                const el = document.querySelector(selector);
                if (el) {{
                    result = el.textContent || el.value || el.innerText;
                    break;
                }}
            }}

            // Try to get from Alpine.js appData
            if (result === null && window.appData) {{
                const data = window.appData();
                if (data) {{
                    result = data[outputCell.toLowerCase()] || data[outputCell];
                }}
            }}

            // Parse numeric result
            let numericResult = null;
            if (result !== null) {{
                const cleaned = String(result).replace(/[^0-9.-]/g, '');
                numericResult = parseFloat(cleaned);
            }}

            const expected = {expected};
            const tolerance = {tolerance};
            const passed = numericResult !== null &&
                          Math.abs(numericResult - expected) <= tolerance;

            console.log(JSON.stringify({{
                passed,
                expected,
                result: numericResult,
                raw: result
            }}));

            process.exit(passed ? 0 : 1);
        }}, 100);

    }} catch (error) {{
        console.log(JSON.stringify({{
            passed: false,
            error: error.message
        }}));
        process.exit(1);
    }}
}}, 100);
"""


async def run_static_tests(
    test_suite: StaticTestSuite,
    html: str,
    css: str,
    js: str,
) -> StaticTestResult:
    """
    Convenience function to run static tests.

    Args:
        test_suite: The test suite to execute
        html: Generated HTML code
        css: Generated CSS code
        js: Generated JavaScript code

    Returns:
        StaticTestResult with all test results
    """
    runner = StaticTestRunner()
    return await runner.run_tests(test_suite, html, css, js)


def run_static_tests_sync(
    test_suite: StaticTestSuite,
    html: str,
    css: str,
    js: str,
) -> StaticTestResult:
    """Synchronous wrapper for run_static_tests."""
    return asyncio.run(run_static_tests(test_suite, html, css, js))
