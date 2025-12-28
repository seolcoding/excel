"""Analyzer Agent - Extracts structural information from Excel files."""

from agents import Agent, function_tool

from src.models import ExcelAnalysis
from src.tools.excel_analyzer import analyze_excel_file, get_cell_data


@function_tool
def analyze_excel(file_path: str) -> dict:
    """
    Analyze an Excel file and extract complete structural information.

    This tool parses the Excel file to extract:
    - Sheet structure (names, dimensions, used ranges)
    - All formulas and their dependencies
    - VBA macros (if .xlsm file)
    - Print settings (orientation, margins, page size)
    - Input cells (cells referenced by formulas but not formulas themselves)
    - Output cells (cells containing formulas)

    Args:
        file_path: Path to the Excel file (.xlsx, .xlsm)

    Returns:
        Complete analysis as a dictionary
    """
    analysis = analyze_excel_file(file_path)
    return analysis.model_dump()


@function_tool
def get_sheet_cells(file_path: str, sheet_name: str = None) -> dict:
    """
    Get detailed cell information from a specific worksheet.

    Returns information about each cell including:
    - Cell address
    - Value (text, number, or formula result)
    - Formula (if any)
    - Data type
    - Number format

    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet (optional, defaults to active sheet)

    Returns:
        Dictionary mapping cell addresses to cell information
    """
    cells = get_cell_data(file_path, sheet_name)
    return {addr: cell.model_dump() for addr, cell in cells.items()}


# Agent definition
ANALYZER_INSTRUCTIONS = """You are an Excel file analyzer expert.

Your role is to thoroughly analyze Excel files to extract all structural information needed
for web app conversion.

## Your Tasks

1. **Analyze the Excel file** using the analyze_excel tool
2. **Review the analysis** and identify:
   - Which cells are inputs (user enters data)
   - Which cells are outputs (display calculated results)
   - How formulas depend on each other
   - If there's VBA code that needs conversion
   - Print layout requirements

3. **Provide a comprehensive summary** including:
   - File complexity assessment
   - List of all sheets and their purposes
   - Formula complexity breakdown
   - VBA presence and complexity
   - Recommended conversion approach

## Output Format

Return the complete ExcelAnalysis data along with your observations about:
- Any potential conversion challenges
- Suggested UI component types (form, table, calculator)
- Print layout considerations

Be thorough - the Planner agent depends on your analysis to design the web app correctly.
"""


def create_analyzer_agent() -> Agent:
    """Create the Analyzer Agent instance."""
    return Agent(
        name="Excel Analyzer",
        instructions=ANALYZER_INSTRUCTIONS,
        tools=[analyze_excel, get_sheet_cells],
        model="gpt-5-mini",  # SOTA cost-optimized model
    )


def create_analyze_prompt(file_path: str) -> str:
    """
    Create a prompt for the Analyzer agent.

    Args:
        file_path: Path to the Excel file

    Returns:
        Prompt string for the analyzer
    """
    return f"""Please analyze the Excel file at the following path:

File: {file_path}

Use the analyze_excel tool to extract complete structural information from this file.
After analysis, provide a comprehensive summary of:
1. File structure (sheets, dimensions)
2. Input cells and output cells
3. Formula complexity
4. VBA presence (if any)
5. Print layout settings
6. Recommended conversion approach

Return the complete analysis data."""
