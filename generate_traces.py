"""Generate sample trace JSON files for each demo."""

import json
from datetime import datetime, timedelta
import random

demos = [
    {
        "num": "01",
        "name": "간이영수증",
        "excel": "엑셀 간이영수증 표준 양식 v2.0.xlsx",
        "formulas": 233,
        "functions": ["IF", "SUM", "TEXT", "TODAY", "VLOOKUP"]
    },
    {
        "num": "02",
        "name": "종합소득세 계산기",
        "excel": "종합소득세 엑셀 간이 계산기 v2.1.xlsx",
        "formulas": 24,
        "functions": ["VLOOKUP", "IFERROR", "MAX", "SUM"]
    },
    {
        "num": "03",
        "name": "4대보험 자동계산기",
        "excel": "4대보험_자동계산기_엑셀템플릿.xlsx",
        "formulas": 6,
        "functions": ["자동계산"]
    },
    {
        "num": "04",
        "name": "거래명세표 (자동계산)",
        "excel": "거래명세표(자동계산)/3.xlsx",
        "formulas": 0,
        "functions": ["자동계산"]
    },
    {
        "num": "05",
        "name": "계산서",
        "excel": "계산서/계산서.xlsx",
        "formulas": 0,
        "functions": ["양식"]
    },
    {
        "num": "06",
        "name": "인사기록카드",
        "excel": "인사기록카드(외국인근로자관리)/3.xlsx",
        "formulas": 0,
        "functions": ["양식"]
    },
    {
        "num": "07",
        "name": "거래명세표",
        "excel": "거래명세표1/거래명세표1.xlsx",
        "formulas": 0,
        "functions": ["양식"]
    },
    {
        "num": "08",
        "name": "자금집행품의서",
        "excel": "자금집행품의서외/3.xlsx",
        "formulas": 0,
        "functions": ["양식"]
    },
    {
        "num": "09",
        "name": "CPM 공정표",
        "excel": "CPM공정표(네트워크)/1.xlsx",
        "formulas": 0,
        "functions": ["네트워크"]
    },
    {
        "num": "10",
        "name": "가계부 (자동화)",
        "excel": "가계부(자동화엑셀)/3.xlsx",
        "formulas": 0,
        "functions": ["자동화"]
    }
]

def generate_trace(demo):
    """Generate a sample trace for a demo."""
    base_time = datetime(2025, 12, 28, 11, 30, 0)

    # Analyzer agent
    analyzer_start = base_time
    analyzer_end = analyzer_start + timedelta(seconds=random.randint(20, 40))

    # Planner agent
    planner_start = analyzer_end + timedelta(seconds=1)
    planner_end = planner_start + timedelta(seconds=random.randint(15, 30))

    # Generator agent
    generator_start = planner_end + timedelta(seconds=1)
    generator_end = generator_start + timedelta(seconds=random.randint(60, 120))

    total_duration = (generator_end - base_time).total_seconds() * 1000

    # Token counts (approximate)
    base_tokens = 500 + demo["formulas"] * 10
    analyzer_tokens = base_tokens + random.randint(200, 500)
    planner_tokens = base_tokens + random.randint(300, 600)
    generator_tokens = base_tokens * 2 + random.randint(500, 1000)
    total_tokens = analyzer_tokens + planner_tokens + generator_tokens

    trace = {
        "trace_id": f"conv_{demo['num']}_trace",
        "workflow_name": f"Excel-to-WebApp: {demo['excel']}",
        "started_at": base_time.isoformat(),
        "ended_at": generator_end.isoformat(),
        "agents_used": ["Excel Analyzer", "WebApp Planner", "Code Generator"],
        "total_tokens": total_tokens,
        "total_cost": total_tokens * 0.00003,  # Approximate cost
        "llm_calls": [
            {
                "agent_name": "Excel Analyzer",
                "model": "gpt-4o",
                "system_prompt": f"""You are an Excel file analyzer agent. Your task is to analyze Excel files and extract their structure, formulas, and data patterns.

For each Excel file, you should:
1. Identify all sheets and their purposes
2. Find input cells (cells where users enter data)
3. Find output cells (cells with formulas that compute results)
4. Extract all formulas and understand their logic
5. Identify any VBA macros or automation

Use the analyze_excel tool to get the file structure, then use get_sheet_cells to examine specific sheets in detail.""",
                "input_messages": [
                    {
                        "role": "user",
                        "content": f"""Please analyze the following Excel file and extract its complete structure:

File: {demo['excel']}

I need you to:
1. Identify all sheets and their structure
2. Find all input cells (where users enter data)
3. Find all output cells (cells with formulas)
4. Extract and understand all formulas
5. Identify the business logic and calculation flow

Use the available tools to thoroughly analyze this file."""
                    }
                ],
                "output_content": f"""I've analyzed the Excel file "{demo['excel']}". Here's what I found:

**File Overview:**
- File Name: {demo['name']}
- Total Sheets: {random.randint(1, 3)}
- Total Formulas: {demo['formulas']}
- Functions Used: {', '.join(demo['functions'])}

**Sheet Structure:**
The file contains a well-organized {"calculation sheet" if demo['formulas'] > 0 else "form template"} with {"multiple formula-driven calculations" if demo['formulas'] > 0 else "structured input fields"}.

**Input Cells:**
Identified {random.randint(5, 15)} input cells where users can enter data.

**Output Cells:**
Found {demo['formulas']} formula cells that compute results based on inputs.

**Business Logic:**
This Excel file implements {"complex business calculations" if demo['formulas'] > 10 else "a standardized business form"} for {demo['name']}.

The analysis is complete and ready for the planning phase.""",
                "output_tool_calls": [
                    {
                        "name": "analyze_excel",
                        "arguments": json.dumps({"file_path": f"excel_files/{demo['excel']}"})
                    }
                ],
                "started_at": analyzer_start.isoformat(),
                "ended_at": analyzer_end.isoformat(),
                "duration_ms": (analyzer_end - analyzer_start).total_seconds() * 1000,
                "usage": {
                    "input_tokens": analyzer_tokens // 2,
                    "output_tokens": analyzer_tokens // 2,
                    "total_tokens": analyzer_tokens
                }
            },
            {
                "agent_name": "WebApp Planner",
                "model": "gpt-4o",
                "system_prompt": """You are a web application planner. Based on the Excel analysis, design a modern web application that replicates the Excel functionality.

Your plan should include:
1. UI/UX design decisions
2. Component structure
3. State management approach
4. Formula-to-JavaScript conversion strategy
5. Print layout preservation

Output a structured WebAppPlan with all necessary details.""",
                "input_messages": [
                    {
                        "role": "user",
                        "content": f"""Based on the Excel analysis for "{demo['name']}", please create a comprehensive web application plan.

The web app should:
1. Replicate all Excel functionality in the browser
2. Maintain the same calculation logic
3. Provide a clean, modern UI
4. Support printing with proper layout
5. Be responsive and user-friendly

Consider the {demo['formulas']} formulas and {', '.join(demo['functions'])} functions that need to be converted to JavaScript."""
                    }
                ],
                "output_content": f"""# Web Application Plan for {demo['name']}

## Overview
Converting the Excel file to a modern web application using HTML5, CSS3, and vanilla JavaScript with Alpine.js for reactivity.

## UI Design
- **Framework**: Bootstrap 5 for responsive layout
- **Reactivity**: Alpine.js for real-time calculations
- **Print Support**: CSS print media queries for A4 output

## Components
1. **Header Section**: Title and metadata
2. **Input Form**: {"Dynamic input fields with validation" if demo['formulas'] > 0 else "Structured form fields"}
3. **Calculation Display**: {"Real-time formula results" if demo['formulas'] > 0 else "Data display area"}
4. **Action Buttons**: Print, Reset, Export

## Formula Conversion Strategy
{f"Converting {demo['formulas']} Excel formulas to JavaScript functions:" if demo['formulas'] > 0 else "No complex formulas - focusing on form structure."}
{chr(10).join([f"- {fn}() → JavaScript equivalent" for fn in demo['functions'][:5]]) if demo['formulas'] > 0 else ""}

## State Management
Using Alpine.js x-data for reactive state management with computed properties for formula results.

## Print Layout
Preserving original Excel print layout using CSS @media print with proper margins and page breaks.

The plan is ready for code generation.""",
                "output_tool_calls": [],
                "started_at": planner_start.isoformat(),
                "ended_at": planner_end.isoformat(),
                "duration_ms": (planner_end - planner_start).total_seconds() * 1000,
                "usage": {
                    "input_tokens": planner_tokens // 2,
                    "output_tokens": planner_tokens // 2,
                    "total_tokens": planner_tokens
                }
            },
            {
                "agent_name": "Code Generator",
                "model": "gpt-4o",
                "system_prompt": """You are a code generator agent. Generate a complete, working HTML web application based on the provided plan.

Requirements:
1. Single HTML file with embedded CSS and JavaScript
2. Use Bootstrap 5 for styling
3. Use Alpine.js for reactivity
4. Implement all formulas as JavaScript functions
5. Ensure print layout matches original Excel
6. Korean language UI

Output a complete GeneratedWebApp with HTML code and metadata.""",
                "input_messages": [
                    {
                        "role": "user",
                        "content": f"""Generate a complete web application for "{demo['name']}" based on the plan.

Requirements:
- Single HTML file
- Bootstrap 5 + Alpine.js
- All {demo['formulas']} formulas converted to JS
- Korean UI
- Print-ready layout
- Responsive design

Generate production-ready code."""
                    }
                ],
                "output_content": f"""I've generated the complete web application for {demo['name']}.

## Generated Code Summary

**HTML Structure:**
- DOCTYPE and meta tags for Korean language support
- Bootstrap 5 CDN for styling
- Alpine.js CDN for reactivity
- Custom CSS for print layout

**JavaScript Implementation:**
{f"- {demo['formulas']} formula functions converted" if demo['formulas'] > 0 else "- Form validation and data handling"}
- Real-time calculation updates
- Print formatting functions
- Input validation

**CSS Styling:**
- Responsive grid layout
- Print media queries for A4 output
- Korean typography support
- Professional form styling

**Features:**
- Auto-calculation on input change
- Print preview support
- Reset functionality
- Responsive mobile layout

The generated HTML file is ready for deployment. Total lines: ~{random.randint(300, 800)} lines of code.""",
                "output_tool_calls": [],
                "started_at": generator_start.isoformat(),
                "ended_at": generator_end.isoformat(),
                "duration_ms": (generator_end - generator_start).total_seconds() * 1000,
                "usage": {
                    "input_tokens": generator_tokens // 2,
                    "output_tokens": generator_tokens // 2,
                    "total_tokens": generator_tokens
                }
            }
        ],
        "tool_calls": [
            {
                "name": "analyze_excel",
                "input": json.dumps({"file_path": f"excel_files/{demo['excel']}"}),
                "output": json.dumps({
                    "filename": demo['excel'].split('/')[-1],
                    "sheets": [{"name": "Sheet1", "formulas": demo['formulas']}],
                    "total_formulas": demo['formulas'],
                    "functions_used": demo['functions']
                }),
                "started_at": (analyzer_start + timedelta(seconds=2)).isoformat(),
                "ended_at": (analyzer_start + timedelta(seconds=5)).isoformat(),
                "duration_ms": 3000
            }
        ]
    }

    return trace


def main():
    for demo in demos:
        trace = generate_trace(demo)
        filename = f"traces/{demo['num']}-trace.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(trace, f, ensure_ascii=False, indent=2)

        print(f"Generated: {filename}")


if __name__ == "__main__":
    main()
