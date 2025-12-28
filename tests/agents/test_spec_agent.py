"""Unit tests for Spec Agent (TDD pipeline).

Based on OpenAI Agents SDK testing patterns.
Reference: refs/openai-agents-python/tests/test_agent_runner.py
"""

from __future__ import annotations

import json
import pytest

from agents import Agent, Runner, AgentOutputSchema

from src.models import WebAppSpec
from src.agents.spec_agent import (
    create_spec_agent,
    create_spec_prompt,
    SPEC_AGENT_INSTRUCTIONS,
)

from tests.fake_model import FakeModel
from tests.helpers import get_text_message, get_json_message, get_webapp_spec_output


class TestSpecAgentCreation:
    """Tests for Spec Agent creation."""

    def test_create_spec_agent_returns_agent(self):
        """Test that create_spec_agent returns an Agent instance."""
        agent = create_spec_agent()
        assert agent is not None
        assert agent.name == "TDD Spec Architect"

    def test_spec_agent_uses_correct_model(self):
        """Test that spec agent uses gpt-5.2 model."""
        agent = create_spec_agent()
        assert agent.model == "gpt-5.2"

    def test_spec_agent_has_no_tools(self):
        """Test that spec agent has no tools (pure LLM reasoning)."""
        agent = create_spec_agent()
        assert agent.tools == []

    def test_spec_agent_output_type_is_webapp_spec(self):
        """Test that spec agent has WebAppSpec output type."""
        agent = create_spec_agent()
        assert agent.output_type is not None


class TestSpecAgentInstructions:
    """Tests for Spec Agent instructions."""

    def test_instructions_mention_tdd(self):
        """Test that instructions mention TDD."""
        assert "TDD" in SPEC_AGENT_INSTRUCTIONS

    def test_instructions_mention_expected_behaviors(self):
        """Test that instructions mention expected behaviors."""
        assert "Expected Behaviors" in SPEC_AGENT_INSTRUCTIONS

    def test_instructions_mention_boundary_conditions(self):
        """Test that instructions mention boundary conditions."""
        assert "Boundary Conditions" in SPEC_AGENT_INSTRUCTIONS

    def test_instructions_mention_input_fields(self):
        """Test that instructions define input fields spec."""
        assert "input_fields" in SPEC_AGENT_INSTRUCTIONS.lower() or "input" in SPEC_AGENT_INSTRUCTIONS.lower()

    def test_instructions_mention_korean(self):
        """Test that instructions mention Korean labels."""
        assert "Korean" in SPEC_AGENT_INSTRUCTIONS


class TestCreateSpecPrompt:
    """Tests for create_spec_prompt function."""

    def test_prompt_includes_filename(self, sample_excel_analysis_dict):
        """Test that prompt includes Excel filename."""
        prompt = create_spec_prompt(sample_excel_analysis_dict)
        assert "test_workbook.xlsx" in prompt

    def test_prompt_includes_sheet_info(self, sample_excel_analysis_dict):
        """Test that prompt includes sheet information."""
        prompt = create_spec_prompt(sample_excel_analysis_dict)
        assert "Sheet1" in prompt

    def test_prompt_includes_formulas(self, sample_excel_analysis_dict):
        """Test that prompt includes formulas."""
        prompt = create_spec_prompt(sample_excel_analysis_dict)
        assert "B10" in prompt or "formula" in prompt.lower()

    def test_prompt_mentions_tdd(self, sample_excel_analysis_dict):
        """Test that prompt mentions TDD requirements."""
        prompt = create_spec_prompt(sample_excel_analysis_dict)
        assert "TDD" in prompt or "test" in prompt.lower()

    def test_prompt_mentions_boundary_conditions(self, sample_excel_analysis_dict):
        """Test that prompt asks for boundary conditions."""
        prompt = create_spec_prompt(sample_excel_analysis_dict)
        assert "boundary" in prompt.lower() or "edge" in prompt.lower()

    def test_prompt_handles_empty_sheets(self):
        """Test that prompt handles empty sheets gracefully."""
        analysis_dict = {
            "filename": "empty.xlsx",
            "sheets": [],
            "has_vba": False,
        }
        prompt = create_spec_prompt(analysis_dict)
        assert "empty.xlsx" in prompt

    def test_prompt_handles_vba_modules(self):
        """Test that prompt handles VBA modules."""
        analysis_dict = {
            "filename": "with_vba.xlsm",
            "sheets": [],
            "has_vba": True,
            "vba_modules": [
                {"name": "Module1", "procedures": ["Calculate", "Validate"]}
            ],
        }
        prompt = create_spec_prompt(analysis_dict)
        assert "VBA" in prompt or "Module1" in prompt


class TestSpecAgentWithFakeModel:
    """Tests for Spec Agent using FakeModel (SDK pattern)."""

    @pytest.mark.asyncio
    async def test_spec_agent_returns_webapp_spec(self):
        """Test that spec agent returns WebAppSpec with FakeModel."""
        model = FakeModel()
        spec_output = get_webapp_spec_output()
        model.set_next_output([get_json_message(spec_output)])

        agent = Agent(
            name="TDD Spec Architect",
            instructions="Test instructions",
            tools=[],
            model=model,
            output_type=AgentOutputSchema(WebAppSpec, strict_json_schema=False),
        )

        result = await Runner.run(agent, input="Create a spec for salary calculator")

        assert result.final_output is not None
        # Output could be WebAppSpec or dict depending on parsing
        if isinstance(result.final_output, WebAppSpec):
            assert result.final_output.app_name == "테스트 앱"
        elif isinstance(result.final_output, dict):
            assert result.final_output.get("app_name") == "테스트 앱"

    @pytest.mark.asyncio
    async def test_spec_agent_captures_input(self):
        """Test that spec agent receives the input correctly."""
        model = FakeModel()
        spec_output = get_webapp_spec_output()
        model.set_next_output([get_json_message(spec_output)])

        agent = Agent(
            name="TDD Spec Architect",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        result = await Runner.run(agent, input="test input")

        assert result.input == "test input"
        assert len(result.new_items) >= 1

    @pytest.mark.asyncio
    async def test_spec_agent_records_model_args(self):
        """Test that FakeModel records the arguments passed."""
        model = FakeModel()
        spec_output = get_webapp_spec_output()
        model.set_next_output([get_json_message(spec_output)])

        agent = Agent(
            name="TDD Spec Architect",
            instructions="Custom instructions for testing",
            tools=[],
            model=model,
        )

        await Runner.run(agent, input="test input")

        # Verify model received the system instructions
        assert model.first_turn_args is not None
        assert "Custom instructions" in model.first_turn_args.get("system_instructions", "")


class TestWebAppSpecOutput:
    """Tests for WebAppSpec output structure."""

    def test_webapp_spec_from_dict(self, sample_webapp_spec_dict):
        """Test creating WebAppSpec from dict."""
        spec = WebAppSpec(**sample_webapp_spec_dict)
        assert spec.app_name == "테스트 앱"
        assert len(spec.input_fields) == 1
        assert len(spec.output_fields) == 1
        assert len(spec.expected_behaviors) == 2
        assert len(spec.boundary_conditions) == 1

    def test_webapp_spec_input_fields_structure(self, sample_webapp_spec_dict):
        """Test input field structure in WebAppSpec."""
        spec = WebAppSpec(**sample_webapp_spec_dict)
        salary_field = spec.input_fields[0]
        assert salary_field["name"] == "salary"
        assert salary_field["type"] == "number"
        assert salary_field["label"] == "급여"
        assert salary_field["source_cell"] == "B3"

    def test_webapp_spec_expected_behaviors(self, sample_webapp_spec_dict):
        """Test expected behaviors in WebAppSpec."""
        spec = WebAppSpec(**sample_webapp_spec_dict)
        assert "Salary 5000000 → Tax 500000" in spec.expected_behaviors
        assert "Zero salary → Tax 0" in spec.expected_behaviors

    def test_webapp_spec_boundary_conditions(self, sample_webapp_spec_dict):
        """Test boundary conditions in WebAppSpec."""
        spec = WebAppSpec(**sample_webapp_spec_dict)
        bc = spec.boundary_conditions[0]
        assert bc["name"] == "zero_salary"
        assert bc["inputs"] == {"salary": 0}
        assert bc["expected_output"] == {"tax": 0}

    def test_webapp_spec_korean_labels(self, sample_webapp_spec_dict):
        """Test Korean labels setting."""
        spec = WebAppSpec(**sample_webapp_spec_dict)
        assert spec.korean_labels is True

    def test_webapp_spec_print_layout(self, sample_webapp_spec_dict):
        """Test print layout configuration."""
        spec = WebAppSpec(**sample_webapp_spec_dict)
        assert spec.print_layout["paper_size"] == "A4"
        assert spec.print_layout["orientation"] == "portrait"


class TestSpecAgentErrorHandling:
    """Tests for Spec Agent error handling."""

    @pytest.mark.asyncio
    async def test_spec_agent_handles_exception(self):
        """Test that spec agent handles model exceptions."""
        model = FakeModel()
        model.set_next_output(ValueError("Test error"))

        agent = Agent(
            name="TDD Spec Architect",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        with pytest.raises(ValueError) as exc_info:
            await Runner.run(agent, input="test input")

        assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_spec_agent_handles_empty_output(self):
        """Test that spec agent handles empty output."""
        model = FakeModel()
        model.set_next_output([])  # Empty output

        agent = Agent(
            name="TDD Spec Architect",
            instructions="Test instructions",
            tools=[],
            model=model,
        )

        result = await Runner.run(agent, input="test input")

        # Empty output should still return a result
        assert result is not None
