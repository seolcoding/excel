"""Agents for Excel to Web App conversion.

Agent Pipeline (LLM-as-a-Judge pattern):
1. Analyzer Agent: Extract structure from Excel
2. Planner Agent: Design web app architecture
3. Generator Agent: Produce HTML/CSS/JS code
4. Tester Agent: Evaluate code and provide feedback (LLM-as-a-Judge)
"""

from .analyzer_agent import create_analyzer_agent, create_analyze_prompt
from .planner_agent import create_planner_agent, create_plan_prompt
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

__all__ = [
    # Analyzer
    "create_analyzer_agent",
    "create_analyze_prompt",
    # Planner
    "create_planner_agent",
    "create_plan_prompt",
    # Generator
    "create_generator_agent",
    "create_generation_prompt",
    "generate_html_template",
    # Tester (LLM-as-a-Judge)
    "create_tester_agent",
    "create_test_prompt",
    "TestEvaluation",
]
