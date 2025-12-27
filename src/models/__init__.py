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
    GeneratedCode,
    GeneratedWebApp,
    ImprovementFeedback,
    ConversionResult,
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
    "GeneratedCode",
    "GeneratedWebApp",
    "ImprovementFeedback",
    "ConversionResult",
]
