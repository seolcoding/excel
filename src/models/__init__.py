"""Data models for xls_agent."""

from .analysis import (
    CellInfo,
    FormulaInfo,
    VBAModule,
    SheetInfo,
    PrintSettings,
    ExcelAnalysis,
)
from .plan import (
    FormField,
    OutputField,
    ComponentSpec,
    JavaScriptFunction,
    PrintLayout,
    WebAppPlan,
)
from .output import (
    TestStatus,
    TestResult,
    TestSuite,
    TestEvaluation,
    GeneratedCode,
    GeneratedWebApp,
    ImprovementFeedback,
    ConversionResult,
)
from .test_case import (
    CellValue,
    FormulaTestCase,
    InputOutputMapping,
    TestScenario,
    StaticTestSuite,
    TestExecutionResult,
    StaticTestResult,
)

__all__ = [
    # Analysis models
    "CellInfo",
    "FormulaInfo",
    "VBAModule",
    "SheetInfo",
    "PrintSettings",
    "ExcelAnalysis",
    # Plan models
    "FormField",
    "OutputField",
    "ComponentSpec",
    "JavaScriptFunction",
    "PrintLayout",
    "WebAppPlan",
    # Output models
    "TestStatus",
    "TestResult",
    "TestSuite",
    "TestEvaluation",
    "GeneratedCode",
    "GeneratedWebApp",
    "ImprovementFeedback",
    "ConversionResult",
    # Test case models
    "CellValue",
    "FormulaTestCase",
    "InputOutputMapping",
    "TestScenario",
    "StaticTestSuite",
    "TestExecutionResult",
    "StaticTestResult",
]
