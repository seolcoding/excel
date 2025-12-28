"""Spec Agent - Creates TDD-oriented WebAppSpec from Excel analysis.

This agent replaces the Planner Agent in TDD flow.
Instead of creating a WebAppPlan, it creates a WebAppSpec that:
1. Defines testable requirements
2. Specifies expected behaviors for test generation
3. Includes boundary conditions for thorough testing
"""

from agents import Agent, AgentOutputSchema

from src.models import WebAppSpec


SPEC_AGENT_INSTRUCTIONS = """You are a TDD (Test-Driven Development) specification architect.

Your job is to create a WebAppSpec from Excel analysis that enables:
1. Test-First development (write failing tests before code)
2. Clear, testable requirements
3. Comprehensive boundary condition testing

## Input

You receive an ExcelAnalysis containing:
- Sheet information (names, dimensions, formulas)
- Input cells (where users enter data)
- Output cells (where calculations are displayed)
- VBA modules (if any)
- Print settings

## Your Tasks

### 1. Define Input Fields
For each input cell, specify:
- `name`: Semantic name (e.g., "salary", "tax_rate")
- `type`: "number" | "text" | "date" | "select"
- `label`: Korean label for UI
- `validation`: Min/max, required, pattern
- `source_cell`: Original Excel cell (e.g., "B3")

### 2. Define Output Fields
For each output/formula cell, specify:
- `name`: Semantic name (e.g., "total_tax", "net_salary")
- `format`: "number" | "currency" | "percentage" | "text"
- `label`: Korean label for UI
- `source_cell`: Original Excel cell
- `source_formula`: Original Excel formula

### 3. Define Calculations
For each calculation, specify:
- `name`: Calculation name
- `inputs`: List of input field names
- `output`: Output field name
- `formula`: Original Excel formula
- `expected_logic`: Plain language description

### 4. Define Expected Behaviors (CRITICAL for TDD)
List testable behaviors, e.g.:
- "When salary is 5000000, tax should be 500000 (10%)"
- "When input is empty, show validation error"
- "Print button should trigger window.print()"

### 5. Define Boundary Conditions (CRITICAL for TDD)
For each calculation, define boundary test cases:
```json
{
  "name": "zero_input_test",
  "inputs": {"salary": 0},
  "expected_output": {"tax": 0},
  "description": "Zero input should produce zero tax"
}
```

Include:
- Zero values
- Negative values (if applicable)
- Large numbers
- Empty/null values
- Edge cases specific to the formula

## Output Format

Return a WebAppSpec:
```json
{
  "app_name": "앱 이름",
  "app_description": "앱 설명",
  "input_fields": [
    {
      "name": "salary",
      "type": "number",
      "label": "급여",
      "source_cell": "B3",
      "validation": {"required": true, "min": 0}
    }
  ],
  "output_fields": [
    {
      "name": "tax",
      "format": "currency",
      "label": "세금",
      "source_cell": "B10",
      "source_formula": "=B3*0.1"
    }
  ],
  "calculations": [
    {
      "name": "calculate_tax",
      "inputs": ["salary"],
      "output": "tax",
      "formula": "=B3*0.1",
      "expected_logic": "Tax is 10% of salary"
    }
  ],
  "expected_behaviors": [
    "Salary 5000000 → Tax 500000",
    "Empty salary → Validation error",
    "Calculate button triggers recalculation"
  ],
  "boundary_conditions": [
    {
      "name": "zero_salary",
      "inputs": {"salary": 0},
      "expected_output": {"tax": 0},
      "description": "Zero salary produces zero tax"
    },
    {
      "name": "large_salary",
      "inputs": {"salary": 100000000},
      "expected_output": {"tax": 10000000},
      "description": "Large values calculated correctly"
    }
  ],
  "korean_labels": true,
  "print_layout": {
    "paper_size": "A4",
    "orientation": "portrait"
  }
}
```

## Guidelines

1. **Testable requirements**: Every behavior must be verifiable
2. **Semantic naming**: Use meaningful names, not cell addresses
3. **Korean labels**: All user-facing text in Korean
4. **Boundary coverage**: Include edge cases for robust testing
5. **Formula accuracy**: Preserve original Excel formula logic

Be thorough - the Test Generator will use this spec to create failing tests.
"""


def create_spec_agent() -> Agent:
    """Create the Spec Agent instance for TDD pipeline."""
    return Agent(
        name="TDD Spec Architect",
        instructions=SPEC_AGENT_INSTRUCTIONS,
        tools=[],  # No tools - pure LLM reasoning
        model="gpt-5.2",  # SOTA model for complex reasoning
        output_type=AgentOutputSchema(WebAppSpec, strict_json_schema=False),
    )


def create_spec_prompt(analysis_dict: dict) -> str:
    """
    Create a prompt for the Spec Agent.

    Args:
        analysis_dict: ExcelAnalysis as dictionary

    Returns:
        Prompt string for the spec agent
    """
    filename = analysis_dict.get("filename", "unknown.xlsx")
    sheets = analysis_dict.get("sheets", [])
    has_vba = analysis_dict.get("has_vba", False)
    vba_modules = analysis_dict.get("vba_modules", [])
    print_settings = analysis_dict.get("print_settings", {})

    # Build sheet summaries with formula details
    sheet_summaries = []
    all_formulas = []

    for sheet in sheets:
        sheet_summaries.append(f"""
### Sheet: {sheet['name']}
- Dimensions: {sheet['row_count']} rows × {sheet['col_count']} cols
- Used range: {sheet['used_range']}
- Input cells ({len(sheet['input_cells'])}): {', '.join(sheet['input_cells'][:10])}{'...' if len(sheet['input_cells']) > 10 else ''}
- Output cells ({len(sheet['output_cells'])}): {', '.join(sheet['output_cells'][:10])}{'...' if len(sheet['output_cells']) > 10 else ''}
""")
        # Collect formulas for testing
        for f in sheet.get("formulas", []):
            all_formulas.append({
                "sheet": sheet["name"],
                "cell": f["cell"],
                "formula": f["formula"],
            })

    # Format formulas
    formula_section = "\n## Formulas to Convert\n"
    for f in all_formulas[:20]:
        formula_section += f"- {f['sheet']}!{f['cell']}: `{f['formula']}`\n"
    if len(all_formulas) > 20:
        formula_section += f"... and {len(all_formulas) - 20} more\n"

    # VBA summary
    vba_summary = ""
    if has_vba and vba_modules:
        vba_summary = "\n## VBA Modules\n"
        for module in vba_modules:
            vba_summary += f"- {module['name']}: {', '.join(module.get('procedures', []))}\n"

    # Print settings
    print_summary = ""
    if print_settings:
        print_summary = f"""
## Print Settings
- Orientation: {print_settings.get('orientation', 'portrait')}
- Paper size: {print_settings.get('paper_size', 'A4')}
"""

    return f"""# Excel Analysis for TDD Specification

## File Information
- Filename: {filename}
- Has VBA: {"Yes" if has_vba else "No"}

{''.join(sheet_summaries)}
{formula_section}
{vba_summary}
{print_summary}

Create a comprehensive WebAppSpec with:
1. All input/output fields mapped from Excel cells
2. Calculation specifications with expected logic
3. **Expected behaviors** - specific, testable behaviors
4. **Boundary conditions** - edge cases for thorough testing

Focus on creating testable requirements that the Test Generator can use.
"""
