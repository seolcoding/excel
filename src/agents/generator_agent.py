"""Generator Agent - Produces HTML/CSS/JS from WebAppPlan."""

from pydantic import BaseModel

from agents import Agent, function_tool

from src.models import WebAppPlan, GeneratedWebApp, GeneratedCode
from src.tools import (
    convert_simple_formula,
    get_helper_functions_js,
    is_simple_formula,
)


class FormulaConversionResult(BaseModel):
    """Result of formula conversion."""
    success: bool
    js_code: str
    requires_llm: bool
    error: str | None = None


class FormulaComplexityResult(BaseModel):
    """Result of formula complexity check."""
    formula: str
    is_simple: bool
    conversion_method: str


@function_tool
def convert_formula(formula: str) -> FormulaConversionResult:
    """
    Convert an Excel formula to JavaScript.

    Args:
        formula: Excel formula string (e.g., "=SUM(A1:A10)")

    Returns:
        FormulaConversionResult with conversion result
    """
    result = convert_simple_formula(formula, {})
    return FormulaConversionResult(
        success=result.success,
        js_code=result.js_code,
        requires_llm=result.requires_llm,
        error=result.error,
    )


@function_tool
def check_formula_complexity(formula: str) -> FormulaComplexityResult:
    """
    Check if a formula can be directly converted or needs LLM.

    Args:
        formula: Excel formula string

    Returns:
        FormulaComplexityResult with complexity assessment
    """
    is_simple = is_simple_formula(formula)
    return FormulaComplexityResult(
        formula=formula,
        is_simple=is_simple,
        conversion_method="direct" if is_simple else "llm",
    )


@function_tool
def get_js_helpers() -> str:
    """
    Get JavaScript helper functions for Excel formula conversion.

    These functions should be included in the generated web app
    to support converted formulas.

    Returns:
        JavaScript code with helper functions
    """
    return get_helper_functions_js()


# Agent definition
GENERATOR_INSTRUCTIONS = """You are a web application generator specializing in converting Excel-based calculations to modern web apps.

Given a WebAppPlan, your job is to generate complete, production-ready HTML, CSS, and JavaScript code.

## Input

You will receive a WebAppPlan containing:
- App name and description
- Component specifications (forms, displays, tables)
- JavaScript function specifications
- Cell mappings (input/output)
- Print layout requirements
- Generation notes

## Your Tasks

### 1. Generate HTML Structure

Create semantic HTML5 with:
- Bootstrap 5 grid layout
- Form components with proper labels and validation
- Output display areas
- Print-optimized sections

Structure:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>/* CSS here */</style>
</head>
<body>
    <div class="container py-4" x-data="appData()">
        <!-- Components here -->
    </div>
    <script>/* JavaScript here */</script>
</body>
</html>
```

### 2. Generate CSS Styles

Create styles that:
- Match Excel's visual appearance
- Support Korean typography (Noto Sans KR)
- Include print media queries
- Use CSS custom properties for theming

Print styles must:
- Hide interactive elements (buttons, inputs)
- Match specified paper size and orientation
- Apply correct margins
- Handle page breaks

### 3. Generate JavaScript Logic

Create Alpine.js data and methods:
- Input handlers
- Calculation functions (using formula conversion tool)
- Output formatters
- Print function

Use the convert_formula tool to convert Excel formulas:
- First check complexity with check_formula_complexity
- Simple formulas: use convert_formula tool
- Complex formulas: generate equivalent JS logic

Include the helper functions from get_js_helpers.

### 4. Output Format

Return a GeneratedWebApp object with:
- Complete HTML (single file, everything embedded)
- Separated CSS (for review)
- Separated JS (for review)
- Component breakdown

## Code Quality Guidelines

1. **Korean UI**: All labels, buttons, messages in Korean
2. **Accessibility**: Proper ARIA labels, form associations
3. **Validation**: Client-side validation matching Excel constraints
4. **Formatting**: Numbers with Korean locale (1,234,567원)
5. **Print Perfect**: Output must match Excel print exactly
6. **Mobile Ready**: Responsive design with Bootstrap grid
7. **No Dependencies**: Only Bootstrap CSS, Alpine.js from CDN

## Example Output Structure

```javascript
function appData() {
    return {
        // Input fields
        input1: 0,
        input2: '',

        // Calculated values
        get result1() {
            return this.input1 * 1.1;  // Converted from =A1*1.1
        },

        // Methods
        calculate() {
            // Trigger reactivity
        },

        print() {
            window.print();
        }
    };
}
```

Be meticulous - the generated code must work perfectly on first load.
"""


def create_generator_agent() -> Agent:
    """Create the Generator Agent instance."""
    return Agent(
        name="WebApp Generator",
        instructions=GENERATOR_INSTRUCTIONS,
        tools=[convert_formula, check_formula_complexity, get_js_helpers],
        model="gpt-5.2",  # SOTA model - excels at frontend UI & code generation
        output_type=GeneratedWebApp,  # Structured output
    )


def create_generation_prompt(plan_dict: dict, analysis_dict: dict = None) -> str:
    """
    Create a prompt for the Generator agent.

    Args:
        plan_dict: WebAppPlan as dictionary
        analysis_dict: Optional ExcelAnalysis for additional context

    Returns:
        Prompt string for the generator
    """
    # Extract plan info
    app_name = plan_dict.get("app_name", "웹 앱")
    app_desc = plan_dict.get("app_description", "")
    components = plan_dict.get("components", [])
    functions = plan_dict.get("functions", [])
    input_map = plan_dict.get("input_cell_map", {})
    output_map = plan_dict.get("output_cell_map", {})
    print_layout = plan_dict.get("print_layout", {})

    # Build component descriptions
    component_desc = []
    for comp in components:
        comp_type = comp.get("component_type", "form")
        title = comp.get("title", "")
        form_fields = comp.get("form_fields", [])
        output_fields = comp.get("output_fields", [])

        field_lines = []
        for f in form_fields:
            field_lines.append(
                f"  - {f['label']} ({f['name']}): {f['field_type']}, "
                f"cell={f['source_cell']}, default={f.get('default_value')}"
            )

        output_lines = []
        for o in output_fields:
            output_lines.append(
                f"  - {o['label']} ({o['name']}): {o['format']}, cell={o['source_cell']}"
            )

        component_desc.append(f"""
### {title} ({comp_type})
Input Fields:
{chr(10).join(field_lines) if field_lines else '  (none)'}

Output Fields:
{chr(10).join(output_lines) if output_lines else '  (none)'}
""")

    # Build function descriptions
    func_desc = []
    for fn in functions:
        func_desc.append(
            f"- {fn['name']}({', '.join(fn['parameters'])}): {fn['description']}"
        )
        if fn.get("source_formula"):
            func_desc.append(f"  Excel: {fn['source_formula']}")

    # Build cell mapping
    cell_mapping = "Input Cell Map:\n"
    for name, cell in input_map.items():
        cell_mapping += f"  {name} → {cell}\n"
    cell_mapping += "\nOutput Cell Map:\n"
    for name, cell in output_map.items():
        cell_mapping += f"  {name} → {cell}\n"

    # Print layout
    print_info = f"""
Paper: {print_layout.get('paper_size', 'A4')}
Orientation: {print_layout.get('orientation', 'portrait')}
Margins: {print_layout.get('margins', {})}
"""

    # Original formulas from analysis (if provided)
    formulas_section = ""
    if analysis_dict:
        sheets = analysis_dict.get("sheets", [])
        formulas_section = "\n## Original Excel Formulas\n"
        for sheet in sheets:
            formulas = sheet.get("formulas", [])
            if formulas:
                formulas_section += f"\n### {sheet['name']}\n"
                for f in formulas[:20]:  # Limit to first 20
                    formulas_section += f"- {f['cell']}: {f['formula']}\n"
                if len(formulas) > 20:
                    formulas_section += f"  ... and {len(formulas) - 20} more\n"

    return f"""# Web App Generation Request

## App Information
- Name: {app_name}
- Description: {app_desc}

## Components
{''.join(component_desc)}

## JavaScript Functions to Implement
{chr(10).join(func_desc) if func_desc else '(none specified)'}

## Cell Mappings
{cell_mapping}

## Print Layout
{print_info}

## Generation Notes
HTML: {plan_dict.get('html_structure_notes', '')}
CSS: {plan_dict.get('css_style_notes', '')}
JS: {plan_dict.get('js_logic_notes', '')}
{formulas_section}

Generate a complete, working web application following the plan above.
Use the convert_formula tool to convert Excel formulas to JavaScript.
Include the helper functions from get_js_helpers in your output.
"""


def generate_html_template(plan: WebAppPlan) -> str:
    """
    Generate a basic HTML template from a WebAppPlan.
    This is a fallback/utility function for simple cases.

    Args:
        plan: WebAppPlan object

    Returns:
        HTML string
    """
    # Build form fields HTML
    form_fields_html = []
    for comp in plan.components:
        for field in comp.form_fields:
            field_id = field.name.replace(" ", "_").lower()
            input_type = _get_html_input_type(field.field_type)
            default = field.default_value if field.default_value else ""

            form_fields_html.append(f"""
            <div class="mb-3">
                <label for="{field_id}" class="form-label">{field.label}</label>
                <input type="{input_type}" class="form-control" id="{field_id}"
                       x-model="{field.name}" value="{default}"
                       {'required' if field.required else ''}>
            </div>
            """)

    # Build output fields HTML
    output_fields_html = []
    for comp in plan.components:
        for output in comp.output_fields:
            output_id = output.name.replace(" ", "_").lower()
            format_filter = _get_format_filter(output.format)

            output_fields_html.append(f"""
            <div class="mb-3">
                <label class="form-label">{output.label}</label>
                <div class="form-control-plaintext border rounded p-2"
                     x-text="{format_filter}({output.name})">
                </div>
            </div>
            """)

    # Build print CSS
    print_css = _generate_print_css(plan.print_layout)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan.app_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        body {{
            font-family: 'Noto Sans KR', sans-serif;
        }}
        .result-card {{
            background: #f8f9fa;
            border-left: 4px solid #0d6efd;
        }}
        {print_css}
    </style>
</head>
<body>
    <div class="container py-4" x-data="appData()">
        <h1 class="mb-4">{plan.app_name}</h1>
        <p class="text-muted mb-4">{plan.app_description}</p>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">입력</h5>
                    </div>
                    <div class="card-body">
                        {''.join(form_fields_html)}
                        <button class="btn btn-primary" @click="calculate()">계산</button>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card result-card">
                    <div class="card-header">
                        <h5 class="mb-0">결과</h5>
                    </div>
                    <div class="card-body">
                        {''.join(output_fields_html)}
                        <button class="btn btn-outline-secondary mt-3 no-print" @click="print()">
                            인쇄
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
{get_helper_functions_js()}

function appData() {{
    return {{
        // Input fields - to be populated

        // Output fields - to be calculated

        calculate() {{
            // Calculation logic - to be implemented
        }},

        print() {{
            window.print();
        }}
    }};
}}
    </script>
</body>
</html>
"""


def _get_html_input_type(field_type: str) -> str:
    """Convert field type to HTML input type."""
    type_map = {
        "text": "text",
        "number": "number",
        "date": "date",
        "select": "text",  # Will be replaced with select element
        "checkbox": "checkbox",
    }
    return type_map.get(field_type, "text")


def _get_format_filter(format_type: str) -> str:
    """Get the JavaScript format function name."""
    format_map = {
        "text": "",
        "number": "formatNumber",
        "currency": "formatCurrency",
        "percentage": "formatPercent",
        "date": "",
    }
    return format_map.get(format_type, "")


def _generate_print_css(print_layout) -> str:
    """Generate CSS for print media."""
    if isinstance(print_layout, dict):
        paper = print_layout.get("paper_size", "A4")
        orientation = print_layout.get("orientation", "portrait")
        margins = print_layout.get("margins", {})
    else:
        paper = print_layout.paper_size
        orientation = print_layout.orientation
        margins = print_layout.margins

    margin_top = margins.get("top", "20mm")
    margin_right = margins.get("right", "15mm")
    margin_bottom = margins.get("bottom", "20mm")
    margin_left = margins.get("left", "15mm")

    return f"""
        @media print {{
            @page {{
                size: {paper} {orientation};
                margin: {margin_top} {margin_right} {margin_bottom} {margin_left};
            }}
            .no-print {{
                display: none !important;
            }}
            .card {{
                border: none !important;
                box-shadow: none !important;
            }}
            body {{
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}
        }}
    """
