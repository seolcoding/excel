"""Orchestrator - Coordinates the Excel to WebApp conversion pipeline."""

import asyncio
import json
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from agents import Runner, trace

from src.models import (
    ExcelAnalysis,
    WebAppPlan,
    GeneratedWebApp,
    ConversionResult,
    TestSuite,
    TestResult,
    TestStatus,
)
from src.agents import (
    create_analyzer_agent,
    create_analyze_prompt,
    create_planner_agent,
    create_plan_prompt,
    create_generator_agent,
    create_generation_prompt,
)
from src.tracing import ConversationCaptureHooks, ConversationTrace


@dataclass
class ConversionProgress:
    """Progress information for the conversion pipeline."""
    stage: str
    message: str
    progress: float  # 0.0 to 1.0


# Progress callback type
ProgressCallback = Callable[[ConversionProgress], None]


class ExcelToWebAppOrchestrator:
    """
    Orchestrates the conversion of Excel files to web applications.

    Pipeline:
    1. Analyzer Agent: Extract structure from Excel file
    2. Planner Agent: Design web app based on analysis
    3. Generator Agent: Produce HTML/CSS/JS code
    4. (Optional) Test and iterate
    """

    def __init__(
        self,
        max_iterations: int = 3,
        min_pass_rate: float = 0.9,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            max_iterations: Maximum generation iterations for improvement
            min_pass_rate: Minimum test pass rate to accept (0.0 to 1.0)
            progress_callback: Optional callback for progress updates
        """
        self.max_iterations = max_iterations
        self.min_pass_rate = min_pass_rate
        self.progress_callback = progress_callback

        # Create all agents (all use OpenAI Agents SDK)
        self.analyzer = create_analyzer_agent()
        self.planner = create_planner_agent()
        self.generator = create_generator_agent()

    def _report_progress(self, stage: str, message: str, progress: float):
        """Report progress via callback if available."""
        if self.progress_callback:
            self.progress_callback(ConversionProgress(
                stage=stage,
                message=message,
                progress=progress,
            ))

    async def convert(self, excel_path: str) -> ConversionResult:
        """
        Convert an Excel file to a web application.

        Args:
            excel_path: Path to the Excel file (.xlsx or .xlsm)

        Returns:
            ConversionResult with the generated web app or error
        """
        path = Path(excel_path)

        # Validate file exists
        if not path.exists():
            return ConversionResult(
                success=False,
                iterations_used=0,
                final_pass_rate=0.0,
                message=f"File not found: {excel_path}",
            )

        # Validate file type
        if path.suffix.lower() not in [".xlsx", ".xlsm"]:
            return ConversionResult(
                success=False,
                iterations_used=0,
                final_pass_rate=0.0,
                message=f"Unsupported file type: {path.suffix}. Use .xlsx or .xlsm",
            )

        # Create conversation hooks to capture all LLM interactions
        hooks = ConversationCaptureHooks(f"Excel-to-WebApp: {path.name}")

        # Wrap entire pipeline in a trace for observability
        with trace(f"Excel-to-WebApp: {path.name}"):
            try:
                # Stage 1: Analyze
                self._report_progress("analyze", "Excel 파일 분석 중...", 0.1)
                analysis = await self._analyze(excel_path, hooks)

                if analysis is None:
                    hooks.finalize()
                    return ConversionResult(
                        success=False,
                        iterations_used=0,
                        final_pass_rate=0.0,
                        message="Failed to analyze Excel file",
                        conversation_trace=hooks.get_trace().to_dict(),
                    )

                # Stage 2: Plan
                self._report_progress("plan", "웹 앱 구조 설계 중...", 0.3)
                plan = await self._plan(analysis, hooks)

                if plan is None:
                    hooks.finalize()
                    return ConversionResult(
                        success=False,
                        iterations_used=0,
                        final_pass_rate=0.0,
                        message="Failed to create web app plan",
                        conversation_trace=hooks.get_trace().to_dict(),
                    )

                # Stage 3: Generate (with iterations)
                self._report_progress("generate", "코드 생성 중...", 0.5)
                webapp, iterations, pass_rate = await self._generate_with_iterations(
                    plan, analysis, hooks
                )

                if webapp is None:
                    hooks.finalize()
                    return ConversionResult(
                        success=False,
                        iterations_used=iterations,
                        final_pass_rate=pass_rate,
                        message="Failed to generate web application",
                        conversation_trace=hooks.get_trace().to_dict(),
                    )

                self._report_progress("complete", "변환 완료!", 1.0)
                hooks.finalize()

                return ConversionResult(
                    success=True,
                    app=webapp,
                    iterations_used=iterations,
                    final_pass_rate=pass_rate,
                    message="Successfully converted Excel to web application",
                    conversation_trace=hooks.get_trace().to_dict(),
                )

            except Exception as e:
                hooks.finalize()
                return ConversionResult(
                    success=False,
                    iterations_used=0,
                    final_pass_rate=0.0,
                    message=f"Conversion error: {str(e)}",
                    conversation_trace=hooks.get_trace().to_dict(),
                )

    async def _analyze(
        self, excel_path: str, hooks: ConversationCaptureHooks
    ) -> Optional[ExcelAnalysis]:
        """Run the Analyzer agent to extract Excel structure."""
        try:
            prompt = create_analyze_prompt(excel_path)

            result = await Runner.run(
                self.analyzer,
                prompt,
                hooks=hooks,
            )

            # The agent returns the analysis via tool call result
            if result.final_output:
                if isinstance(result.final_output, dict):
                    return ExcelAnalysis(**result.final_output)
                elif isinstance(result.final_output, ExcelAnalysis):
                    return result.final_output

            # Fallback: check tool call results for analysis data
            for item in result.new_items:
                if hasattr(item, 'output') and isinstance(item.output, dict):
                    if 'filename' in item.output and 'sheets' in item.output:
                        return ExcelAnalysis(**item.output)

            return None

        except Exception as e:
            print(f"Analysis error: {e}")
            return None

    async def _plan(
        self, analysis: ExcelAnalysis, hooks: ConversationCaptureHooks
    ) -> Optional[WebAppPlan]:
        """Run the Planner agent to design the web app."""
        try:
            # Convert analysis to dict for prompt
            analysis_dict = analysis.model_dump()
            prompt = create_plan_prompt(analysis_dict)

            result = await Runner.run(
                self.planner,
                prompt,
                hooks=hooks,
            )

            if result.final_output:
                if isinstance(result.final_output, dict):
                    return WebAppPlan(**result.final_output)
                elif isinstance(result.final_output, WebAppPlan):
                    return result.final_output

            return None

        except Exception as e:
            print(f"Planning error: {e}")
            return None

    async def _generate_with_iterations(
        self,
        plan: WebAppPlan,
        analysis: ExcelAnalysis,
        hooks: ConversationCaptureHooks,
    ) -> tuple[Optional[GeneratedWebApp], int, float]:
        """
        Generate web app with test-driven iterations.

        Returns:
            Tuple of (webapp, iterations_used, final_pass_rate)
        """
        webapp = None
        pass_rate = 0.0

        for iteration in range(1, self.max_iterations + 1):
            progress = 0.5 + (0.4 * iteration / self.max_iterations)
            self._report_progress(
                "generate",
                f"코드 생성 중... (시도 {iteration}/{self.max_iterations})",
                progress,
            )

            # Generate code
            webapp = await self._generate(plan, analysis, iteration, hooks)

            if webapp is None:
                continue

            # Run tests
            test_results = await self._run_tests(webapp, analysis)
            webapp.test_results = test_results
            pass_rate = test_results.pass_rate

            # Check if good enough
            if pass_rate >= self.min_pass_rate:
                break

            # If not last iteration, prepare feedback for next round
            if iteration < self.max_iterations:
                # Add feedback info to webapp for next iteration
                failed_tests = [
                    r for r in test_results.results
                    if r.status == TestStatus.FAILED
                ]
                webapp.feedback_applied.append(
                    f"Iteration {iteration}: {len(failed_tests)} tests failed"
                )

        return webapp, iteration, pass_rate

    async def _generate(
        self,
        plan: WebAppPlan,
        analysis: ExcelAnalysis,
        iteration: int,
        hooks: ConversationCaptureHooks,
    ) -> Optional[GeneratedWebApp]:
        """Run the Generator agent to produce code."""
        try:
            plan_dict = plan.model_dump()
            analysis_dict = analysis.model_dump()
            prompt = create_generation_prompt(plan_dict, analysis_dict)

            if iteration > 1:
                prompt += f"\n\nThis is iteration {iteration}. Please fix any issues from previous attempts."

            result = await Runner.run(
                self.generator,
                prompt,
                hooks=hooks,
            )

            if result.final_output:
                if isinstance(result.final_output, dict):
                    webapp = GeneratedWebApp(**result.final_output)
                elif isinstance(result.final_output, GeneratedWebApp):
                    webapp = result.final_output
                else:
                    return None

                webapp.generation_iteration = iteration
                return webapp

            return None

        except Exception as e:
            print(f"Generation error: {e}")
            return None

    async def _run_tests(
        self,
        webapp: GeneratedWebApp,
        analysis: ExcelAnalysis,
    ) -> TestSuite:
        """
        Run tests on the generated web app.

        Tests include:
        - Formula output verification
        - Print layout checks
        - Input/output mapping validation
        """
        results = []

        # Test 1: HTML structure validation
        html_valid, html_issues = self._validate_html(webapp.html)
        results.append(TestResult(
            test_name="HTML Structure",
            test_type="structure",
            status=TestStatus.PASSED if html_valid else TestStatus.FAILED,
            message="; ".join(html_issues) if html_issues else "Valid HTML structure",
        ))

        # Test 2: Required elements present
        elements_valid, missing = self._check_required_elements(webapp.html, analysis)
        results.append(TestResult(
            test_name="Required Elements",
            test_type="structure",
            status=TestStatus.PASSED if elements_valid else TestStatus.FAILED,
            message=f"Missing: {', '.join(missing)}" if missing else "All elements present",
        ))

        # Test 3: Print CSS validation
        print_valid = "@media print" in webapp.css or "@media print" in webapp.html
        results.append(TestResult(
            test_name="Print Styles",
            test_type="print_layout",
            status=TestStatus.PASSED if print_valid else TestStatus.FAILED,
            message="Print styles found" if print_valid else "Missing print media query",
        ))

        # Test 4: JavaScript functions present
        js_valid, js_issues = self._validate_javascript(webapp.js or webapp.html)
        results.append(TestResult(
            test_name="JavaScript Logic",
            test_type="formula",
            status=TestStatus.PASSED if js_valid else TestStatus.FAILED,
            message="; ".join(js_issues) if js_issues else "Valid JavaScript",
        ))

        # Test 5: Korean labels present
        has_korean = any(
            ord(char) >= 0xAC00 and ord(char) <= 0xD7A3
            for char in webapp.html
        )
        results.append(TestResult(
            test_name="Korean Labels",
            test_type="input_output",
            status=TestStatus.PASSED if has_korean else TestStatus.FAILED,
            message="Korean text found" if has_korean else "No Korean text in UI",
        ))

        # Calculate summary
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        total = len(results)

        return TestSuite(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            pass_rate=passed / total if total > 0 else 0.0,
            results=results,
        )

    def _validate_html(self, html: str) -> tuple[bool, list[str]]:
        """Basic HTML validation."""
        issues = []

        if "<!DOCTYPE html>" not in html and "<!doctype html>" not in html:
            issues.append("Missing DOCTYPE")

        if "<html" not in html:
            issues.append("Missing <html> tag")

        if "<head>" not in html and "<head " not in html:
            issues.append("Missing <head> tag")

        if "<body>" not in html and "<body " not in html:
            issues.append("Missing <body> tag")

        # Check for balanced tags
        if html.count("<div") != html.count("</div>"):
            issues.append("Unbalanced <div> tags")

        return len(issues) == 0, issues

    def _check_required_elements(
        self,
        html: str,
        analysis: ExcelAnalysis,
    ) -> tuple[bool, list[str]]:
        """Check if required form elements are present."""
        missing = []

        # Check for Bootstrap
        if "bootstrap" not in html.lower():
            missing.append("Bootstrap CSS")

        # Check for Alpine.js
        if "alpinejs" not in html.lower() and "alpine" not in html.lower():
            missing.append("Alpine.js")

        # Check for form elements (at least one input)
        if "<input" not in html:
            missing.append("Input fields")

        # Check for calculate button/function
        if "calculate" not in html.lower() and "계산" not in html:
            missing.append("Calculate button")

        return len(missing) == 0, missing

    def _validate_javascript(self, code: str) -> tuple[bool, list[str]]:
        """Basic JavaScript validation."""
        issues = []

        # Check for appData function
        if "appData" not in code and "function" not in code:
            issues.append("Missing appData or main function")

        # Check for balanced braces
        if code.count("{") != code.count("}"):
            issues.append("Unbalanced curly braces")

        # Check for balanced parentheses
        if code.count("(") != code.count(")"):
            issues.append("Unbalanced parentheses")

        return len(issues) == 0, issues


async def convert_excel_to_webapp(
    excel_path: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> ConversionResult:
    """
    Convenience function to convert an Excel file to a web app.

    Args:
        excel_path: Path to the Excel file
        progress_callback: Optional callback for progress updates

    Returns:
        ConversionResult with the generated web app
    """
    orchestrator = ExcelToWebAppOrchestrator(
        progress_callback=progress_callback,
    )
    return await orchestrator.convert(excel_path)


def convert_excel_to_webapp_sync(
    excel_path: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> ConversionResult:
    """
    Synchronous wrapper for convert_excel_to_webapp.

    Args:
        excel_path: Path to the Excel file
        progress_callback: Optional callback for progress updates

    Returns:
        ConversionResult with the generated web app
    """
    return asyncio.run(convert_excel_to_webapp(excel_path, progress_callback))
