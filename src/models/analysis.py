"""Excel analysis data models."""

from pydantic import BaseModel
from typing import Optional


class CellInfo(BaseModel):
    """Information about a cell."""
    address: str
    value: Optional[str | int | float | bool] = None
    formula: Optional[str] = None
    data_type: str  # 'string', 'number', 'formula', 'date', 'boolean', 'empty'
    format: Optional[str] = None


class FormulaInfo(BaseModel):
    """Information about an Excel formula."""
    cell: str  # e.g., 'A1'
    formula: str  # e.g., '=SUM(B1:B10)'
    dependencies: list[str]  # cells this formula depends on
    result_type: str  # 'number', 'string', 'boolean', 'date'


class VBAModule(BaseModel):
    """Information about a VBA module."""
    name: str
    module_type: str  # 'Module', 'Class', 'Form', 'Sheet'
    code: str
    procedures: list[str]  # list of procedure names


class SheetInfo(BaseModel):
    """Information about a worksheet."""
    name: str
    row_count: int
    col_count: int
    used_range: str  # e.g., 'A1:D20'
    input_cells: list[str]  # cells that appear to accept user input
    output_cells: list[str]  # cells that display calculated results
    formulas: list[FormulaInfo]
    has_print_area: bool
    print_area: Optional[str] = None


class PrintSettings(BaseModel):
    """Print settings for the workbook."""
    orientation: str  # 'portrait' or 'landscape'
    paper_size: str  # 'A4', 'Letter', etc.
    margins: dict[str, float]  # top, bottom, left, right in inches
    header: Optional[str] = None
    footer: Optional[str] = None
    fit_to_page: bool = False
    scale: int = 100


class ExcelAnalysis(BaseModel):
    """Complete analysis of an Excel file."""
    filename: str
    file_type: str  # 'xlsx', 'xlsm', 'xls'
    sheets: list[SheetInfo]
    vba_modules: list[VBAModule]
    has_vba: bool
    print_settings: Optional[PrintSettings] = None

    # Computed summary
    total_formulas: int
    total_input_cells: int
    total_output_cells: int
    complexity_score: str  # 'low', 'medium', 'high'
