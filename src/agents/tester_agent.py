"""Tester Agent - LLM-as-a-Judge pattern for evaluating generated code."""

from typing import Literal
from pydantic import BaseModel, Field

from agents import Agent, AgentOutputSchema, function_tool


class TestCase(BaseModel):
    """A single test case for validation."""
    name: str
    description: str
    input_values: dict[str, str | int | float]
    expected_output: dict[str, str | int | float]
    test_type: Literal["formula", "structure", "print_layout", "input_output"]


class TestEvaluation(BaseModel):
    """Structured evaluation result from the Tester Agent."""
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
        description="Specific, actionable feedback for improvement"
    )
    suggested_fixes: list[str] = Field(
        default_factory=list,
        description="Concrete code fixes or changes to make"
    )


@function_tool
def validate_html_structure(html: str) -> dict:
    """
    Validate HTML structure and return issues.

    Args:
        html: HTML code to validate

    Returns:
        Dict with 'valid' boolean and 'issues' list
    """
    issues = []

    # Check DOCTYPE
    if "<!DOCTYPE html>" not in html and "<!doctype html>" not in html:
        issues.append("Missing DOCTYPE declaration")

    # Check required tags
    required_tags = ["<html", "<head>", "<body>", "</html>", "</head>", "</body>"]
    for tag in required_tags:
        if tag not in html:
            issues.append(f"Missing {tag} tag")

    # Check for Bootstrap
    if "bootstrap" not in html.lower():
        issues.append("Bootstrap CSS not included")

    # Check for Alpine.js
    if "alpine" not in html.lower():
        issues.append("Alpine.js not included")

    # Check balanced tags
    tag_pairs = [("div", "div"), ("script", "script"), ("style", "style")]
    for open_tag, close_tag in tag_pairs:
        open_count = html.lower().count(f"<{open_tag}")
        close_count = html.lower().count(f"</{close_tag}>")
        if open_count != close_count:
            issues.append(f"Unbalanced <{open_tag}> tags: {open_count} open, {close_count} close")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


@function_tool
def validate_javascript_syntax(js_code: str) -> dict:
    """
    Validate JavaScript syntax and return issues.

    Args:
        js_code: JavaScript code to validate

    Returns:
        Dict with 'valid' boolean and 'issues' list
    """
    issues = []

    # Check balanced braces
    if js_code.count("{") != js_code.count("}"):
        issues.append(f"Unbalanced curly braces: {js_code.count('{')} open, {js_code.count('}')} close")

    # Check balanced parentheses
    if js_code.count("(") != js_code.count(")"):
        issues.append(f"Unbalanced parentheses: {js_code.count('(')} open, {js_code.count(')')} close")

    # Check balanced brackets
    if js_code.count("[") != js_code.count("]"):
        issues.append(f"Unbalanced brackets: {js_code.count('[')} open, {js_code.count(']')} close")

    # Check for appData function (Alpine.js data)
    if "appData" not in js_code and "function" not in js_code:
        issues.append("Missing appData() or main function definition")

    # Check for common errors
    if "undefined" in js_code.lower() and "=== undefined" not in js_code:
        # This might be intentional, just a warning
        pass

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


@function_tool
def validate_print_styles(css_or_html: str) -> dict:
    """
    Validate print media query styles.

    Args:
        css_or_html: CSS code or HTML with embedded styles

    Returns:
        Dict with 'valid' boolean and 'issues' list
    """
    issues = []

    # Check for print media query
    if "@media print" not in css_or_html:
        issues.append("Missing @media print media query for print styles")

    # Check for @page rule
    if "@page" not in css_or_html:
        issues.append("Missing @page rule for page size/margins")

    # Check for no-print class
    if "no-print" not in css_or_html and ".no-print" not in css_or_html:
        issues.append("Missing .no-print class to hide interactive elements when printing")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


@function_tool
def validate_korean_ui(html: str) -> dict:
    """
    Validate that UI labels are in Korean.

    Args:
        html: HTML code to check

    Returns:
        Dict with 'valid' boolean and 'issues' list
    """
    issues = []

    # Check for Korean characters (Hangul range: AC00-D7A3)
    has_korean = any(
        ord(char) >= 0xAC00 and ord(char) <= 0xD7A3
        for char in html
    )

    if not has_korean:
        issues.append("No Korean text found in UI labels")

    # Check for common Korean UI elements
    korean_keywords = ["계산", "입력", "결과", "인쇄", "저장"]
    found_keywords = [kw for kw in korean_keywords if kw in html]

    if len(found_keywords) < 2:
        issues.append(f"Only found {len(found_keywords)} Korean UI keywords. Expected more Korean labels.")

    # Check for Noto Sans KR font
    if "Noto Sans KR" not in html and "noto-sans-kr" not in html.lower():
        issues.append("Noto Sans KR font not included for proper Korean typography")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "korean_keywords_found": found_keywords,
    }


@function_tool
def check_formula_implementation(
    js_code: str,
    formula_list: str,
) -> dict:
    """
    Check if Excel formulas are properly implemented in JavaScript.

    Args:
        js_code: Generated JavaScript code
        formula_list: JSON string of formula list, each with 'cell' and 'formula' keys

    Returns:
        Dict with implementation status for each formula
    """
    import json as json_module

    try:
        formulas = json_module.loads(formula_list)
    except (json_module.JSONDecodeError, TypeError):
        # If not valid JSON, try to parse as simple format
        formulas = []

    results = []

    for formula_info in formulas[:10]:  # Check first 10
        cell = formula_info.get("cell", "") if isinstance(formula_info, dict) else ""
        formula = formula_info.get("formula", "") if isinstance(formula_info, dict) else ""

        # Check if formula logic appears to be implemented
        # Look for related function names or calculations
        formula_lower = formula.lower()

        implemented = False
        reason = "Not found in generated code"

        # Check for SUM
        if "sum(" in formula_lower:
            if "reduce" in js_code or ".sum" in js_code or "+ " in js_code:
                implemented = True
                reason = "SUM logic found"

        # Check for IF
        elif "if(" in formula_lower:
            if "?" in js_code or "if " in js_code.lower() or "if(" in js_code.lower():
                implemented = True
                reason = "IF logic found"

        # Check for VLOOKUP
        elif "vlookup(" in formula_lower:
            if "find" in js_code.lower() or "filter" in js_code.lower() or "lookup" in js_code.lower():
                implemented = True
                reason = "VLOOKUP logic found"

        # Check for basic arithmetic
        elif any(op in formula for op in ["+", "-", "*", "/"]):
            if any(op in js_code for op in ["+", "-", "*", "/"]):
                implemented = True
                reason = "Arithmetic operations found"

        # Generic check - look for cell reference pattern
        else:
            # Just check if there's some calculation logic
            if "return" in js_code and ("+" in js_code or "*" in js_code or "get" in js_code):
                implemented = True
                reason = "Calculation logic present"

        results.append({
            "cell": cell,
            "formula": formula[:50] + "..." if len(formula) > 50 else formula,
            "implemented": implemented,
            "reason": reason,
        })

    implemented_count = sum(1 for r in results if r["implemented"])

    return {
        "total_checked": len(results),
        "implemented": implemented_count,
        "not_implemented": len(results) - implemented_count,
        "implementation_rate": implemented_count / len(results) if results else 0,
        "details": results,
    }


# Agent Instructions
TESTER_INSTRUCTIONS = """You are a code quality evaluator specializing in Excel-to-WebApp conversions.

Your job is to thoroughly evaluate generated HTML/CSS/JS code and provide structured feedback.

## Evaluation Process

1. **Validate Structure** - Use validate_html_structure tool
2. **Check JavaScript** - Use validate_javascript_syntax tool
3. **Verify Print Styles** - Use validate_print_styles tool
4. **Check Korean UI** - Use validate_korean_ui tool
5. **Formula Implementation** - Use check_formula_implementation tool

## Scoring Criteria

**PASS** (score: "pass"):
- All structural validations pass
- JavaScript syntax is valid
- Print styles are properly configured
- Korean UI labels are present
- At least 80% of formulas are implemented

**NEEDS IMPROVEMENT** (score: "needs_improvement"):
- Minor issues that can be fixed in the next iteration
- 50-80% of formulas implemented
- Some missing but non-critical features

**FAIL** (score: "fail"):
- Critical structural errors
- JavaScript syntax errors that would prevent execution
- Less than 50% of formulas implemented
- Missing core functionality

## Feedback Requirements

When providing feedback:
1. Be SPECIFIC - point to exact lines or sections
2. Be ACTIONABLE - explain exactly what to fix
3. PRIORITIZE - list most important fixes first
4. Include CODE EXAMPLES when helpful

Example good feedback:
"The calculate() function is missing the tax calculation. Add: `this.tax = this.subtotal * 0.1;` after line where subtotal is calculated."

Example bad feedback:
"The code has some issues with calculations."

## Output Format

Return a TestEvaluation with:
- score: "pass", "needs_improvement", or "fail"
- pass_rate: float from 0.0 to 1.0
- passed_tests: list of test names that passed
- failed_tests: list of test names that failed
- issues: detailed list of each issue
- feedback: comprehensive feedback paragraph
- suggested_fixes: specific code changes to make

Be thorough but fair. After 3-5 improvement iterations, if the code is "good enough" for practical use, give it a "pass".
"""


def create_tester_agent() -> Agent:
    """Create the Tester Agent instance."""
    return Agent(
        name="Code Tester",
        instructions=TESTER_INSTRUCTIONS,
        tools=[
            validate_html_structure,
            validate_javascript_syntax,
            validate_print_styles,
            validate_korean_ui,
            check_formula_implementation,
        ],
        model="gpt-4o-mini",  # Cost-optimized for evaluation
        output_type=AgentOutputSchema(TestEvaluation, strict_json_schema=False),
    )


def create_test_prompt(
    html: str,
    css: str,
    js: str,
    formulas: list[dict],
    iteration: int = 1,
) -> str:
    """
    Create a prompt for the Tester agent.

    Args:
        html: Generated HTML code
        css: Generated CSS code
        js: Generated JavaScript code
        formulas: List of Excel formulas to verify
        iteration: Current iteration number

    Returns:
        Prompt string for the tester
    """
    return f"""# Code Evaluation Request (Iteration {iteration})

Evaluate the following generated web application code.

## Generated HTML
```html
{html[:8000]}
{"... [truncated]" if len(html) > 8000 else ""}
```

## Generated CSS
```css
{css[:3000]}
{"... [truncated]" if len(css) > 3000 else ""}
```

## Generated JavaScript
```javascript
{js[:5000]}
{"... [truncated]" if len(js) > 5000 else ""}
```

## Excel Formulas to Verify
{chr(10).join([f"- {f['cell']}: {f['formula']}" for f in formulas[:15]])}
{"... and more" if len(formulas) > 15 else ""}

## Evaluation Instructions

1. Run all validation tools
2. Check formula implementation
3. Assess overall code quality
4. Provide specific, actionable feedback

{"Note: This is iteration " + str(iteration) + ". Be lenient if code is functional but not perfect." if iteration >= 3 else ""}

Return a structured TestEvaluation with your findings.
"""
