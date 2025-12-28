"""Tools for Excel parsing and code conversion."""

from .excel_analyzer import (
    analyze_excel_file,
    get_cell_data,
)
from .formula_converter import (
    is_simple_formula,
    convert_simple_formula,
    get_helper_functions_js,
    generate_calculation_function,
    ConversionResult,
)
from .vba_converter import (
    check_vba_convertibility,
    parse_vba_structure,
    generate_llm_prompt,
    simple_vba_to_js,
    validate_converted_js,
    VBAConversionResult,
    VBAConversionError,
)
from .test_generator import (
    extract_test_cases,
    generate_node_test_script,
    generate_playwright_tests,
)
from .static_test_runner import (
    StaticTestRunner,
    run_static_tests,
    run_static_tests_sync,
)
from .e2e_test_runner import (
    PlaywrightE2ERunner,
    run_e2e_tests,
    run_e2e_tests_sync,
)

__all__ = [
    # Excel analyzer
    "analyze_excel_file",
    "get_cell_data",
    # Formula converter
    "is_simple_formula",
    "convert_simple_formula",
    "get_helper_functions_js",
    "generate_calculation_function",
    "ConversionResult",
    # VBA converter
    "check_vba_convertibility",
    "parse_vba_structure",
    "generate_llm_prompt",
    "simple_vba_to_js",
    "validate_converted_js",
    "VBAConversionResult",
    "VBAConversionError",
    # Test generator
    "extract_test_cases",
    "generate_node_test_script",
    "generate_playwright_tests",
    # Static test runner
    "StaticTestRunner",
    "run_static_tests",
    "run_static_tests_sync",
    # E2E test runner
    "PlaywrightE2ERunner",
    "run_e2e_tests",
    "run_e2e_tests_sync",
]
