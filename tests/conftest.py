"""Pytest configuration and shared fixtures for TDD Pipeline tests.

Based on OpenAI Agents SDK testing patterns.
Reference: refs/openai-agents-python/tests/conftest.py
"""

from __future__ import annotations

import os
import pytest

from agents.models import _openai_shared
from agents.run import set_default_agent_runner
from agents.tracing import set_trace_processors

from .fake_model import FakeModel
from .helpers import (
    get_text_message,
    get_json_message,
    get_webapp_spec_output,
    get_generated_webapp_output,
    get_test_evaluation_output,
    get_excel_analysis_output,
)


# ============================================
# SDK-Style Session Fixtures
# ============================================

@pytest.fixture(scope="session", autouse=True)
def ensure_openai_api_key():
    """Ensure a default OpenAI API key is present for tests."""
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test_key_for_unit_tests"


@pytest.fixture(autouse=True)
def clear_openai_settings():
    """Clear OpenAI settings before each test."""
    _openai_shared._default_openai_key = None
    _openai_shared._default_openai_client = None
    _openai_shared._use_responses_by_default = True


@pytest.fixture(autouse=True)
def clear_default_runner():
    """Clear default runner before each test."""
    set_default_agent_runner(None)


# ============================================
# FakeModel Fixtures
# ============================================

@pytest.fixture
def fake_model():
    """Create a fresh FakeModel for testing."""
    return FakeModel()


@pytest.fixture
def fake_model_with_spec_output():
    """Create a FakeModel that returns a WebAppSpec."""
    model = FakeModel()
    model.set_next_output([get_json_message(get_webapp_spec_output())])
    return model


@pytest.fixture
def fake_model_with_webapp_output():
    """Create a FakeModel that returns a GeneratedWebApp."""
    model = FakeModel()
    model.set_next_output([get_json_message(get_generated_webapp_output())])
    return model


@pytest.fixture
def fake_model_with_evaluation_pass():
    """Create a FakeModel that returns a passing TestEvaluation."""
    model = FakeModel()
    model.set_next_output([get_json_message(get_test_evaluation_output(passed=True))])
    return model


@pytest.fixture
def fake_model_with_evaluation_fail():
    """Create a FakeModel that returns a failing TestEvaluation."""
    model = FakeModel()
    model.set_next_output([get_json_message(get_test_evaluation_output(passed=False))])
    return model


# ============================================
# Model Fixtures
# ============================================

@pytest.fixture
def sample_webapp_spec_dict():
    """Sample WebAppSpec as dict."""
    return get_webapp_spec_output()


@pytest.fixture
def sample_generated_webapp_dict():
    """Sample GeneratedWebApp as dict."""
    return get_generated_webapp_output()


@pytest.fixture
def sample_test_evaluation_dict():
    """Sample TestEvaluation as dict (passing)."""
    return get_test_evaluation_output(passed=True)


@pytest.fixture
def sample_excel_analysis_dict():
    """Sample ExcelAnalysis as dict."""
    return get_excel_analysis_output()


# ============================================
# Pydantic Model Fixtures
# ============================================

@pytest.fixture
def sample_webapp_spec():
    """Sample WebAppSpec Pydantic model."""
    from src.models import WebAppSpec
    return WebAppSpec(**get_webapp_spec_output())


@pytest.fixture
def sample_generated_webapp():
    """Sample GeneratedWebApp Pydantic model."""
    from src.models import GeneratedWebApp
    return GeneratedWebApp(**get_generated_webapp_output())


@pytest.fixture
def sample_test_evaluation():
    """Sample TestEvaluation Pydantic model."""
    from src.models import TestEvaluation
    return TestEvaluation(**get_test_evaluation_output(passed=True))


@pytest.fixture
def sample_excel_analysis():
    """Sample ExcelAnalysis Pydantic model."""
    from src.models import ExcelAnalysis
    return ExcelAnalysis(**get_excel_analysis_output())


@pytest.fixture
def sample_verification_report():
    """Sample VerificationReport Pydantic model."""
    from src.models import VerificationReport
    return VerificationReport(
        spec_name="테스트 앱",
        total_requirements=5,
        verified_requirements=4,
        unverified_requirements=1,
        verification_rate=0.8,
        requirement_results=[
            {
                "requirement": "Salary 5000000 → Tax 500000",
                "test_name": "behavior_0",
                "passed": True,
                "details": "Verified by static tests",
            },
        ],
        static_test_pass_rate=0.9,
        llm_evaluation_pass_rate=0.85,
        combined_pass_rate=0.88,
        blocking_issues=[],
        warnings=["Minor formatting issue"],
    )


# ============================================
# Agent Fixtures
# ============================================

@pytest.fixture
def spec_agent_with_fake_model(fake_model_with_spec_output):
    """Spec Agent with FakeModel for testing."""
    from agents import Agent, AgentOutputSchema
    from src.models import WebAppSpec

    return Agent(
        name="TDD Spec Architect",
        instructions="Test instructions",
        tools=[],
        model=fake_model_with_spec_output,
        output_type=AgentOutputSchema(WebAppSpec, strict_json_schema=False),
    )


@pytest.fixture
def generator_agent_with_fake_model(fake_model_with_webapp_output):
    """Generator Agent with FakeModel for testing."""
    from agents import Agent, AgentOutputSchema
    from src.models import GeneratedWebApp

    return Agent(
        name="WebApp Generator",
        instructions="Test instructions",
        tools=[],
        model=fake_model_with_webapp_output,
        output_type=AgentOutputSchema(GeneratedWebApp, strict_json_schema=False),
    )


@pytest.fixture
def tester_agent_with_fake_model(fake_model_with_evaluation_pass):
    """Tester Agent with FakeModel for testing."""
    from agents import Agent, AgentOutputSchema
    from src.models import TestEvaluation

    return Agent(
        name="WebApp Tester",
        instructions="Test instructions",
        tools=[],
        model=fake_model_with_evaluation_pass,
        output_type=AgentOutputSchema(TestEvaluation, strict_json_schema=False),
    )


# ============================================
# Integration Test Fixtures
# ============================================

@pytest.fixture
def sample_excel_path(tmp_path):
    """Create a temporary Excel file path (for mocking)."""
    excel_file = tmp_path / "test_workbook.xlsx"
    return str(excel_file)


@pytest.fixture
def progress_callback():
    """Progress callback that collects progress updates."""
    updates = []

    def callback(progress):
        updates.append({
            "stage": progress.stage,
            "message": progress.message,
            "progress": progress.progress,
        })

    callback.updates = updates
    return callback
