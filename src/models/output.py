"""Generated web app output models."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestResult(BaseModel):
    """Result of a single test."""
    test_name: str
    test_type: str  # 'formula', 'vba_logic', 'print_layout', 'input_output'
    status: TestStatus
    expected: Optional[str] = None
    actual: Optional[str] = None
    message: Optional[str] = None


class TestSuite(BaseModel):
    """Results of all tests for a generated web app."""
    total: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float
    results: list[TestResult]


class GeneratedCode(BaseModel):
    """Generated code for a component."""
    component_name: str
    html: str
    css: str
    js: str


class GeneratedWebApp(BaseModel):
    """Complete generated web application."""
    app_name: str
    source_excel: str

    # Generated code
    html: str
    css: str
    js: str

    # Individual components (for debugging/review)
    components: list[GeneratedCode] = []

    # Metadata
    generation_iteration: int = 1
    test_results: Optional[TestSuite] = None
    feedback_applied: list[str] = []


class ImprovementFeedback(BaseModel):
    """Feedback for improving generated code."""
    iteration: int
    failed_tests: list[TestResult]
    improvement_instructions: str
    focus_areas: list[str]


class ConversionResult(BaseModel):
    """Final result of Excel to WebApp conversion."""
    success: bool
    app: Optional[GeneratedWebApp] = None
    iterations_used: int
    final_pass_rate: float
    message: str
    conversation_trace: Optional[dict] = None  # Full LLM conversation history
