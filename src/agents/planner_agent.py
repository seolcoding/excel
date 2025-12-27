"""Planner Agent - Designs web app structure from Excel analysis."""

from agents import Agent, AgentOutputSchema

from src.models import WebAppPlan


# Agent definition (no tools - pure LLM reasoning)
PLANNER_INSTRUCTIONS = """You are a web application architect specializing in converting Excel tools to web apps.

Given an Excel file analysis, your job is to design a complete web application plan.

## Input

You will receive an ExcelAnalysis object containing:
- Sheet information (names, dimensions, formulas)
- Input cells (where users enter data)
- Output cells (where calculations are displayed)
- VBA modules (if any)
- Print settings

## Your Tasks

### 1. Determine App Type
Classify the Excel file as one of:
- **Calculator**: Input fields → calculation → result display
- **Form/Template**: Fill-in-the-blank document for printing
- **Data Table**: Display/edit tabular data
- **Mixed**: Combination of above

### 2. Design UI Components
For each sheet, determine:
- **Form fields**: For each input cell, specify:
  - Field name (human-readable)
  - Label (Korean, user-friendly)
  - Type (text, number, date, select, checkbox)
  - Default value
  - Validation rules

- **Output fields**: For each output cell, specify:
  - Field name
  - Label
  - Display format (text, number, currency, percentage)
  - Calculation description

### 3. Plan JavaScript Logic
Determine:
- Which formulas can be directly converted (SUM, IF, AVERAGE, etc.)
- Which formulas need LLM conversion (VLOOKUP, complex nested)
- VBA functions that need JavaScript equivalents
- Calculation order (dependency graph)

### 4. Design Print Layout
Specify:
- Paper size (A4, Letter)
- Orientation (portrait, landscape)
- Margins
- Elements to hide when printing (buttons, inputs)
- Page break locations

## Output Format

Return a WebAppPlan object with:
```json
{
  "app_name": "앱 이름 (한글)",
  "app_description": "앱 설명",
  "source_file": "원본 파일명",
  "components": [
    {
      "component_type": "form|result_display|table",
      "title": "섹션 제목",
      "source_sheet": "시트명",
      "form_fields": [...],
      "output_fields": [...]
    }
  ],
  "functions": [
    {
      "name": "calculate",
      "description": "메인 계산 함수",
      "parameters": ["input1", "input2"],
      "return_type": "void"
    }
  ],
  "input_cell_map": {"field_name": "A1", ...},
  "output_cell_map": {"output_name": "B2", ...},
  "print_layout": {
    "paper_size": "A4",
    "orientation": "portrait",
    "margins": {"top": "20mm", "right": "15mm", ...}
  },
  "html_structure_notes": "HTML 구조 지침",
  "css_style_notes": "스타일링 지침",
  "js_logic_notes": "JavaScript 로직 지침"
}
```

## Guidelines

1. **Korean labels**: Use Korean for all user-facing text
2. **Semantic naming**: Use descriptive names (급여, 보험료) not cell addresses (A1, B2)
3. **Logical grouping**: Group related fields together
4. **Print optimization**: Design for A4 paper printing by default
5. **Accessibility**: Include proper labels and ARIA attributes in notes

Be thorough and specific - the Generator agent will implement your plan exactly.
"""


def create_planner_agent() -> Agent:
    """Create the Planner Agent instance."""
    return Agent(
        name="WebApp Planner",
        instructions=PLANNER_INSTRUCTIONS,
        tools=[],  # No tools - pure LLM reasoning
        model="gpt-5.2",  # SOTA model for complex reasoning & architecture
        output_type=AgentOutputSchema(WebAppPlan, strict_json_schema=False),  # Structured output
    )


def create_plan_prompt(analysis_dict: dict) -> str:
    """
    Create a prompt for the Planner agent.

    Args:
        analysis_dict: ExcelAnalysis as dictionary

    Returns:
        Prompt string for the planner
    """
    # Extract key information
    filename = analysis_dict.get("filename", "unknown.xlsx")
    sheets = analysis_dict.get("sheets", [])
    has_vba = analysis_dict.get("has_vba", False)
    vba_modules = analysis_dict.get("vba_modules", [])
    print_settings = analysis_dict.get("print_settings", {})
    complexity = analysis_dict.get("complexity_score", "low")

    # Build sheet summaries
    sheet_summaries = []
    for sheet in sheets:
        sheet_summaries.append(f"""
### Sheet: {sheet['name']}
- Dimensions: {sheet['row_count']} rows × {sheet['col_count']} cols
- Used range: {sheet['used_range']}
- Input cells ({len(sheet['input_cells'])}): {', '.join(sheet['input_cells'][:10])}{'...' if len(sheet['input_cells']) > 10 else ''}
- Output cells ({len(sheet['output_cells'])}): {', '.join(sheet['output_cells'][:10])}{'...' if len(sheet['output_cells']) > 10 else ''}
- Formulas ({len(sheet['formulas'])}):
""")
        for f in sheet["formulas"][:5]:
            sheet_summaries.append(f"  - {f['cell']}: {f['formula']}")
        if len(sheet["formulas"]) > 5:
            sheet_summaries.append(f"  - ... and {len(sheet['formulas']) - 5} more")

    # Build VBA summary
    vba_summary = ""
    if has_vba:
        vba_summary = "\n## VBA Modules\n"
        for module in vba_modules:
            vba_summary += f"- {module['name']} ({module['module_type']}): {', '.join(module['procedures'])}\n"

    # Build print settings summary
    print_summary = ""
    if print_settings:
        print_summary = f"""
## Print Settings
- Orientation: {print_settings.get('orientation', 'portrait')}
- Paper size: {print_settings.get('paper_size', 'A4')}
- Margins: {print_settings.get('margins', {})}
"""

    return f"""# Excel Analysis for Web App Conversion

## File Information
- Filename: {filename}
- Complexity: {complexity}
- Has VBA: {"Yes" if has_vba else "No"}

{''.join(sheet_summaries)}
{vba_summary}
{print_summary}

Based on this analysis, create a complete WebAppPlan for converting this Excel file to a web application.
"""
