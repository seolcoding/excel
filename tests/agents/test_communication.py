"""Unit tests for agent communication protocols.

Tests the data flow between agents in the TDD pipeline:
- Analyze → Spec Agent (ExcelAnalysis → WebAppSpec)
- Spec Agent → Generator (WebAppSpec → GeneratedWebApp)
- Generator → Tester (GeneratedWebApp → TestEvaluation)
- Verification Report generation

Based on OpenAI Agents SDK testing patterns.
"""

from __future__ import annotations

import json
import pytest

from agents import Agent, Runner, AgentOutputSchema

from src.models import (
    ExcelAnalysis,
    WebAppSpec,
    WebAppPlan,
    GeneratedWebApp,
    VerificationReport,
)
from src.agents.spec_agent import create_spec_prompt, create_spec_agent
from src.agents.generator_agent import create_generation_prompt, create_generator_agent
from src.agents.tester_agent import create_test_prompt, create_tester_agent, TestEvaluation

from tests.fake_model import FakeModel
from tests.helpers import (
    get_json_message,
    get_webapp_spec_output,
    get_generated_webapp_output,
    get_test_evaluation_output,
    get_excel_analysis_output,
)


class TestAnalysisToSpecCommunication:
    """Tests for Analyze → Spec Agent communication."""

    @pytest.fixture
    def excel_analysis(self):
        """Sample ExcelAnalysis for testing."""
        return get_excel_analysis_output()

    def test_spec_prompt_contains_analysis_data(self, excel_analysis):
        """Test that spec prompt includes analysis data."""
        prompt = create_spec_prompt(excel_analysis)

        # Should contain filename
        assert excel_analysis["filename"] in prompt

        # Should contain sheet info
        for sheet in excel_analysis["sheets"]:
            assert sheet["name"] in prompt

    def test_spec_prompt_contains_formulas(self, excel_analysis):
        """Test that spec prompt includes formulas from analysis."""
        prompt = create_spec_prompt(excel_analysis)

        # Should contain formula references
        for sheet in excel_analysis["sheets"]:
            for formula in sheet["formulas"]:
                # At least the cell reference should appear
                assert formula["cell"] in prompt or "formula" in prompt.lower()

    def test_spec_prompt_contains_input_output_cells(self, excel_analysis):
        """Test that spec prompt includes I/O cell information."""
        prompt = create_spec_prompt(excel_analysis)

        for sheet in excel_analysis["sheets"]:
            for cell in sheet["input_cells"]:
                assert cell in prompt or "input" in prompt.lower()

    @pytest.mark.asyncio
    async def test_spec_agent_produces_webapp_spec(self, excel_analysis):
        """Test that Spec Agent produces WebAppSpec from analysis."""
        model = FakeModel()
        spec_output = get_webapp_spec_output()
        model.set_next_output([get_json_message(spec_output)])

        agent = Agent(
            name="TDD Spec Architect",
            instructions="Generate a spec from analysis",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(WebAppSpec, strict_json_schema=False),
        )

        prompt = create_spec_prompt(excel_analysis)
        result = await Runner.run(agent, input=prompt)

        assert result.final_output is not None


class TestSpecToGeneratorCommunication:
    """Tests for Spec → Generator communication (via Plan conversion)."""

    @pytest.fixture
    def webapp_spec(self):
        """Sample WebAppSpec for testing."""
        return get_webapp_spec_output()

    def test_spec_can_be_converted_to_plan(self, webapp_spec):
        """Test that WebAppSpec can be converted to WebAppPlan structure."""
        # This mimics the _spec_to_plan conversion in orchestrator
        spec = WebAppSpec(**webapp_spec)

        plan_dict = {
            "app_name": spec.app_name,
            "app_description": spec.app_description,
            "components": [],
            "functions": [],
            "input_cell_map": {},
            "output_cell_map": {},
            "print_layout": spec.print_layout or {},
        }

        # Add input fields to components
        form_fields = []
        for field in spec.input_fields:
            form_fields.append({
                "name": field["name"],
                "label": field.get("label", field["name"]),
                "field_type": field["type"],
                "source_cell": field.get("source_cell", ""),
                "required": field.get("validation", {}).get("required", False),
            })
            plan_dict["input_cell_map"][field["name"]] = field.get("source_cell", "")

        # Add output fields to components
        output_fields = []
        for field in spec.output_fields:
            output_fields.append({
                "name": field["name"],
                "label": field.get("label", field["name"]),
                "format": field.get("format", "text"),
                "source_cell": field.get("source_cell", ""),
            })
            plan_dict["output_cell_map"][field["name"]] = field.get("source_cell", "")

        if form_fields or output_fields:
            plan_dict["components"].append({
                "component_type": "form",
                "title": "입력/결과",
                "form_fields": form_fields,
                "output_fields": output_fields,
            })

        # Verify conversion
        assert plan_dict["app_name"] == spec.app_name
        assert len(plan_dict["input_cell_map"]) == len(spec.input_fields)
        assert len(plan_dict["output_cell_map"]) == len(spec.output_fields)

    def test_generation_prompt_contains_plan_data(self, webapp_spec):
        """Test that generation prompt includes plan data."""
        spec = WebAppSpec(**webapp_spec)

        # Create a minimal plan from spec
        plan_dict = {
            "app_name": spec.app_name,
            "app_description": spec.app_description,
            "components": [{
                "component_type": "form",
                "title": "입력",
                "form_fields": [
                    {
                        "name": f["name"],
                        "label": f.get("label", f["name"]),
                        "field_type": f["type"],
                        "source_cell": f.get("source_cell", ""),
                        "default_value": "0",
                    }
                    for f in spec.input_fields
                ],
                "output_fields": [
                    {
                        "name": f["name"],
                        "label": f.get("label", f["name"]),
                        "format": f.get("format", "text"),
                        "source_cell": f.get("source_cell", ""),
                    }
                    for f in spec.output_fields
                ],
            }],
            "functions": [],
            "input_cell_map": {f["name"]: f.get("source_cell", "") for f in spec.input_fields},
            "output_cell_map": {f["name"]: f.get("source_cell", "") for f in spec.output_fields},
            "print_layout": spec.print_layout or {},
        }

        prompt = create_generation_prompt(plan_dict)

        assert spec.app_name in prompt
        assert "salary" in prompt.lower() or "입력" in prompt

    @pytest.mark.asyncio
    async def test_generator_receives_plan_data(self, webapp_spec):
        """Test that Generator Agent receives and processes plan data."""
        model = FakeModel()
        webapp_output = get_generated_webapp_output()
        model.set_next_output([get_json_message(webapp_output)])

        agent = Agent(
            name="WebApp Generator",
            instructions="Generate code from plan",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(GeneratedWebApp, strict_json_schema=False),
        )

        # Minimal plan prompt
        plan_dict = {
            "app_name": "테스트 앱",
            "app_description": "테스트",
            "components": [],
            "functions": [],
            "input_cell_map": {},
            "output_cell_map": {},
            "print_layout": {},
        }
        prompt = create_generation_prompt(plan_dict)
        result = await Runner.run(agent, input=prompt)

        assert result.final_output is not None
        # Verify model received the prompt
        assert model.first_turn_args is not None


class TestGeneratorToTesterCommunication:
    """Tests for Generator → Tester communication."""

    @pytest.fixture
    def generated_webapp(self):
        """Sample GeneratedWebApp for testing."""
        return get_generated_webapp_output()

    def test_test_prompt_contains_generated_code(self, generated_webapp):
        """Test that test prompt includes generated code."""
        prompt = create_test_prompt(
            html=generated_webapp["html"],
            css=generated_webapp["css"],
            js=generated_webapp["js"],
            formulas=[{"cell": "B10", "formula": "=B3*0.1"}],
            iteration=1,
        )

        # Should contain code sections
        assert "html" in prompt.lower()
        assert "css" in prompt.lower()
        assert "javascript" in prompt.lower()

    def test_test_prompt_contains_formulas_to_verify(self, generated_webapp):
        """Test that test prompt includes formulas to verify."""
        formulas = [
            {"cell": "B10", "formula": "=B3*0.1"},
            {"cell": "B11", "formula": "=SUM(B1:B5)"},
        ]

        prompt = create_test_prompt(
            html=generated_webapp["html"],
            css=generated_webapp["css"],
            js=generated_webapp["js"],
            formulas=formulas,
            iteration=1,
        )

        assert "B10" in prompt
        assert "=B3*0.1" in prompt

    @pytest.mark.asyncio
    async def test_tester_receives_generated_code(self, generated_webapp):
        """Test that Tester Agent receives and evaluates generated code."""
        model = FakeModel()
        eval_output = get_test_evaluation_output(passed=True)
        model.set_next_output([get_json_message(eval_output)])

        agent = Agent(
            name="Code Tester",
            instructions="Evaluate the code",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(TestEvaluation, strict_json_schema=False),
        )

        prompt = create_test_prompt(
            html=generated_webapp["html"],
            css=generated_webapp["css"],
            js=generated_webapp["js"],
            formulas=[],
            iteration=1,
        )
        result = await Runner.run(agent, input=prompt)

        assert result.final_output is not None


class TestVerificationReportGeneration:
    """Tests for Verification Report generation from test results."""

    @pytest.fixture
    def webapp_spec(self):
        """Sample WebAppSpec for testing."""
        return get_webapp_spec_output()

    @pytest.fixture
    def test_evaluation_pass(self):
        """Passing TestEvaluation for testing."""
        return get_test_evaluation_output(passed=True)

    @pytest.fixture
    def test_evaluation_fail(self):
        """Failing TestEvaluation for testing."""
        return get_test_evaluation_output(passed=False)

    def test_verification_report_from_passing_evaluation(
        self, webapp_spec, test_evaluation_pass
    ):
        """Test creating VerificationReport from passing evaluation."""
        spec = WebAppSpec(**webapp_spec)
        evaluation = TestEvaluation(**test_evaluation_pass)

        # Calculate verification
        total_requirements = len(spec.expected_behaviors) + len(spec.boundary_conditions)
        verified = int(evaluation.pass_rate * total_requirements)

        report = VerificationReport(
            spec_name=spec.app_name,
            total_requirements=total_requirements,
            verified_requirements=verified,
            unverified_requirements=total_requirements - verified,
            verification_rate=evaluation.pass_rate,
            requirement_results=[
                {
                    "requirement": behavior,
                    "test_name": f"behavior_{i}",
                    "passed": True,
                    "details": "Verified",
                }
                for i, behavior in enumerate(spec.expected_behaviors)
            ],
            static_test_pass_rate=evaluation.pass_rate,
            llm_evaluation_pass_rate=evaluation.pass_rate,
            combined_pass_rate=evaluation.pass_rate,
            blocking_issues=[],
            warnings=[],
        )

        assert report.spec_name == spec.app_name
        assert report.verification_rate == evaluation.pass_rate
        assert report.combined_pass_rate >= 0.9  # Pass threshold

    def test_verification_report_from_failing_evaluation(
        self, webapp_spec, test_evaluation_fail
    ):
        """Test creating VerificationReport from failing evaluation."""
        spec = WebAppSpec(**webapp_spec)
        evaluation = TestEvaluation(**test_evaluation_fail)

        total_requirements = len(spec.expected_behaviors) + len(spec.boundary_conditions)
        verified = int(evaluation.pass_rate * total_requirements)

        report = VerificationReport(
            spec_name=spec.app_name,
            total_requirements=total_requirements,
            verified_requirements=verified,
            unverified_requirements=total_requirements - verified,
            verification_rate=evaluation.pass_rate,
            requirement_results=[
                {
                    "requirement": behavior,
                    "test_name": f"behavior_{i}",
                    "passed": i < verified,
                    "details": "Verified" if i < verified else "Failed",
                }
                for i, behavior in enumerate(spec.expected_behaviors)
            ],
            static_test_pass_rate=0.5,
            llm_evaluation_pass_rate=evaluation.pass_rate,
            combined_pass_rate=0.5 * 0.6 + evaluation.pass_rate * 0.4,  # 60/40 weighted
            blocking_issues=evaluation.issues,
            warnings=[],
        )

        assert report.verification_rate < 0.9  # Below pass threshold
        assert len(report.blocking_issues) > 0


class TestAgentChainCommunication:
    """Tests for full agent chain communication."""

    @pytest.mark.asyncio
    async def test_full_pipeline_data_flow(self):
        """Test data flows correctly through entire pipeline."""
        # Step 1: Analysis → Spec
        analysis = get_excel_analysis_output()
        spec_prompt = create_spec_prompt(analysis)
        assert analysis["filename"] in spec_prompt

        # Step 2: Spec → Generator (via Plan)
        spec_output = get_webapp_spec_output()
        plan_dict = {
            "app_name": spec_output["app_name"],
            "app_description": spec_output["app_description"],
            "components": [],
            "functions": [],
            "input_cell_map": {},
            "output_cell_map": {},
            "print_layout": spec_output["print_layout"],
        }
        gen_prompt = create_generation_prompt(plan_dict)
        assert spec_output["app_name"] in gen_prompt

        # Step 3: Generator → Tester
        webapp_output = get_generated_webapp_output()
        test_prompt = create_test_prompt(
            html=webapp_output["html"],
            css=webapp_output["css"],
            js=webapp_output["js"],
            formulas=[{"cell": "B10", "formula": "=B3*0.1"}],
            iteration=1,
        )
        assert "html" in test_prompt.lower()

    @pytest.mark.asyncio
    async def test_iteration_loop_communication(self):
        """Test that iteration loop passes feedback correctly."""
        # First iteration
        model = FakeModel()
        fail_output = get_test_evaluation_output(passed=False)
        pass_output = get_test_evaluation_output(passed=True)
        model.add_multiple_turn_outputs([
            [get_json_message(fail_output)],  # First iteration fails
            [get_json_message(pass_output)],  # Second iteration passes
        ])

        agent = Agent(
            name="Code Tester",
            instructions="Test code",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(TestEvaluation, strict_json_schema=False),
        )

        # First run - should fail
        result1 = await Runner.run(agent, input="Evaluate iteration 1")
        output1 = result1.final_output
        if isinstance(output1, dict):
            output1 = TestEvaluation(**output1)

        assert output1.score == "needs_improvement"
        assert len(output1.suggested_fixes) > 0  # Has feedback for next iteration

        # Second run with feedback
        model.set_next_output([get_json_message(pass_output)])
        feedback = output1.suggested_fixes[0] if output1.suggested_fixes else "Fix the issues"
        result2 = await Runner.run(agent, input=f"Evaluate iteration 2 after fix: {feedback}")
        output2 = result2.final_output
        if isinstance(output2, dict):
            output2 = TestEvaluation(**output2)

        assert output2.score == "pass"


class TestSpecToTestGeneration:
    """Tests for Spec → Test-First generation."""

    @pytest.fixture
    def webapp_spec(self):
        """Sample WebAppSpec for testing."""
        return get_webapp_spec_output()

    def test_tests_generated_from_expected_behaviors(self, webapp_spec):
        """Test that tests are generated from expected_behaviors."""
        spec = WebAppSpec(**webapp_spec)

        # Simulate test generation from spec
        generated_tests = []
        for i, behavior in enumerate(spec.expected_behaviors):
            test = {
                "name": f"test_behavior_{i}",
                "description": behavior,
                "assertion": f"// Verify: {behavior}",
            }
            generated_tests.append(test)

        assert len(generated_tests) == len(spec.expected_behaviors)
        assert "Salary 5000000" in generated_tests[0]["description"]

    def test_tests_generated_from_boundary_conditions(self, webapp_spec):
        """Test that tests are generated from boundary_conditions."""
        spec = WebAppSpec(**webapp_spec)

        # Simulate test generation from spec
        generated_tests = []
        for i, bc in enumerate(spec.boundary_conditions):
            test = {
                "name": f"test_boundary_{bc['name']}",
                "inputs": bc["inputs"],
                "expected": bc["expected_output"],
                "description": bc.get("description", ""),
            }
            generated_tests.append(test)

        assert len(generated_tests) == len(spec.boundary_conditions)
        assert generated_tests[0]["inputs"] == {"salary": 0}
        assert generated_tests[0]["expected"] == {"tax": 0}
