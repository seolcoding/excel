"""Excel formula to JavaScript converter with hybrid approach."""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of formula conversion."""
    success: bool
    js_code: str
    requires_llm: bool
    error: Optional[str] = None


# Simple formulas that can be directly converted
SIMPLE_FUNCTIONS = {
    "SUM", "AVERAGE", "MIN", "MAX", "COUNT", "COUNTA",
    "IF", "AND", "OR", "NOT",
    "ROUND", "ROUNDUP", "ROUNDDOWN", "INT", "ABS",
    "LEN", "LEFT", "RIGHT", "MID", "TRIM", "UPPER", "LOWER",
    "CONCATENATE", "CONCAT",
    "TODAY", "NOW",
}

# Complex formulas requiring LLM
COMPLEX_FUNCTIONS = {
    "VLOOKUP", "HLOOKUP", "INDEX", "MATCH", "INDIRECT",
    "SUMIF", "SUMIFS", "COUNTIF", "COUNTIFS", "AVERAGEIF", "AVERAGEIFS",
    "OFFSET", "CHOOSE", "LOOKUP",
    "PMT", "FV", "PV", "NPV", "IRR",
}


def is_simple_formula(formula: str) -> bool:
    """
    Check if a formula can be directly converted to JavaScript.

    Args:
        formula: Excel formula string (e.g., "=SUM(A1:A10)")

    Returns:
        True if the formula can be directly converted
    """
    formula_upper = formula.upper()

    # Check if any complex function is used
    for func in COMPLEX_FUNCTIONS:
        if func + "(" in formula_upper:
            return False

    # Check if nested functions are too deep (more than 2 levels)
    depth = 0
    max_depth = 0
    for char in formula:
        if char == "(":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ")":
            depth -= 1

    if max_depth > 3:
        return False

    return True


def convert_simple_formula(formula: str, cell_map: dict[str, str] = None) -> ConversionResult:
    """
    Convert a simple Excel formula to JavaScript.

    Args:
        formula: Excel formula string (e.g., "=SUM(A1:A10)")
        cell_map: Optional mapping of cell addresses to JS variable names

    Returns:
        ConversionResult with the JavaScript code
    """
    if not is_simple_formula(formula):
        return ConversionResult(
            success=False,
            js_code="",
            requires_llm=True,
            error="Formula is too complex for direct conversion"
        )

    try:
        # Remove leading = if present
        formula = formula.lstrip("=")

        # Convert to JavaScript
        js_code = _convert_formula_to_js(formula, cell_map or {})

        return ConversionResult(
            success=True,
            js_code=js_code,
            requires_llm=False
        )
    except Exception as e:
        return ConversionResult(
            success=False,
            js_code="",
            requires_llm=True,
            error=str(e)
        )


def _convert_formula_to_js(formula: str, cell_map: dict[str, str]) -> str:
    """Convert an Excel formula to JavaScript expression."""
    result = formula

    # Replace cell references with JS variables
    result = _replace_cell_references(result, cell_map)

    # Replace Excel functions with JS equivalents
    result = _replace_functions(result)

    # Fix operators
    result = result.replace("^", "**")  # Power operator
    result = result.replace("<>", "!==")  # Not equal

    return result


def _replace_cell_references(formula: str, cell_map: dict[str, str]) -> str:
    """Replace Excel cell references with JavaScript variable names."""
    result = formula

    # Find all cell references (e.g., A1, $B$2, Sheet1!C3)
    pattern = r"(?:[\w\s]+!)?\$?([A-Z]+)\$?(\d+)"

    def replace_ref(match):
        col = match.group(1)
        row = match.group(2)
        cell_addr = f"{col}{row}"

        if cell_addr in cell_map:
            return cell_map[cell_addr]

        # Default: use data object with cell address
        return f"data['{cell_addr}']"

    result = re.sub(pattern, replace_ref, result, flags=re.IGNORECASE)
    return result


def _replace_functions(formula: str) -> str:
    """Replace Excel functions with JavaScript equivalents."""
    result = formula

    # SUM - handle ranges
    result = _replace_sum(result)

    # AVERAGE
    result = _replace_average(result)

    # MIN/MAX
    result = re.sub(r"\bMIN\s*\(", "Math.min(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bMAX\s*\(", "Math.max(", result, flags=re.IGNORECASE)

    # COUNT/COUNTA
    result = re.sub(r"\bCOUNT\s*\(", "_count(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bCOUNTA\s*\(", "_counta(", result, flags=re.IGNORECASE)

    # IF statement
    result = _replace_if(result)

    # AND/OR/NOT
    result = re.sub(r"\bAND\s*\(", "_and(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bOR\s*\(", "_or(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bNOT\s*\(", "!", result, flags=re.IGNORECASE)

    # ROUND functions
    result = re.sub(r"\bROUND\s*\(", "_round(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bROUNDUP\s*\(", "_roundUp(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bROUNDDOWN\s*\(", "_roundDown(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bINT\s*\(", "Math.floor(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bABS\s*\(", "Math.abs(", result, flags=re.IGNORECASE)

    # String functions
    result = re.sub(r"\bLEN\s*\(", "_len(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bLEFT\s*\(", "_left(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bRIGHT\s*\(", "_right(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bMID\s*\(", "_mid(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bTRIM\s*\(", "_trim(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bUPPER\s*\(", "_upper(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bLOWER\s*\(", "_lower(", result, flags=re.IGNORECASE)

    # CONCATENATE
    result = re.sub(r"\bCONCATENATE\s*\(", "_concat(", result, flags=re.IGNORECASE)
    result = re.sub(r"\bCONCAT\s*\(", "_concat(", result, flags=re.IGNORECASE)

    # Date functions
    result = re.sub(r"\bTODAY\s*\(\s*\)", "new Date()", result, flags=re.IGNORECASE)
    result = re.sub(r"\bNOW\s*\(\s*\)", "new Date()", result, flags=re.IGNORECASE)

    return result


def _replace_sum(formula: str) -> str:
    """Replace SUM function with JavaScript equivalent."""
    pattern = r"\bSUM\s*\(([^)]+)\)"

    def replace(match):
        args = match.group(1)
        # If it's a range, convert to array sum
        if ":" in args:
            return f"_sumRange({args})"
        else:
            # Multiple args: convert to sum
            return f"_sum({args})"

    return re.sub(pattern, replace, formula, flags=re.IGNORECASE)


def _replace_average(formula: str) -> str:
    """Replace AVERAGE function with JavaScript equivalent."""
    pattern = r"\bAVERAGE\s*\(([^)]+)\)"

    def replace(match):
        args = match.group(1)
        if ":" in args:
            return f"_averageRange({args})"
        else:
            return f"_average({args})"

    return re.sub(pattern, replace, formula, flags=re.IGNORECASE)


def _replace_if(formula: str) -> str:
    """Replace IF function with JavaScript ternary operator."""
    # Simple IF replacement - handles non-nested IF
    pattern = r"\bIF\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)"

    def replace(match):
        condition = match.group(1).strip()
        true_val = match.group(2).strip()
        false_val = match.group(3).strip()
        return f"({condition} ? {true_val} : {false_val})"

    # Apply multiple times for nested IFs
    prev = ""
    result = formula
    while prev != result:
        prev = result
        result = re.sub(pattern, replace, result, flags=re.IGNORECASE)

    return result


def get_helper_functions_js() -> str:
    """
    Get JavaScript helper functions required for formula conversion.

    Returns:
        JavaScript code with all helper functions
    """
    return '''
// Excel formula helper functions
function _sum(...args) {
    return args.flat().reduce((a, b) => (parseFloat(a) || 0) + (parseFloat(b) || 0), 0);
}

function _sumRange(rangeData) {
    if (Array.isArray(rangeData)) {
        return rangeData.flat().reduce((a, b) => (parseFloat(a) || 0) + (parseFloat(b) || 0), 0);
    }
    return parseFloat(rangeData) || 0;
}

function _average(...args) {
    const flat = args.flat().filter(x => x !== null && x !== '' && !isNaN(x));
    return flat.length ? _sum(...flat) / flat.length : 0;
}

function _averageRange(rangeData) {
    if (Array.isArray(rangeData)) {
        const flat = rangeData.flat().filter(x => x !== null && x !== '' && !isNaN(x));
        return flat.length ? _sumRange(flat) / flat.length : 0;
    }
    return parseFloat(rangeData) || 0;
}

function _count(...args) {
    return args.flat().filter(x => typeof x === 'number' && !isNaN(x)).length;
}

function _counta(...args) {
    return args.flat().filter(x => x !== null && x !== '' && x !== undefined).length;
}

function _and(...args) {
    return args.every(x => Boolean(x));
}

function _or(...args) {
    return args.some(x => Boolean(x));
}

function _round(num, digits = 0) {
    const factor = Math.pow(10, digits);
    return Math.round(num * factor) / factor;
}

function _roundUp(num, digits = 0) {
    const factor = Math.pow(10, digits);
    return Math.ceil(num * factor) / factor;
}

function _roundDown(num, digits = 0) {
    const factor = Math.pow(10, digits);
    return Math.floor(num * factor) / factor;
}

function _len(text) {
    return String(text).length;
}

function _left(text, numChars = 1) {
    return String(text).substring(0, numChars);
}

function _right(text, numChars = 1) {
    const str = String(text);
    return str.substring(str.length - numChars);
}

function _mid(text, startNum, numChars) {
    return String(text).substring(startNum - 1, startNum - 1 + numChars);
}

function _trim(text) {
    return String(text).trim();
}

function _upper(text) {
    return String(text).toUpperCase();
}

function _lower(text) {
    return String(text).toLowerCase();
}

function _concat(...args) {
    return args.join('');
}

// Number formatting
function formatNumber(num, decimals = 0) {
    return new Intl.NumberFormat('ko-KR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

function formatCurrency(num) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW',
        maximumFractionDigits: 0
    }).format(num);
}

function formatPercent(num, decimals = 1) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num / 100);
}
'''


def generate_calculation_function(
    formulas: list[dict],
    cell_map: dict[str, str]
) -> str:
    """
    Generate a JavaScript calculate() function from a list of formulas.

    Args:
        formulas: List of formula dicts with 'cell' and 'formula' keys
        cell_map: Mapping of cell addresses to JS variable names

    Returns:
        JavaScript function code
    """
    lines = ["function calculate() {"]

    for f in formulas:
        cell = f["cell"]
        formula = f["formula"]

        result = convert_simple_formula(formula, cell_map)

        if result.success:
            js_expr = result.js_code
            var_name = cell_map.get(cell, f"data['{cell}']")
            lines.append(f"    {var_name} = {js_expr};")
        else:
            # Mark for LLM conversion
            lines.append(f"    // TODO: Complex formula requires LLM conversion")
            lines.append(f"    // Original: {formula}")
            lines.append(f"    // {var_name} = ???;")

    lines.append("}")
    return "\n".join(lines)
