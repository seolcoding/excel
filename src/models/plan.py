"""Web app generation plan models."""

from pydantic import BaseModel
from typing import Optional


class FormField(BaseModel):
    """Definition of a form input field."""
    name: str
    label: str
    field_type: str  # 'text', 'number', 'date', 'select', 'checkbox'
    source_cell: str  # Excel cell this maps to
    required: bool = True
    default_value: Optional[str | int | float] = None
    validation: Optional[str] = None  # validation rule description
    options: Optional[list[str]] = None  # for select fields


class OutputField(BaseModel):
    """Definition of an output/result field."""
    name: str
    label: str
    source_cell: str  # Excel cell this maps to
    format: str = "number"  # 'text', 'number', 'currency', 'percentage', 'date'
    calculation: Optional[str] = None  # description of calculation


class ComponentSpec(BaseModel):
    """Specification for a UI component."""
    component_type: str  # 'form', 'result_display', 'table', 'summary'
    title: str
    description: Optional[str] = None
    source_sheet: str
    form_fields: list[FormField] = []
    output_fields: list[OutputField] = []


class JavaScriptFunction(BaseModel):
    """Specification for a JavaScript function to generate."""
    name: str
    description: str
    source_formula: Optional[str] = None  # Original Excel formula
    source_vba: Optional[str] = None  # Original VBA code if applicable
    parameters: list[str]
    return_type: str


class PrintLayout(BaseModel):
    """Print layout specification."""
    paper_size: str  # 'A4', 'Letter'
    orientation: str  # 'portrait', 'landscape'
    margins: dict[str, str]  # CSS margins
    header_html: Optional[str] = None
    footer_html: Optional[str] = None
    page_breaks: list[str] = []  # CSS selectors for page breaks


class WebAppPlan(BaseModel):
    """Complete plan for generating a web application."""
    app_name: str
    app_description: str
    source_file: str

    # UI Components
    components: list[ComponentSpec]

    # JavaScript logic
    functions: list[JavaScriptFunction]

    # Cell mappings
    input_cell_map: dict[str, str]  # form_field_name -> excel_cell
    output_cell_map: dict[str, str]  # output_field_name -> excel_cell

    # Print settings
    print_layout: PrintLayout

    # Generation instructions
    html_structure_notes: str
    css_style_notes: str
    js_logic_notes: str
