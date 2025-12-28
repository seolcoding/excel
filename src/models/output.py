"""Generated web app output models."""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestEvaluation(BaseModel):
    """Structured evaluation result from the Tester Agent (LLM-as-a-Judge)."""
    score: Literal["pass", "needs_improvement", "fail"] = Field(
        description="Overall evaluation score"
    )
    pass_rate: float = Field(
        description="Percentage of tests passed (0.0 to 1.0)"
    )
    passed_tests: list[str] = Field(
        default_factory=list,
        description="Names of passed tests"
    )
    failed_tests: list[str] = Field(
        default_factory=list,
        description="Names of failed tests"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Detailed description of each issue found"
    )
    feedback: str = Field(
        default="",
        description="Specific, actionable feedback for improvement"
    )
    suggested_fixes: list[str] = Field(
        default_factory=list,
        description="Concrete code fixes or changes to make"
    )


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
