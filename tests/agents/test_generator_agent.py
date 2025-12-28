"""Unit tests for Generator Agent (TDD pipeline).

Based on OpenAI Agents SDK testing patterns.
Reference: refs/openai-agents-python/tests/test_agent_runner.py
"""

from __future__ import annotations

import json
import pytest

from agents import Agent, Runner, AgentOutputSchema

from src.models import GeneratedWebApp, WebAppPlan
from src.agents.generator_agent import (
    create_generator_agent,
    create_generation_prompt,
    generate_html_template,
    GENERATOR_INSTRUCTIONS,
    FormulaConversionResult,
    FormulaComplexityResult,
)

from tests.fake_model import FakeModel
from tests.helpers import get_text_message, get_json_message, get_generated_webapp_output


class TestGeneratorAgentCreation:
    """Tests for Generator Agent creation."""

    def test_create_generator_agent_returns_agent(self):
        """Test that create_generator_agent returns an Agent instance."""
        agent = create_generator_agent()
        assert agent is not None
        assert agent.name == "WebApp Generator"

    def test_generator_agent_uses_codex_model(self):
        """Test that generator agent uses gpt-5.1-codex model."""
        agent = create_generator_agent()
        assert agent.model == "gpt-5.1-codex"

    def test_generator_agent_has_tools(self):
        """Test that generator agent has formula conversion tools."""
        agent = create_generator_agent()
        assert len(agent.tools) == 3  # convert_formula, check_formula_complexity, get_js_helpers

    def test_generator_agent_output_type_is_generated_webapp(self):
        """Test that generator agent has GeneratedWebApp output type."""
        agent = create_generator_agent()
        assert agent.output_type is not None


class TestGeneratorAgentInstructions:
    """Tests for Generator Agent instructions."""

    def test_instructions_mention_html_generation(self):
        """Test that instructions mention HTML generation."""
        assert "HTML" in GENERATOR_INSTRUCTIONS
        assert "HTML5" in GENERATOR_INSTRUCTIONS

    def test_instructions_mention_bootstrap(self):
        """Test that instructions mention Bootstrap framework."""
        assert "Bootstrap" in GENERATOR_INSTRUCTIONS

    def test_instructions_mention_alpinejs(self):
        """Test that instructions mention Alpine.js."""
        assert "Alpine" in GENERATOR_INSTRUCTIONS

    def test_instructions_mention_korean_ui(self):
        """Test that instructions mention Korean UI."""
        assert "Korean" in GENERATOR_INSTRUCTIONS

    def test_instructions_mention_print_layout(self):
        """Test that instructions mention print layout."""
        assert "print" in GENERATOR_INSTRUCTIONS.lower()


class TestCreateGenerationPrompt:
    """Tests for create_generation_prompt function."""

    @pytest.fixture
    def sample_plan_dict(self):
        """Sample WebAppPlan dict for testing."""
        return {
            "app_name": "급여 계산기",
            "app_description": "급여 계산 앱입니다",
            "components": [
                {
                    "component_type": "form",
                    "title": "입력 양식",
                    "form_fields": [
                        {
                            "name": "salary",
                            "label": "급여",
                            "field_type": "number",
                            "source_cell": "B3",
                            "default_value": "0",
                        }
                    ],
                    "output_fields": [
                        {
                            "name": "tax",
                            "label": "세금",
                            "format": "currency",
                            "source_cell": "B10",
                        }
                    ],
                }
            ],
            "functions": [
                {
                    "name": "calculateTax",
                    "parameters": ["salary"],
                    "description": "Calculate tax from salary",
                    "source_formula": "=B3*0.1",
                }
            ],
            "input_cell_map": {"salary": "B3"},
            "output_cell_map": {"tax": "B10"},
            "print_layout": {
                "paper_size": "A4",
                "orientation": "portrait",
                "margins": {"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
            },
            "html_structure_notes": "Use Bootstrap grid",
            "css_style_notes": "Match Excel styling",
            "js_logic_notes": "Use Alpine.js reactive data",
        }

    def test_prompt_includes_app_name(self, sample_plan_dict):
        """Test that prompt includes app name."""
        prompt = create_generation_prompt(sample_plan_dict)
        assert "급여 계산기" in prompt

    def test_prompt_includes_component_info(self, sample_plan_dict):
        """Test that prompt includes component information."""
        prompt = create_generation_prompt(sample_plan_dict)
        assert "입력 양식" in prompt or "form" in prompt.lower()

    def test_prompt_includes_cell_mappings(self, sample_plan_dict):
        """Test that prompt includes cell mappings."""
        prompt = create_generation_prompt(sample_plan_dict)
        assert "B3" in prompt
        assert "B10" in prompt

    def test_prompt_includes_print_layout(self, sample_plan_dict):
        """Test that prompt includes print layout."""
        prompt = create_generation_prompt(sample_plan_dict)
        assert "A4" in prompt
        assert "portrait" in prompt

    def test_prompt_includes_original_formulas(self, sample_plan_dict):
        """Test that prompt includes original formulas when analysis provided."""
        analysis_dict = {
            "sheets": [
                {
                    "name": "Sheet1",
                    "formulas": [
                        {"cell": "B10", "formula": "=B3*0.1"},
                        {"cell": "B11", "formula": "=B3-B10"},
                    ],
                }
            ]
        }
        prompt = create_generation_prompt(sample_plan_dict, analysis_dict)
        assert "=B3*0.1" in prompt


class TestGeneratorAgentWithFakeModel:
    """Tests for Generator Agent using FakeModel (SDK pattern)."""

    @pytest.mark.asyncio
    async def test_generator_agent_returns_generated_webapp(self):
        """Test that generator agent returns GeneratedWebApp with FakeModel."""
        model = FakeModel()
        webapp_output = get_generated_webapp_output()
        model.set_next_output([get_json_message(webapp_output)])

        agent = Agent(
            name="WebApp Generator",
            instructions="Test instructions",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(GeneratedWebApp, strict_json_schema=False),
        )

        result = await Runner.run(agent, input="Generate a web app")

        assert result.final_output is not None
        if isinstance(result.final_output, GeneratedWebApp):
            assert result.final_output.app_name == "테스트 앱"
        elif isinstance(result.final_output, dict):
            assert result.final_output.get("app_name") == "테스트 앱"

    @pytest.mark.asyncio
    async def test_generator_agent_receives_input(self):
        """Test that generator agent receives the input correctly."""
        model = FakeModel()
        webapp_output = get_generated_webapp_output()
        model.set_next_output([get_json_message(webapp_output)])

        agent = Agent(
            name="WebApp Generator",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        result = await Runner.run(agent, input="generate code")

        assert result.input == "generate code"
        assert len(result.new_items) >= 1

    @pytest.mark.asyncio
    async def test_generator_agent_records_model_args(self):
        """Test that FakeModel records the arguments passed."""
        model = FakeModel()
        webapp_output = get_generated_webapp_output()
        model.set_next_output([get_json_message(webapp_output)])

        agent = Agent(
            name="WebApp Generator",
            instructions="Generate a complete web app",
            tools=[],
            model=model,
        )

        await Runner.run(agent, input="test input")

        assert model.first_turn_args is not None
        assert "Generate a complete web app" in model.first_turn_args.get("system_instructions", "")


class TestGeneratedWebAppOutput:
    """Tests for GeneratedWebApp output structure."""

    def test_generated_webapp_from_dict(self, sample_generated_webapp_dict):
        """Test creating GeneratedWebApp from dict."""
        webapp = GeneratedWebApp(**sample_generated_webapp_dict)
        assert webapp.app_name == "테스트 앱"
        assert webapp.source_excel == "test.xlsx"
        assert webapp.html is not None
        assert webapp.css is not None
        assert webapp.js is not None

    def test_generated_webapp_html_contains_doctype(self, sample_generated_webapp_dict):
        """Test that generated HTML contains DOCTYPE."""
        webapp = GeneratedWebApp(**sample_generated_webapp_dict)
        assert "<!DOCTYPE html>" in webapp.html

    def test_generated_webapp_html_contains_alpinejs(self, sample_generated_webapp_dict):
        """Test that generated HTML contains Alpine.js."""
        webapp = GeneratedWebApp(**sample_generated_webapp_dict)
        assert "x-data" in webapp.html or "alpine" in webapp.html.lower()

    def test_generated_webapp_has_iteration_count(self, sample_generated_webapp_dict):
        """Test that generated webapp has iteration count."""
        webapp = GeneratedWebApp(**sample_generated_webapp_dict)
        assert webapp.generation_iteration >= 1


class TestGenerateHtmlTemplate:
    """Tests for generate_html_template utility function."""

    @pytest.fixture
    def sample_webapp_plan(self):
        """Sample WebAppPlan for testing."""
        from src.models import PrintLayout
        return WebAppPlan(
            app_name="테스트 앱",
            app_description="테스트 설명",
            source_file="test.xlsx",
            components=[],
            functions=[],
            input_cell_map={},
            output_cell_map={},
            print_layout=PrintLayout(
                paper_size="A4",
                orientation="portrait",
                margins={"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
            ),
            html_structure_notes="Use Bootstrap grid",
            css_style_notes="Match Excel styling",
            js_logic_notes="Use Alpine.js reactive data",
        )

    def test_html_template_contains_doctype(self, sample_webapp_plan):
        """Test that template contains DOCTYPE."""
        html = generate_html_template(sample_webapp_plan)
        assert "<!DOCTYPE html>" in html

    def test_html_template_contains_bootstrap(self, sample_webapp_plan):
        """Test that template contains Bootstrap."""
        html = generate_html_template(sample_webapp_plan)
        assert "bootstrap" in html.lower()

    def test_html_template_contains_alpinejs(self, sample_webapp_plan):
        """Test that template contains Alpine.js."""
        html = generate_html_template(sample_webapp_plan)
        assert "alpinejs" in html.lower() or "alpine" in html.lower()

    def test_html_template_contains_app_name(self, sample_webapp_plan):
        """Test that template contains app name."""
        html = generate_html_template(sample_webapp_plan)
        assert "테스트 앱" in html

    def test_html_template_contains_print_styles(self, sample_webapp_plan):
        """Test that template contains print styles."""
        html = generate_html_template(sample_webapp_plan)
        assert "@media print" in html


class TestFormulaConversionModels:
    """Tests for formula conversion Pydantic models."""

    def test_formula_conversion_result_success(self):
        """Test successful formula conversion result."""
        result = FormulaConversionResult(
            success=True,
            js_code="salary * 0.1",
            requires_llm=False,
        )
        assert result.success is True
        assert result.js_code == "salary * 0.1"
        assert result.requires_llm is False
        assert result.error is None

    def test_formula_conversion_result_failure(self):
        """Test failed formula conversion result."""
        result = FormulaConversionResult(
            success=False,
            js_code="",
            requires_llm=True,
            error="Complex formula requires LLM",
        )
        assert result.success is False
        assert result.requires_llm is True
        assert result.error is not None

    def test_formula_complexity_result_simple(self):
        """Test simple formula complexity result."""
        result = FormulaComplexityResult(
            formula="=A1+B1",
            is_simple=True,
            conversion_method="direct",
        )
        assert result.is_simple is True
        assert result.conversion_method == "direct"

    def test_formula_complexity_result_complex(self):
        """Test complex formula complexity result."""
        result = FormulaComplexityResult(
            formula="=VLOOKUP(A1,Sheet2!A:B,2,FALSE)",
            is_simple=False,
            conversion_method="llm",
        )
        assert result.is_simple is False
        assert result.conversion_method == "llm"


class TestGeneratorAgentErrorHandling:
    """Tests for Generator Agent error handling."""

    @pytest.mark.asyncio
    async def test_generator_agent_handles_exception(self):
        """Test that generator agent handles model exceptions."""
        model = FakeModel()
        model.set_next_output(ValueError("Test error"))

        agent = Agent(
            name="WebApp Generator",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        with pytest.raises(ValueError) as exc_info:
            await Runner.run(agent, input="test input")

        assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generator_agent_handles_empty_output(self):
        """Test that generator agent handles empty output."""
        model = FakeModel()
        model.set_next_output([])  # Empty output

        agent = Agent(
            name="WebApp Generator",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        result = await Runner.run(agent, input="test input")

        # Empty output should still return a result
        assert result is not None
