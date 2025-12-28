"""Agents for Excel to Web App conversion.

TDD Pipeline Flow:
1. Analyzer Agent: Extract structure from Excel
2. Spec Agent: Create testable WebAppSpec (TDD)
3. Test Generator: Generate failing tests from Spec
4. Generator Agent: Produce HTML/CSS/JS code to pass tests
5. Tester Agent: Evaluate code and provide feedback (LLM-as-a-Judge)

Legacy flow (deprecated):
1. Analyzer → 2. Planner → 3. Generator → 4. Tester
"""

from .analyzer_agent import (
    create_analyzer_agent,
    create_analyze_prompt,
    analyze_layout_structure,
    analyze_io_mapping,
    build_formula_dependency_graph,
    analyze_vba_cell_mapping,
)
from .planner_agent import create_planner_agent, create_plan_prompt
from .spec_agent import create_spec_agent, create_spec_prompt
from .generator_agent import (
    create_generator_agent,
    create_generation_prompt,
    generate_html_template,
)
from .tester_agent import (
    create_tester_agent,
    create_test_prompt,
    TestEvaluation,
)
from .test_generator_agent import (
    create_test_generator_agent,
    create_test_generation_prompt,
    GeneratedTestSuite,
    convert_to_static_test_suite,
)

__all__ = [
    # Analyzer
    "create_analyzer_agent",
    "create_analyze_prompt",
    "analyze_layout_structure",
    "analyze_io_mapping",
    "build_formula_dependency_graph",
    "analyze_vba_cell_mapping",
    # Planner (legacy)
    "create_planner_agent",
    "create_plan_prompt",
    # Spec Agent (TDD)
    "create_spec_agent",
    "create_spec_prompt",
    # Generator
    "create_generator_agent",
    "create_generation_prompt",
    "generate_html_template",
    # Tester (LLM-as-a-Judge)
    "create_tester_agent",
    "create_test_prompt",
    "TestEvaluation",
    # Test Generator
    "create_test_generator_agent",
    "create_test_generation_prompt",
    "GeneratedTestSuite",
    "convert_to_static_test_suite",
]
