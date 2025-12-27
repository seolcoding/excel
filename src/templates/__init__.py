"""Jinja2 template utilities for web app generation."""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models import WebAppPlan, GeneratedWebApp, GeneratedCode
from src.tools import get_helper_functions_js


# Template directory
TEMPLATE_DIR = Path(__file__).parent


def get_template_env() -> Environment:
    """Get the Jinja2 environment with our templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_calculator(
    plan: WebAppPlan,
    form_fields: list[dict],
    output_fields: list[dict],
    calculate_logic: str,
    data_properties: str,
    custom_css: str = "",
) -> str:
    """
    Render a calculator-type web app.

    Args:
        plan: WebAppPlan with app metadata
        form_fields: List of form field definitions
        output_fields: List of output field definitions
        calculate_logic: JavaScript calculation logic
        data_properties: JavaScript data properties
        custom_css: Additional CSS styles

    Returns:
        Complete HTML string
    """
    env = get_template_env()
    template = env.get_template("calculator.html.j2")

    return template.render(
        app_name=plan.app_name,
        app_description=plan.app_description,
        source_file=plan.source_file,
        form_fields=form_fields,
        output_fields=output_fields,
        calculate_logic=calculate_logic,
        data_properties=data_properties,
        helper_functions=get_helper_functions_js(),
        custom_css=custom_css,
        print_layout=plan.print_layout.model_dump() if plan.print_layout else {},
    )


def render_form(
    plan: WebAppPlan,
    sections: list[dict],
    signature_section: bool = True,
    date_section: bool = True,
    custom_css: str = "",
) -> str:
    """
    Render a form/template-type web app.

    Args:
        plan: WebAppPlan with app metadata
        sections: List of form sections with fields
        signature_section: Whether to show signature area
        date_section: Whether to show date
        custom_css: Additional CSS styles

    Returns:
        Complete HTML string
    """
    env = get_template_env()
    template = env.get_template("form.html.j2")

    # Build data properties from all fields
    all_fields = []
    for section in sections:
        all_fields.extend(section.get("fields", []))

    data_properties = ",\n".join(
        f"{f['name']}: '{f.get('default_value', '')}'"
        for f in all_fields
    )

    return template.render(
        app_name=plan.app_name,
        app_description=plan.app_description,
        source_file=plan.source_file,
        form_title=plan.app_name,
        sections=sections,
        signature_section=signature_section,
        date_section=date_section,
        data_properties=data_properties,
        helper_functions=get_helper_functions_js(),
        custom_css=custom_css,
        print_layout=plan.print_layout.model_dump() if plan.print_layout else {},
    )


def render_table(
    plan: WebAppPlan,
    columns: list[dict],
    initial_rows: str,
    row_calculation_logic: str = "",
    totals_calculation_logic: str = "",
    show_totals: bool = True,
    show_row_numbers: bool = True,
    allow_add_row: bool = True,
    allow_delete_row: bool = True,
    custom_css: str = "",
) -> str:
    """
    Render a table-type web app.

    Args:
        plan: WebAppPlan with app metadata
        columns: List of column definitions
        initial_rows: JavaScript array literal for initial rows
        row_calculation_logic: JavaScript for per-row calculations
        totals_calculation_logic: JavaScript for footer totals
        show_totals: Whether to show totals row
        show_row_numbers: Whether to show row numbers
        allow_add_row: Whether to allow adding rows
        allow_delete_row: Whether to allow deleting rows
        custom_css: Additional CSS styles

    Returns:
        Complete HTML string
    """
    env = get_template_env()
    template = env.get_template("table.html.j2")

    # Build initial totals
    initial_totals = "{"
    for col in columns:
        if col.get("show_total"):
            initial_totals += f"{col['name']}: 0, "
    initial_totals += "}"

    # Build new row template
    new_row_template = "{"
    for col in columns:
        default = col.get("default_value", "''")
        if col.get("type") == "number":
            default = col.get("default_value", 0)
        new_row_template += f"{col['name']}: {default}, "
    new_row_template += "}"

    return template.render(
        app_name=plan.app_name,
        app_description=plan.app_description,
        source_file=plan.source_file,
        table_title=plan.app_name,
        columns=columns,
        initial_rows=initial_rows,
        initial_totals=initial_totals,
        new_row_template=new_row_template,
        row_calculation_logic=row_calculation_logic,
        totals_calculation_logic=totals_calculation_logic,
        show_totals=show_totals,
        show_row_numbers=show_row_numbers,
        allow_add_row=allow_add_row,
        allow_delete_row=allow_delete_row,
        helper_functions=get_helper_functions_js(),
        custom_css=custom_css,
        print_layout=plan.print_layout.model_dump() if plan.print_layout else {},
    )


def render_from_plan(plan: WebAppPlan) -> GeneratedWebApp:
    """
    Automatically render a web app from a WebAppPlan.

    Determines the best template based on component types.

    Args:
        plan: WebAppPlan to render

    Returns:
        GeneratedWebApp with complete HTML
    """
    # Determine app type from components
    component_types = [c.component_type for c in plan.components]

    if "table" in component_types:
        # Table-heavy app
        html = _render_table_from_plan(plan)
    elif len(plan.components) == 1 and plan.components[0].component_type == "form":
        # Pure form/template
        html = _render_form_from_plan(plan)
    else:
        # Default to calculator
        html = _render_calculator_from_plan(plan)

    return GeneratedWebApp(
        app_name=plan.app_name,
        source_excel=plan.source_file,
        html=html,
        css="",  # Embedded in HTML
        js="",  # Embedded in HTML
        components=[],
    )


def _render_calculator_from_plan(plan: WebAppPlan) -> str:
    """Render calculator from plan."""
    form_fields = []
    output_fields = []

    for comp in plan.components:
        for field in comp.form_fields:
            form_fields.append({
                "name": field.name,
                "label": field.label,
                "field_type": field.field_type,
                "required": field.required,
                "default_value": field.default_value,
                "options": field.options,
            })

        for output in comp.output_fields:
            format_fn = {
                "currency": "formatCurrency",
                "number": "formatNumber",
                "percentage": "formatPercent",
            }.get(output.format, "")

            output_fields.append({
                "name": output.name,
                "label": output.label,
                "format_function": format_fn,
            })

    # Build data properties
    data_props = []
    for f in form_fields:
        default = f.get("default_value", "")
        if f["field_type"] == "number":
            default = f.get("default_value", 0) or 0
        elif f["field_type"] == "checkbox":
            default = "false"
        else:
            default = f"'{default or ''}'"
        data_props.append(f"{f['name']}: {default}")

    for o in output_fields:
        data_props.append(f"{o['name']}: 0")

    data_properties = ",\n".join(data_props)

    # Build calculate logic (placeholder)
    calc_lines = ["// Calculation logic"]
    for fn in plan.functions:
        calc_lines.append(f"// {fn.name}: {fn.description}")

    calculate_logic = "\n".join(calc_lines)

    return render_calculator(
        plan=plan,
        form_fields=form_fields,
        output_fields=output_fields,
        calculate_logic=calculate_logic,
        data_properties=data_properties,
    )


def _render_form_from_plan(plan: WebAppPlan) -> str:
    """Render form from plan."""
    sections = []

    for comp in plan.components:
        fields = []
        for field in comp.form_fields:
            fields.append({
                "name": field.name,
                "label": field.label,
                "field_type": field.field_type,
                "col_size": "6",
                "options": field.options,
            })

        sections.append({
            "title": comp.title,
            "fields": fields,
        })

    return render_form(
        plan=plan,
        sections=sections,
    )


def _render_table_from_plan(plan: WebAppPlan) -> str:
    """Render table from plan."""
    columns = []
    initial_rows = "[]"

    for comp in plan.components:
        if comp.component_type == "table":
            for field in comp.form_fields:
                columns.append({
                    "name": field.name,
                    "label": field.label,
                    "type": field.field_type,
                    "align": "right" if field.field_type == "number" else "left",
                })

            for output in comp.output_fields:
                format_fn = {
                    "currency": "formatCurrency",
                    "number": "formatNumber",
                }.get(output.format, "")

                columns.append({
                    "name": output.name,
                    "label": output.label,
                    "readonly": True,
                    "align": "right",
                    "show_total": True,
                    "format_function": format_fn,
                })

    return render_table(
        plan=plan,
        columns=columns,
        initial_rows=initial_rows,
    )


__all__ = [
    "get_template_env",
    "render_calculator",
    "render_form",
    "render_table",
    "render_from_plan",
]
