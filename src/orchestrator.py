"""Orchestrator - Coordinates the Excel to WebApp conversion pipeline.

Implements LLM-as-a-Judge pattern for iterative improvement:
1. Generator Agent produces code
2. Tester Agent evaluates and provides feedback
3. Loop continues until pass or max iterations reached
"""

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
    TestEvaluation,
    StaticTestSuite,
    StaticTestResult,
)
from src.tools import (
    extract_test_cases,
    run_static_tests,
)
from src.agents import (
    create_analyzer_agent,
    create_analyze_prompt,
    create_planner_agent,
    create_plan_prompt,
    create_generator_agent,
    create_generation_prompt,
    create_tester_agent,
    create_test_prompt,
    create_test_generator_agent,
    create_test_generation_prompt,
    convert_to_static_test_suite,
    GeneratedTestSuite,
)
from src.tracing import (
    ConversationCaptureHooks,
    ConversationTrace,
    StreamingMonitorHooks,
    Colors,
)


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

    Pipeline (LLM-as-a-Judge + Static Tests):
    1. Analyzer Agent: Extract structure from Excel file
    2. Test Case Generator: Extract deterministic test cases from Excel
    3. Planner Agent: Design web app based on analysis
    4. Generator Agent: Produce HTML/CSS/JS code
    5. Static Tests: Run deterministic formula tests (Node.js)
    6. Tester Agent: Evaluate code and provide feedback (LLM-as-a-Judge)
    7. Loop: If tests fail, feed feedback to Generator and retry (max 3 iterations)
    """

    def __init__(
        self,
        max_iterations: int = 3,
        min_pass_rate: float = 0.8,
        progress_callback: Optional[ProgressCallback] = None,
        verbose: bool = False,
        run_static_tests: bool = True,
    ):
        """
        Initialize the orchestrator.

        Args:
            max_iterations: Maximum generation iterations for improvement
            min_pass_rate: Minimum test pass rate to accept (0.0 to 1.0)
            progress_callback: Optional callback for progress updates
            verbose: Whether to print detailed monitoring output
            run_static_tests: Whether to run deterministic static tests
        """
        self.max_iterations = max_iterations
        self.min_pass_rate = min_pass_rate
        self.progress_callback = progress_callback
        self.verbose = verbose
        self.run_static_tests_flag = run_static_tests

        # Create all agents (all use OpenAI Agents SDK)
        self.analyzer = create_analyzer_agent()
        self.planner = create_planner_agent()
        self.generator = create_generator_agent()
        self.tester = create_tester_agent()  # LLM-as-a-Judge
        self.test_generator = create_test_generator_agent()  # Intelligent test generation

        # Static test suite (generated from Excel)
        self.static_test_suite: Optional[StaticTestSuite] = None

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

                # Stage 1.5: Generate intelligent test cases using Test Generator Agent
                if self.run_static_tests_flag:
                    self._report_progress("test_gen", "테스트 케이스 생성 중...", 0.15)
                    try:
                        # First, extract basic test cases from Excel (fast, deterministic)
                        basic_suite = extract_test_cases(excel_path, analysis)

                        if self.verbose:
                            print(f"\n{Colors.OUTPUT}📋 Basic extraction: {len(basic_suite.formula_tests)} test cases{Colors.RESET}")

                        # Then, use Test Generator Agent for intelligent test generation
                        self._report_progress("test_gen", "AI 테스트 생성 중...", 0.18)
                        agent_suite = await self._generate_tests_with_agent(analysis, hooks)

                        if agent_suite and agent_suite.formula_tests:
                            # Merge: basic (from Excel values) + agent (intelligent cases)
                            combined_tests = basic_suite.formula_tests + agent_suite.formula_tests
                            basic_suite.formula_tests = combined_tests
                            basic_suite.scenarios.extend(agent_suite.scenarios)

                            if self.verbose:
                                print(f"{Colors.OUTPUT}🤖 Agent generated: {len(agent_suite.formula_tests)} additional tests{Colors.RESET}")
                                for tc in agent_suite.formula_tests[:3]:
                                    print(f"   - {tc.description[:50]}...")

                        self.static_test_suite = basic_suite

                        if self.verbose:
                            print(f"{Colors.OUTPUT}📊 Total test cases: {len(self.static_test_suite.formula_tests)}{Colors.RESET}")

                    except Exception as e:
                        if self.verbose:
                            print(f"{Colors.ERROR}⚠️ Test case generation failed: {e}{Colors.RESET}")
                        self.static_test_suite = None

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

    async def _generate_tests_with_agent(
        self,
        analysis: ExcelAnalysis,
        hooks: ConversationCaptureHooks,
    ) -> Optional[StaticTestSuite]:
        """
        Use Test Generator Agent to create intelligent test cases.

        The agent analyzes formulas and generates:
        - Boundary value tests (0, negative, large numbers)
        - Error handling tests
        - Business scenario tests

        Args:
            analysis: Excel analysis result
            hooks: Conversation hooks for tracing

        Returns:
            StaticTestSuite with agent-generated tests, or None if failed
        """
        try:
            prompt = create_test_generation_prompt(analysis, max_formulas=15)

            result = await Runner.run(
                self.test_generator,
                prompt,
                hooks=hooks,
            )

            if result.final_output:
                if isinstance(result.final_output, GeneratedTestSuite):
                    return convert_to_static_test_suite(
                        result.final_output,
                        analysis.filename,
                    )
                elif isinstance(result.final_output, dict):
                    generated = GeneratedTestSuite(**result.final_output)
                    return convert_to_static_test_suite(
                        generated,
                        analysis.filename,
                    )

            return None

        except Exception as e:
            if self.verbose:
                print(f"{Colors.ERROR}Test Generator Agent error: {e}{Colors.RESET}")
            return None

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
        Generate web app with LLM-as-a-Judge test-driven iterations.

        Pattern:
        1. Generator produces code
        2. Tester evaluates and provides structured feedback
        3. If not passed, feedback is appended to input for next iteration
        4. Loop continues until pass or max iterations

        Returns:
            Tuple of (webapp, iterations_used, final_pass_rate)
        """
        webapp = None
        pass_rate = 0.0
        evaluation: Optional[TestEvaluation] = None

        # Build input items list for conversation continuity
        input_items = []

        # Extract formulas for testing
        formulas = []
        for sheet in analysis.sheets:
            for formula in sheet.formulas[:20]:  # Limit to 20 formulas
                formulas.append({
                    "cell": formula.cell,
                    "formula": formula.formula,
                })

        for iteration in range(1, self.max_iterations + 1):
            progress = 0.5 + (0.4 * iteration / self.max_iterations)
            self._report_progress(
                "generate",
                f"코드 생성 중... (시도 {iteration}/{self.max_iterations})",
                progress,
            )

            if self.verbose:
                print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
                print(f"{Colors.BOLD}🔄 Iteration {iteration}/{self.max_iterations}{Colors.RESET}")
                print(f"{'='*60}\n")

            # Step 1: Generate code
            webapp = await self._generate(
                plan, analysis, iteration, hooks,
                previous_feedback=evaluation.feedback if evaluation else None,
                suggested_fixes=evaluation.suggested_fixes if evaluation else None,
            )

            if webapp is None:
                if self.verbose:
                    print(f"{Colors.ERROR}❌ Generation failed{Colors.RESET}")
                continue

            if self.verbose:
                print(f"{Colors.OUTPUT}✅ Code generated ({len(webapp.html)} chars HTML){Colors.RESET}")

            # Step 2a: Run Static Tests (deterministic)
            static_result: Optional[StaticTestResult] = None
            if self.run_static_tests_flag and self.static_test_suite:
                self._report_progress(
                    "static_test",
                    f"정적 테스트 실행 중... (시도 {iteration}/{self.max_iterations})",
                    progress + 0.03,
                )

                try:
                    static_result = await run_static_tests(
                        self.static_test_suite,
                        webapp.html,
                        webapp.css,
                        webapp.js or "",
                    )

                    if self.verbose:
                        color = Colors.OUTPUT if static_result.pass_rate >= 0.8 else Colors.ERROR
                        print(f"\n{color}🧪 Static Tests: {static_result.passed}/{static_result.total_tests} passed ({static_result.pass_rate:.1%}){Colors.RESET}")
                        for failure in static_result.failures[:3]:
                            print(f"   ❌ {failure[:80]}...")

                except Exception as e:
                    if self.verbose:
                        print(f"{Colors.ERROR}⚠️ Static test execution failed: {e}{Colors.RESET}")

            # Step 2b: Evaluate with Tester Agent (LLM-as-a-Judge)
            self._report_progress(
                "test",
                f"코드 평가 중... (시도 {iteration}/{self.max_iterations})",
                progress + 0.05,
            )

            evaluation = await self._evaluate_with_tester(
                webapp, formulas, iteration, hooks
            )

            if evaluation is None:
                # Fallback to static tests if tester fails
                if self.verbose:
                    print(f"{Colors.ERROR}⚠️ Tester agent failed, using static tests{Colors.RESET}")
                test_results = await self._run_tests(webapp, analysis)
                webapp.test_results = test_results
                pass_rate = test_results.pass_rate
            else:
                # Convert evaluation to test results
                pass_rate = evaluation.pass_rate
                webapp.test_results = self._evaluation_to_test_suite(evaluation)

            # Combine static test results with LLM evaluation
            # Static tests are weighted more heavily as they're deterministic
            if static_result and static_result.total_tests > 0:
                # Weight: 60% static, 40% LLM evaluation
                combined_pass_rate = (static_result.pass_rate * 0.6) + (pass_rate * 0.4)
                pass_rate = combined_pass_rate

                if self.verbose:
                    print(f"   📊 Combined pass rate: {pass_rate:.1%} (static: {static_result.pass_rate:.1%}, LLM: {evaluation.pass_rate if evaluation else 0:.1%})")

                if self.verbose:
                    score_color = (
                        Colors.OUTPUT if evaluation.score == "pass"
                        else Colors.THINKING if evaluation.score == "needs_improvement"
                        else Colors.ERROR
                    )
                    print(f"\n{score_color}📊 Evaluation: {evaluation.score.upper()}{Colors.RESET}")
                    print(f"   Pass rate: {pass_rate:.1%}")
                    if evaluation.issues:
                        print(f"   Issues: {len(evaluation.issues)}")
                        for issue in evaluation.issues[:3]:
                            print(f"   - {issue[:80]}...")

            # Step 3: Check if good enough
            if evaluation and evaluation.score == "pass":
                if self.verbose:
                    print(f"\n{Colors.OUTPUT}🎉 Tests passed!{Colors.RESET}")
                break

            if pass_rate >= self.min_pass_rate:
                if self.verbose:
                    print(f"\n{Colors.OUTPUT}✅ Pass rate {pass_rate:.1%} >= {self.min_pass_rate:.1%}{Colors.RESET}")
                break

            # Step 4: If not last iteration, prepare feedback for next round
            if iteration < self.max_iterations:
                feedback_parts = []

                # Add static test failures to feedback
                if static_result and static_result.failures:
                    feedback_parts.append("Static Test Failures:")
                    for failure in static_result.failures[:5]:
                        feedback_parts.append(f"  - {failure}")

                # Add LLM evaluation feedback
                if evaluation:
                    webapp.feedback_applied.append(
                        f"Iteration {iteration}: {evaluation.score} - {len(evaluation.issues)} issues"
                    )
                    feedback_parts.append(f"\nLLM Evaluation: {evaluation.feedback}")

                if self.verbose and feedback_parts:
                    print(f"\n{Colors.THINKING}📝 Feedback for next iteration:{Colors.RESET}")
                    for part in feedback_parts[:5]:
                        print(f"   {part[:100]}...")

        return webapp, iteration, pass_rate

    async def _evaluate_with_tester(
        self,
        webapp: GeneratedWebApp,
        formulas: list[dict],
        iteration: int,
        hooks: ConversationCaptureHooks,
    ) -> Optional[TestEvaluation]:
        """
        Evaluate generated code using the Tester Agent (LLM-as-a-Judge).

        Args:
            webapp: Generated web application
            formulas: List of Excel formulas to verify
            iteration: Current iteration number
            hooks: Conversation hooks for tracing

        Returns:
            TestEvaluation with structured feedback, or None if failed
        """
        try:
            prompt = create_test_prompt(
                html=webapp.html,
                css=webapp.css,
                js=webapp.js,
                formulas=formulas,
                iteration=iteration,
            )

            result = await Runner.run(
                self.tester,
                prompt,
                hooks=hooks,
            )

            if result.final_output:
                if isinstance(result.final_output, TestEvaluation):
                    return result.final_output
                elif isinstance(result.final_output, dict):
                    return TestEvaluation(**result.final_output)

            return None

        except Exception as e:
            if self.verbose:
                print(f"{Colors.ERROR}Tester error: {e}{Colors.RESET}")
            return None

    def _evaluation_to_test_suite(self, evaluation: TestEvaluation) -> TestSuite:
        """Convert TestEvaluation to TestSuite for compatibility."""
        results = []

        # Add passed tests
        for test_name in evaluation.passed_tests:
            results.append(TestResult(
                test_name=test_name,
                test_type="evaluation",
                status=TestStatus.PASSED,
                message="Passed",
            ))

        # Add failed tests
        for test_name in evaluation.failed_tests:
            # Find related issue
            related_issue = next(
                (issue for issue in evaluation.issues if test_name.lower() in issue.lower()),
                None
            )
            results.append(TestResult(
                test_name=test_name,
                test_type="evaluation",
                status=TestStatus.FAILED,
                message=related_issue or "Failed",
            ))

        total = len(results)
        passed = len(evaluation.passed_tests)
        failed = len(evaluation.failed_tests)

        return TestSuite(
            total=total,
            passed=passed,
            failed=failed,
            skipped=0,
            pass_rate=evaluation.pass_rate,
            results=results,
        )

    async def _generate(
        self,
        plan: WebAppPlan,
        analysis: ExcelAnalysis,
        iteration: int,
        hooks: ConversationCaptureHooks,
        previous_feedback: Optional[str] = None,
        suggested_fixes: Optional[list[str]] = None,
    ) -> Optional[GeneratedWebApp]:
        """
        Run the Generator agent to produce code.

        Args:
            plan: Web app plan
            analysis: Excel analysis
            iteration: Current iteration number
            hooks: Conversation hooks
            previous_feedback: Feedback from previous iteration's evaluation
            suggested_fixes: Specific fixes suggested by tester

        Returns:
            GeneratedWebApp or None if failed
        """
        try:
            plan_dict = plan.model_dump()
            analysis_dict = analysis.model_dump()
            prompt = create_generation_prompt(plan_dict, analysis_dict)

            # Add iteration-specific instructions with feedback
            if iteration > 1:
                prompt += f"\n\n## Iteration {iteration} - Improvement Required\n\n"

                if previous_feedback:
                    prompt += f"### Previous Evaluation Feedback\n{previous_feedback}\n\n"

                if suggested_fixes:
                    prompt += "### Specific Fixes to Apply\n"
                    for i, fix in enumerate(suggested_fixes, 1):
                        prompt += f"{i}. {fix}\n"
                    prompt += "\n"

                prompt += """Please address ALL the issues mentioned above.
Focus on:
1. Fixing any syntax errors first
2. Implementing missing functionality
3. Ensuring all validations pass
4. Maintaining Korean UI labels
"""

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
            if self.verbose:
                print(f"{Colors.ERROR}Generation error: {e}{Colors.RESET}")
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
    verbose: bool = False,
    max_iterations: int = 3,
    run_static_tests: bool = True,
) -> ConversionResult:
    """
    Convenience function to convert an Excel file to a web app.

    Uses LLM-as-a-Judge pattern + Static Tests for iterative improvement:
    1. Generator produces code
    2. Static tests verify formula accuracy (deterministic)
    3. Tester evaluates code quality (LLM-as-a-Judge)
    4. Loop until pass or max iterations

    Args:
        excel_path: Path to the Excel file
        progress_callback: Optional callback for progress updates
        verbose: Whether to print detailed monitoring output
        max_iterations: Maximum iterations for improvement (default: 3)
        run_static_tests: Whether to run deterministic formula tests

    Returns:
        ConversionResult with the generated web app
    """
    orchestrator = ExcelToWebAppOrchestrator(
        progress_callback=progress_callback,
        verbose=verbose,
        max_iterations=max_iterations,
        run_static_tests=run_static_tests,
    )
    return await orchestrator.convert(excel_path)


def convert_excel_to_webapp_sync(
    excel_path: str,
    progress_callback: Optional[ProgressCallback] = None,
    verbose: bool = False,
    max_iterations: int = 3,
    run_static_tests: bool = True,
) -> ConversionResult:
    """
    Synchronous wrapper for convert_excel_to_webapp.

    Args:
        excel_path: Path to the Excel file
        progress_callback: Optional callback for progress updates
        verbose: Whether to print detailed monitoring output
        max_iterations: Maximum iterations for improvement (default: 3)
        run_static_tests: Whether to run deterministic formula tests

    Returns:
        ConversionResult with the generated web app
    """
    return asyncio.run(convert_excel_to_webapp(
        excel_path, progress_callback, verbose, max_iterations, run_static_tests
    ))
