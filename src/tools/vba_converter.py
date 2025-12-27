"""VBA to JavaScript converter using LLM assistance."""

import re
from dataclasses import dataclass
from typing import Optional

from src.models import VBAModule


@dataclass
class VBAConversionResult:
    """Result of VBA to JavaScript conversion."""
    success: bool
    js_code: str
    error: Optional[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class VBAConversionError(Exception):
    """Raised when VBA conversion fails."""
    pass


# Patterns that indicate complex VBA that may not convert well
UNSUPPORTED_PATTERNS = [
    r"\bCreateObject\s*\(",
    r"\bActiveX",
    r"\bApplication\.Run\b",
    r"\bShell\s*\(",
    r"\bMkDir\b",
    r"\bOpen\s+.*\s+For\s+",
    r"\bFileSystemObject\b",
    r"\bWScript\b",
    r"\bADODB\b",
    r"\bDAO\b",
]


def check_vba_convertibility(vba_code: str) -> tuple[bool, list[str]]:
    """
    Check if VBA code can be converted to JavaScript.

    Args:
        vba_code: VBA source code

    Returns:
        Tuple of (is_convertible, list of issues)
    """
    issues = []

    for pattern in UNSUPPORTED_PATTERNS:
        if re.search(pattern, vba_code, re.IGNORECASE):
            issues.append(f"Unsupported pattern: {pattern}")

    # Check for external references
    if re.search(r"Workbooks\s*\(", vba_code, re.IGNORECASE):
        issues.append("External workbook references are not supported")

    # Check for UserForms
    if re.search(r"UserForm", vba_code, re.IGNORECASE):
        issues.append("UserForms are not supported - will need manual UI creation")

    return len(issues) == 0, issues


def parse_vba_structure(vba_module: VBAModule) -> dict:
    """
    Parse VBA code structure for LLM context.

    Args:
        vba_module: VBA module to parse

    Returns:
        Structured information about the VBA code
    """
    code = vba_module.code

    # Extract procedures
    procedures = []
    proc_pattern = r"(?:Public\s+|Private\s+)?(Sub|Function)\s+(\w+)\s*\(([^)]*)\)"

    for match in re.finditer(proc_pattern, code, re.IGNORECASE):
        proc_type = match.group(1)
        proc_name = match.group(2)
        params = match.group(3).strip()

        # Find procedure body
        start = match.end()
        end_pattern = rf"End\s+{proc_type}"
        end_match = re.search(end_pattern, code[start:], re.IGNORECASE)

        if end_match:
            body = code[start:start + end_match.start()].strip()
        else:
            body = ""

        procedures.append({
            "type": proc_type.lower(),
            "name": proc_name,
            "params": _parse_params(params),
            "body": body,
        })

    # Extract global variables
    variables = []
    var_pattern = r"(?:Dim|Public|Private)\s+(\w+)\s+As\s+(\w+)"

    for match in re.finditer(var_pattern, code, re.IGNORECASE):
        variables.append({
            "name": match.group(1),
            "type": match.group(2),
        })

    # Extract cell references
    cell_refs = set()
    range_pattern = r'Range\s*\(\s*["\']([^"\']+)["\']\s*\)'
    cells_pattern = r'Cells\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)'

    for match in re.finditer(range_pattern, code, re.IGNORECASE):
        cell_refs.add(match.group(1))

    for match in re.finditer(cells_pattern, code, re.IGNORECASE):
        row, col = int(match.group(1)), int(match.group(2))
        cell_refs.add(f"R{row}C{col}")

    return {
        "module_name": vba_module.name,
        "module_type": vba_module.module_type,
        "procedures": procedures,
        "variables": variables,
        "cell_references": list(cell_refs),
    }


def _parse_params(params_str: str) -> list[dict]:
    """Parse VBA parameter string into structured format."""
    if not params_str:
        return []

    params = []
    for param in params_str.split(","):
        param = param.strip()
        if not param:
            continue

        # Parse "ByVal/ByRef name As Type" or "name As Type" or just "name"
        match = re.match(r"(?:ByVal\s+|ByRef\s+)?(\w+)(?:\s+As\s+(\w+))?", param, re.IGNORECASE)
        if match:
            params.append({
                "name": match.group(1),
                "type": match.group(2) or "Variant",
            })

    return params


def generate_llm_prompt(vba_structure: dict, context: str = "") -> str:
    """
    Generate a prompt for LLM to convert VBA to JavaScript.

    Args:
        vba_structure: Parsed VBA structure from parse_vba_structure
        context: Additional context about the Excel file

    Returns:
        Prompt string for LLM
    """
    procedures_desc = []
    for proc in vba_structure["procedures"]:
        params = ", ".join([f"{p['name']}: {p['type']}" for p in proc["params"]])
        procedures_desc.append(f"- {proc['type']} {proc['name']}({params})")

    cell_refs = ", ".join(vba_structure["cell_references"][:20])

    return f'''Convert the following VBA code to JavaScript for a web application.

## VBA Module: {vba_structure["module_name"]} ({vba_structure["module_type"]})

## Procedures to convert:
{chr(10).join(procedures_desc)}

## Cell references used:
{cell_refs}

## Conversion rules:
1. Range("A1").Value → document.getElementById('cell-A1').value or data['A1']
2. MsgBox → alert()
3. InputBox → prompt() or HTML input field
4. Sub → function (no return)
5. Function → function (with return)
6. Dim x As Integer → let x = 0
7. For i = 1 To 10 → for (let i = 1; i <= 10; i++)
8. If...Then...Else → if...else
9. Select Case → switch
10. Worksheets("Sheet1") → ignore (single page app)

## Additional context:
{context}

## Requirements:
- Generate clean, modern JavaScript (ES6+)
- Use const/let, arrow functions where appropriate
- Handle errors gracefully
- Add comments for complex logic
- Preserve the original function names
- Make sure the logic is equivalent to VBA

Generate the JavaScript code:
'''


def simple_vba_to_js(vba_code: str) -> str:
    """
    Perform simple VBA to JavaScript conversion for basic patterns.
    This is used for simple macros before falling back to LLM.

    Args:
        vba_code: VBA source code

    Returns:
        Partially converted JavaScript code
    """
    js = vba_code

    # Basic replacements
    replacements = [
        # Comments
        (r"'(.*)$", r"// \1"),

        # Variable declarations
        (r"\bDim\s+(\w+)\s+As\s+(?:Integer|Long|Double|Single)", r"let \1 = 0"),
        (r"\bDim\s+(\w+)\s+As\s+String", r'let \1 = ""'),
        (r"\bDim\s+(\w+)\s+As\s+Boolean", r"let \1 = false"),
        (r"\bDim\s+(\w+)\s+As\s+Date", r"let \1 = new Date()"),
        (r"\bDim\s+(\w+)\s+As\s+Variant", r"let \1 = null"),
        (r"\bDim\s+(\w+)", r"let \1"),

        # Control structures
        (r"\bEnd\s+Sub\b", "}"),
        (r"\bEnd\s+Function\b", "}"),
        (r"\bEnd\s+If\b", "}"),
        (r"\bThen\b", ") {"),
        (r"\bElseIf\s+", "} else if ("),
        (r"\bElse\b", "} else {"),
        (r"\bIf\s+", "if ("),

        # Loops
        (r"\bFor\s+(\w+)\s*=\s*(\d+)\s+To\s+(\d+)", r"for (let \1 = \2; \1 <= \3; \1++)"),
        (r"\bNext\s+\w*", "}"),
        (r"\bDo\s+While\s+", "while ("),
        (r"\bLoop\b", "}"),
        (r"\bWend\b", "}"),

        # Operators
        (r"\bAnd\b", "&&"),
        (r"\bOr\b", "||"),
        (r"\bNot\b", "!"),
        (r"\bMod\b", "%"),
        (r"\s*&\s*", " + "),
        (r"<>", "!=="),

        # Common functions
        (r"\bMsgBox\s*\(?\s*([^)\n]+)\s*\)?", r"alert(\1)"),
        (r"\bCInt\s*\(", "parseInt("),
        (r"\bCDbl\s*\(", "parseFloat("),
        (r"\bCStr\s*\(", "String("),
        (r"\bLen\s*\(", "String(\1).length"),
        (r"\bUCase\s*\(", "String(\1).toUpperCase("),
        (r"\bLCase\s*\(", "String(\1).toLowerCase("),
        (r"\bTrim\s*\(", "String(\1).trim("),

        # Range access
        (r'Range\s*\(\s*"([^"]+)"\s*\)\.Value', r"data['\1']"),
        (r'Range\s*\(\s*"([^"]+)"\s*\)', r"data['\1']"),

        # Sub/Function
        (r"\bPublic\s+Sub\s+(\w+)\s*\(([^)]*)\)", r"function \1(\2) {"),
        (r"\bPrivate\s+Sub\s+(\w+)\s*\(([^)]*)\)", r"function \1(\2) {"),
        (r"\bSub\s+(\w+)\s*\(([^)]*)\)", r"function \1(\2) {"),
        (r"\bPublic\s+Function\s+(\w+)\s*\(([^)]*)\)\s*As\s+\w+", r"function \1(\2) {"),
        (r"\bPrivate\s+Function\s+(\w+)\s*\(([^)]*)\)\s*As\s+\w+", r"function \1(\2) {"),
        (r"\bFunction\s+(\w+)\s*\(([^)]*)\)\s*As\s+\w+", r"function \1(\2) {"),

        # Exit statements
        (r"\bExit\s+Sub\b", "return"),
        (r"\bExit\s+Function\b", "return"),
        (r"\bExit\s+For\b", "break"),
    ]

    for pattern, replacement in replacements:
        js = re.sub(pattern, replacement, js, flags=re.IGNORECASE | re.MULTILINE)

    return js


def validate_converted_js(js_code: str) -> tuple[bool, list[str]]:
    """
    Basic validation of converted JavaScript code.

    Args:
        js_code: JavaScript code to validate

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    # Check for balanced braces
    open_braces = js_code.count("{")
    close_braces = js_code.count("}")
    if open_braces != close_braces:
        issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

    # Check for balanced parentheses
    open_parens = js_code.count("(")
    close_parens = js_code.count(")")
    if open_parens != close_parens:
        issues.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")

    # Check for common VBA leftovers
    vba_remnants = [
        (r"\bEnd\s+Sub\b", "VBA 'End Sub' not converted"),
        (r"\bEnd\s+If\b", "VBA 'End If' not converted"),
        (r"\bDim\s+", "VBA 'Dim' not converted"),
        (r"\bThen\b(?!\s*{)", "VBA 'Then' not converted"),
    ]

    for pattern, msg in vba_remnants:
        if re.search(pattern, js_code, re.IGNORECASE):
            issues.append(msg)

    return len(issues) == 0, issues
