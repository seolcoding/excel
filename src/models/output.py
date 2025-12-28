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


class WebAppSpec(BaseModel):
    """TDD Specification - Defines what the app should do (replaces WebAppPlan in TDD flow).

    This spec is used to:
    1. Generate failing tests first (Test-First)
    2. Guide code generation to pass those tests
    """
    app_name: str = Field(description="Name of the web application")
    app_description: str = Field(description="Description of what the app does")

    # Functional requirements
    input_fields: list[dict] = Field(
        default_factory=list,
        description="Input fields with name, type, label, validation rules"
    )
    output_fields: list[dict] = Field(
        default_factory=list,
        description="Output fields with name, format, source formula/cell"
    )
    calculations: list[dict] = Field(
        default_factory=list,
        description="Calculation specs: input cells → formula → output"
    )

    # Test expectations
    expected_behaviors: list[str] = Field(
        default_factory=list,
        description="Expected behaviors to test"
    )
    boundary_conditions: list[dict] = Field(
        default_factory=list,
        description="Boundary value test cases"
    )

    # UI requirements
    korean_labels: bool = Field(default=True, description="Use Korean UI labels")
    print_layout: Optional[dict] = Field(default=None, description="Print layout requirements")


class VerificationReport(BaseModel):
    """Verification report linking test results to requirements.

    Provides traceability from requirements → tests → results.
    """
    spec_name: str = Field(description="Name of the WebAppSpec verified")
    total_requirements: int = Field(description="Total number of requirements")
    verified_requirements: int = Field(description="Requirements with passing tests")
    unverified_requirements: int = Field(description="Requirements with failing tests")
    verification_rate: float = Field(description="Percentage of verified requirements")

    # Detailed results
    requirement_results: list[dict] = Field(
        default_factory=list,
        description="Per-requirement verification: {requirement, test_name, passed, details}"
    )

    # Summary
    static_test_pass_rate: float = Field(default=0.0, description="Static test pass rate")
    llm_evaluation_pass_rate: float = Field(default=0.0, description="LLM evaluation pass rate")
    combined_pass_rate: float = Field(default=0.0, description="Weighted combined pass rate")

    # Issues
    blocking_issues: list[str] = Field(
        default_factory=list,
        description="Critical issues that must be fixed"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-critical issues or recommendations"
    )


class ConversionResult(BaseModel):
    """Final result of Excel to WebApp conversion."""
    success: bool
    app: Optional[GeneratedWebApp] = None
    iterations_used: int
    final_pass_rate: float
    message: str
    conversation_trace: Optional[dict] = None  # Full LLM conversation history
    verification_report: Optional[VerificationReport] = None  # TDD verification report
