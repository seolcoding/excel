"""Unit tests for Tester Agent (LLM-as-a-Judge pattern).

Based on OpenAI Agents SDK testing patterns.
Reference: refs/openai-agents-python/tests/test_agent_runner.py
"""

from __future__ import annotations

import json
import pytest

from agents import Agent, Runner, AgentOutputSchema

from src.agents.tester_agent import (
    create_tester_agent,
    create_test_prompt,
    TESTER_INSTRUCTIONS,
    TestCase,
    TestEvaluation,
    validate_html_structure,
    validate_javascript_syntax,
    validate_print_styles,
    validate_korean_ui,
    check_formula_implementation,
)

from tests.fake_model import FakeModel
from tests.helpers import get_json_message, get_test_evaluation_output


class TestTesterAgentCreation:
    """Tests for Tester Agent creation."""

    def test_create_tester_agent_returns_agent(self):
        """Test that create_tester_agent returns an Agent instance."""
        agent = create_tester_agent()
        assert agent is not None
        assert agent.name == "Code Tester"

    def test_tester_agent_uses_mini_model(self):
        """Test that tester agent uses gpt-5-mini model (cost-optimized)."""
        agent = create_tester_agent()
        assert agent.model == "gpt-5-mini"

    def test_tester_agent_has_validation_tools(self):
        """Test that tester agent has validation tools."""
        agent = create_tester_agent()
        assert len(agent.tools) == 5  # 5 validation tools

    def test_tester_agent_output_type_is_test_evaluation(self):
        """Test that tester agent has TestEvaluation output type."""
        agent = create_tester_agent()
        assert agent.output_type is not None


class TestTesterAgentInstructions:
    """Tests for Tester Agent instructions."""

    def test_instructions_mention_llm_as_judge(self):
        """Test that instructions describe evaluation process."""
        assert "evaluate" in TESTER_INSTRUCTIONS.lower()

    def test_instructions_mention_scoring_criteria(self):
        """Test that instructions mention scoring criteria."""
        assert "PASS" in TESTER_INSTRUCTIONS
        assert "NEEDS IMPROVEMENT" in TESTER_INSTRUCTIONS
        assert "FAIL" in TESTER_INSTRUCTIONS

    def test_instructions_mention_feedback_requirements(self):
        """Test that instructions mention feedback requirements."""
        assert "feedback" in TESTER_INSTRUCTIONS.lower()
        assert "SPECIFIC" in TESTER_INSTRUCTIONS
        assert "ACTIONABLE" in TESTER_INSTRUCTIONS

    def test_instructions_mention_validation_tools(self):
        """Test that instructions mention validation tools."""
        assert "validate_html_structure" in TESTER_INSTRUCTIONS
        assert "validate_javascript_syntax" in TESTER_INSTRUCTIONS


class TestCreateTestPrompt:
    """Tests for create_test_prompt function."""

    def test_prompt_includes_html(self):
        """Test that prompt includes HTML code."""
        prompt = create_test_prompt(
            html="<html></html>",
            css="body {}",
            js="function test() {}",
            formulas=[],
            iteration=1,
        )
        assert "<html></html>" in prompt

    def test_prompt_includes_css(self):
        """Test that prompt includes CSS code."""
        prompt = create_test_prompt(
            html="<html></html>",
            css="body { color: red; }",
            js="function test() {}",
            formulas=[],
            iteration=1,
        )
        assert "body { color: red; }" in prompt

    def test_prompt_includes_js(self):
        """Test that prompt includes JavaScript code."""
        prompt = create_test_prompt(
            html="<html></html>",
            css="body {}",
            js="function calculate() { return 42; }",
            formulas=[],
            iteration=1,
        )
        assert "function calculate()" in prompt

    def test_prompt_includes_formulas(self):
        """Test that prompt includes formulas to verify."""
        prompt = create_test_prompt(
            html="<html></html>",
            css="body {}",
            js="function test() {}",
            formulas=[
                {"cell": "B10", "formula": "=B3*0.1"},
                {"cell": "B11", "formula": "=SUM(B3:B5)"},
            ],
            iteration=1,
        )
        assert "B10" in prompt
        assert "=B3*0.1" in prompt

    def test_prompt_includes_iteration_number(self):
        """Test that prompt includes iteration number."""
        prompt = create_test_prompt(
            html="<html></html>",
            css="body {}",
            js="function test() {}",
            formulas=[],
            iteration=3,
        )
        assert "Iteration 3" in prompt

    def test_prompt_is_lenient_after_3_iterations(self):
        """Test that prompt is lenient after 3+ iterations."""
        prompt = create_test_prompt(
            html="<html></html>",
            css="body {}",
            js="function test() {}",
            formulas=[],
            iteration=3,
        )
        assert "lenient" in prompt.lower()


class TestTesterAgentWithFakeModel:
    """Tests for Tester Agent using FakeModel (SDK pattern)."""

    @pytest.mark.asyncio
    async def test_tester_agent_returns_test_evaluation(self):
        """Test that tester agent returns TestEvaluation with FakeModel."""
        model = FakeModel()
        eval_output = get_test_evaluation_output(passed=True)
        model.set_next_output([get_json_message(eval_output)])

        agent = Agent(
            name="Code Tester",
            instructions="Test instructions",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(TestEvaluation, strict_json_schema=False),
        )

        result = await Runner.run(agent, input="Evaluate this code")

        assert result.final_output is not None
        if isinstance(result.final_output, TestEvaluation):
            assert result.final_output.score == "pass"
        elif isinstance(result.final_output, dict):
            assert result.final_output.get("score") == "pass"

    @pytest.mark.asyncio
    async def test_tester_agent_returns_failing_evaluation(self):
        """Test that tester agent can return failing evaluation."""
        model = FakeModel()
        eval_output = get_test_evaluation_output(passed=False)
        model.set_next_output([get_json_message(eval_output)])

        agent = Agent(
            name="Code Tester",
            instructions="Test instructions",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(TestEvaluation, strict_json_schema=False),
        )

        result = await Runner.run(agent, input="Evaluate this code")

        assert result.final_output is not None
        if isinstance(result.final_output, TestEvaluation):
            assert result.final_output.score == "needs_improvement"
            assert len(result.final_output.failed_tests) > 0
        elif isinstance(result.final_output, dict):
            assert result.final_output.get("score") == "needs_improvement"


class TestTestEvaluationOutput:
    """Tests for TestEvaluation output structure."""

    def test_test_evaluation_pass(self, sample_test_evaluation_dict):
        """Test creating passing TestEvaluation from dict."""
        evaluation = TestEvaluation(**sample_test_evaluation_dict)
        assert evaluation.score == "pass"
        assert evaluation.pass_rate == 0.95
        assert len(evaluation.passed_tests) == 4
        assert len(evaluation.failed_tests) == 0
        assert len(evaluation.issues) == 0

    def test_test_evaluation_fail(self):
        """Test creating failing TestEvaluation."""
        eval_dict = get_test_evaluation_output(passed=False)
        evaluation = TestEvaluation(**eval_dict)
        assert evaluation.score == "needs_improvement"
        assert evaluation.pass_rate == 0.6
        assert len(evaluation.failed_tests) > 0
        assert len(evaluation.issues) > 0
        assert len(evaluation.suggested_fixes) > 0


class TestTestCaseModel:
    """Tests for TestCase model."""

    def test_test_case_formula_type(self):
        """Test creating formula test case."""
        test_case = TestCase(
            name="tax_calculation",
            description="Test tax is 10% of salary",
            input_values={"salary": 5000000},
            expected_output={"tax": 500000},
            test_type="formula",
        )
        assert test_case.test_type == "formula"
        assert test_case.input_values["salary"] == 5000000

    def test_test_case_structure_type(self):
        """Test creating structure test case."""
        test_case = TestCase(
            name="html_structure",
            description="Test HTML has proper structure",
            input_values={},
            expected_output={"valid": True},
            test_type="structure",
        )
        assert test_case.test_type == "structure"


class TestValidationTools:
    """Tests for validation tool functions.

    Uses the FunctionTool.on_invoke_tool() method with JSON input.
    """

    @pytest.mark.asyncio
    async def test_validate_html_structure_valid(self):
        """Test validating valid HTML structure."""
        valid_html = """<!DOCTYPE html>
<html lang="ko">
<head>
    <link href="https://bootstrap.min.css" rel="stylesheet">
    <script src="https://alpine.js"></script>
</head>
<body>
    <div></div>
</body>
</html>"""
        result = await validate_html_structure.on_invoke_tool(
            {}, json.dumps({"html": valid_html})
        )
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_html_structure_missing_doctype(self):
        """Test detecting missing DOCTYPE."""
        invalid_html = "<html><head></head><body></body></html>"
        result = await validate_html_structure.on_invoke_tool(
            {}, json.dumps({"html": invalid_html})
        )
        assert result["valid"] is False
        assert "DOCTYPE" in result["issues"][0]

    @pytest.mark.asyncio
    async def test_validate_javascript_syntax_valid(self):
        """Test validating valid JavaScript."""
        valid_js = """function appData() {
    return {
        salary: 0,
        get tax() { return this.salary * 0.1; }
    };
}"""
        result = await validate_javascript_syntax.on_invoke_tool(
            {}, json.dumps({"js_code": valid_js})
        )
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_javascript_syntax_unbalanced_braces(self):
        """Test detecting unbalanced braces."""
        invalid_js = "function test() { return { }"
        result = await validate_javascript_syntax.on_invoke_tool(
            {}, json.dumps({"js_code": invalid_js})
        )
        assert result["valid"] is False
        assert "Unbalanced" in result["issues"][0]

    @pytest.mark.asyncio
    async def test_validate_print_styles_valid(self):
        """Test validating valid print styles."""
        valid_css = """
@media print {
    @page { size: A4; }
    .no-print { display: none; }
}"""
        result = await validate_print_styles.on_invoke_tool(
            {}, json.dumps({"css_or_html": valid_css})
        )
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_print_styles_missing_media_query(self):
        """Test detecting missing @media print."""
        invalid_css = "body { color: black; }"
        result = await validate_print_styles.on_invoke_tool(
            {}, json.dumps({"css_or_html": invalid_css})
        )
        assert result["valid"] is False
        assert "@media print" in result["issues"][0]

    @pytest.mark.asyncio
    async def test_validate_korean_ui_valid(self):
        """Test validating Korean UI labels."""
        # Note: The validator checks for exact "Noto Sans KR" string
        korean_html = """<!DOCTYPE html>
<html>
<head>
    <!-- Noto Sans KR font for Korean typography -->
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR" rel="stylesheet">
</head>
<body>
    <button>계산</button>
    <label>입력</label>
    <div>결과</div>
</body>
</html>"""
        result = await validate_korean_ui.on_invoke_tool(
            {}, json.dumps({"html": korean_html})
        )
        assert result["valid"] is True
        assert len(result["korean_keywords_found"]) >= 2

    @pytest.mark.asyncio
    async def test_validate_korean_ui_missing_korean(self):
        """Test detecting missing Korean text."""
        english_html = """<!DOCTYPE html>
<html><body><button>Calculate</button></body></html>"""
        result = await validate_korean_ui.on_invoke_tool(
            {}, json.dumps({"html": english_html})
        )
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_check_formula_implementation_found(self):
        """Test detecting formula implementation."""
        js_code = """function appData() {
    return {
        salary: 0,
        get tax() { return this.salary * 0.1; }
    };
}"""
        formula_list = json.dumps([
            {"cell": "B10", "formula": "=B3*0.1"}
        ])
        result = await check_formula_implementation.on_invoke_tool(
            {}, json.dumps({"js_code": js_code, "formula_list": formula_list})
        )
        assert result["implementation_rate"] > 0

    @pytest.mark.asyncio
    async def test_check_formula_implementation_sum(self):
        """Test detecting SUM implementation."""
        js_code = """function calculate() {
    return values.reduce((a, b) => a + b, 0);
}"""
        formula_list = json.dumps([
            {"cell": "B20", "formula": "=SUM(B1:B10)"}
        ])
        result = await check_formula_implementation.on_invoke_tool(
            {}, json.dumps({"js_code": js_code, "formula_list": formula_list})
        )
        assert result["details"][0]["implemented"] is True

    @pytest.mark.asyncio
    async def test_check_formula_implementation_if(self):
        """Test detecting IF implementation."""
        js_code = """function calculate() {
    return amount > 1000 ? amount * 0.1 : 0;
}"""
        formula_list = json.dumps([
            {"cell": "C5", "formula": "=IF(B5>1000,B5*0.1,0)"}
        ])
        result = await check_formula_implementation.on_invoke_tool(
            {}, json.dumps({"js_code": js_code, "formula_list": formula_list})
        )
        assert result["details"][0]["implemented"] is True


class TestTesterAgentErrorHandling:
    """Tests for Tester Agent error handling."""

    @pytest.mark.asyncio
    async def test_tester_agent_handles_exception(self):
        """Test that tester agent handles model exceptions."""
        model = FakeModel()
        model.set_next_output(ValueError("Evaluation error"))

        agent = Agent(
            name="Code Tester",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        with pytest.raises(ValueError) as exc_info:
            await Runner.run(agent, input="test input")

        assert "Evaluation error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tester_agent_handles_empty_output(self):
        """Test that tester agent handles empty output."""
        model = FakeModel()
        model.set_next_output([])  # Empty output

        agent = Agent(
            name="Code Tester",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        result = await Runner.run(agent, input="test input")

        # Empty output should still return a result
        assert result is not None
