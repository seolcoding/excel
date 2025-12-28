"""Test helper functions for creating mock responses.

Based on OpenAI Agents SDK testing patterns.
Reference: refs/openai-agents-python/tests/test_responses.py
"""

from __future__ import annotations

import json
from typing import Any

from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputItem,
    ResponseOutputMessage,
    ResponseOutputText,
)

from agents import (
    Agent,
    FunctionTool,
    Handoff,
    TResponseInputItem,
    default_tool_error_function,
    function_tool,
)


# ============================================
# Input Item Helpers
# ============================================

def get_text_input_item(content: str) -> TResponseInputItem:
    """Create a user text input item."""
    return {
        "content": content,
        "role": "user",
    }


def get_system_input_item(content: str) -> TResponseInputItem:
    """Create a system input item."""
    return {
        "content": content,
        "role": "system",
    }


# ============================================
# Output Item Helpers
# ============================================

def get_text_message(content: str, id: str = "msg-1") -> ResponseOutputItem:
    """Create a text message response from assistant."""
    return ResponseOutputMessage(
        id=id,
        type="message",
        role="assistant",
        content=[ResponseOutputText(text=content, type="output_text", annotations=[], logprobs=[])],
        status="completed",
    )


def get_json_message(data: dict, id: str = "msg-1") -> ResponseOutputItem:
    """Create a JSON message response (for structured output)."""
    return ResponseOutputMessage(
        id=id,
        type="message",
        role="assistant",
        content=[ResponseOutputText(
            text=json.dumps(data),
            type="output_text",
            annotations=[],
            logprobs=[],
        )],
        status="completed",
    )


def get_function_tool_call(
    name: str,
    arguments: str | dict | None = None,
    call_id: str | None = None,
    id: str = "tc-1",
) -> ResponseOutputItem:
    """Create a function tool call response."""
    if isinstance(arguments, dict):
        arguments = json.dumps(arguments)
    return ResponseFunctionToolCall(
        id=id,
        call_id=call_id or "call-1",
        type="function_call",
        name=name,
        arguments=arguments or "",
    )


def get_handoff_tool_call(
    to_agent: Agent[Any],
    override_name: str | None = None,
    args: str | None = None,
) -> ResponseOutputItem:
    """Create a handoff tool call response."""
    name = override_name or Handoff.default_tool_name(to_agent)
    return get_function_tool_call(name, args)


# ============================================
# Tool Helpers
# ============================================

def get_function_tool(
    name: str | None = None,
    return_value: str | None = None,
    hide_errors: bool = False,
) -> FunctionTool:
    """Create a simple function tool for testing."""
    def _func() -> str:
        return return_value or "result_ok"

    return function_tool(
        _func,
        name_override=name,
        failure_error_function=None if hide_errors else default_tool_error_function,
    )


def get_async_function_tool(
    name: str | None = None,
    return_value: str | None = None,
) -> FunctionTool:
    """Create an async function tool for testing."""
    async def _func() -> str:
        return return_value or "result_ok"

    return function_tool(
        _func,
        name_override=name,
    )


# ============================================
# Structured Output Helpers
# ============================================

def get_webapp_spec_output() -> dict:
    """Create a sample WebAppSpec output for testing."""
    return {
        "app_name": "테스트 앱",
        "app_description": "테스트용 앱입니다",
        "input_fields": [
            {
                "name": "salary",
                "type": "number",
                "label": "급여",
                "source_cell": "B3",
                "validation": {"required": True, "min": 0},
            }
        ],
        "output_fields": [
            {
                "name": "tax",
                "format": "currency",
                "label": "세금",
                "source_cell": "B10",
                "source_formula": "=B3*0.1",
            }
        ],
        "calculations": [
            {
                "name": "calculate_tax",
                "inputs": ["salary"],
                "output": "tax",
                "formula": "=B3*0.1",
                "expected_logic": "Tax is 10% of salary",
            }
        ],
        "expected_behaviors": [
            "Salary 5000000 → Tax 500000",
            "Zero salary → Tax 0",
        ],
        "boundary_conditions": [
            {
                "name": "zero_salary",
                "inputs": {"salary": 0},
                "expected_output": {"tax": 0},
                "description": "Zero salary produces zero tax",
            }
        ],
        "korean_labels": True,
        "print_layout": {
            "paper_size": "A4",
            "orientation": "portrait",
            "margins": {"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
        },
    }


def get_generated_webapp_output() -> dict:
    """Create a sample GeneratedWebApp output for testing."""
    return {
        "app_name": "테스트 앱",
        "source_excel": "test.xlsx",
        "html": """<!DOCTYPE html>
<html lang="ko">
<head><title>테스트</title></head>
<body>
<div x-data="appData()">
    <input type="number" x-model="salary" id="salary">
    <button @click="calculate()">계산</button>
    <div id="tax" x-text="tax"></div>
</div>
<script>
function appData() {
    return {
        salary: 0,
        get tax() { return this.salary * 0.1; },
        calculate() {}
    };
}
</script>
</body>
</html>""",
        "css": "@media print { .no-print { display: none; } }",
        "js": "function appData() { return { salary: 0, get tax() { return this.salary * 0.1; } }; }",
        "components": [],
        "generation_iteration": 1,
    }


def get_test_evaluation_output(passed: bool = True) -> dict:
    """Create a sample TestEvaluation output for testing."""
    if passed:
        return {
            "score": "pass",
            "pass_rate": 0.95,
            "passed_tests": ["HTML Structure", "Korean Labels", "Print Styles", "JavaScript Logic"],
            "failed_tests": [],
            "issues": [],
            "feedback": "All tests passed successfully.",
            "suggested_fixes": [],
        }
    else:
        return {
            "score": "needs_improvement",
            "pass_rate": 0.6,
            "passed_tests": ["HTML Structure", "Korean Labels"],
            "failed_tests": ["Print Styles", "JavaScript Logic"],
            "issues": ["Missing @media print", "Calculation error in tax function"],
            "feedback": "Fix print styles and calculation logic.",
            "suggested_fixes": [
                "Add @media print CSS",
                "Fix tax calculation: use this.salary * 0.1",
            ],
        }


# ============================================
# Analysis Helpers
# ============================================

def get_excel_analysis_output() -> dict:
    """Create a sample ExcelAnalysis output for testing."""
    return {
        "filename": "test_workbook.xlsx",
        "sheets": [
            {
                "name": "Sheet1",
                "row_count": 20,
                "col_count": 10,
                "used_range": "A1:J20",
                "input_cells": ["B3", "B4", "B5"],
                "output_cells": ["B10", "B11", "B12"],
                "formulas": [
                    {
                        "cell": "B10",
                        "formula": "=B3*0.1",
                        "dependencies": ["B3"],
                    }
                ],
                "merged_ranges": [],
                "data_validations": [],
            }
        ],
        "has_vba": False,
        "vba_modules": [],
        "complexity_score": "low",
    }
