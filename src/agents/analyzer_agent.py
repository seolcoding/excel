"""Analyzer Agent - Sequential structural analysis of Excel files.

Implements 4-phase analysis flow:
1. Cell Layout & Structure - Physical organization of cells
2. Input/Output Mapping - Data flow identification
3. Formula Dependency Graph - Calculation chain analysis
4. VBA Relationship Extraction - Macro-to-cell mappings
"""

import re
from collections import defaultdict
from typing import Any

from agents import Agent, function_tool

from src.models import ExcelAnalysis
from src.tools.excel_analyzer import analyze_excel_file, get_cell_data, get_vba_module_code


# =============================================================================
# Phase 1: Cell Layout & Structure Tools
# =============================================================================

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


@function_tool
def analyze_layout_structure(analysis_dict: str) -> str:
    """
    Analyze the physical layout structure of the Excel workbook.

    Phase 1 of sequential analysis - identifies:
    - Section boundaries (header, input area, output area, footer)
    - Merged cell regions
    - Border-defined areas
    - Label-value patterns
    - Grid structure (rows/columns with similar purposes)

    Args:
        analysis_dict: JSON string of ExcelAnalysis data

    Returns:
        Structured layout analysis as JSON string
    """
    import json

    try:
        analysis = json.loads(analysis_dict) if isinstance(analysis_dict, str) else analysis_dict
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid analysis data"})

    layout_info = {
        "sections": [],
        "merged_regions": [],
        "label_value_pairs": [],
        "grid_patterns": [],
        "recommendations": []
    }

    sheets = analysis.get("sheets", [])

    for sheet in sheets:
        sheet_name = sheet.get("name", "Unknown")
        used_range = sheet.get("used_range", {})

        # Identify potential sections based on row/column usage
        min_row = used_range.get("min_row", 1)
        max_row = used_range.get("max_row", 1)
        min_col = used_range.get("min_col", 1)
        max_col = used_range.get("max_col", 1)

        # Estimate sections
        row_count = max_row - min_row + 1

        if row_count > 10:
            # Likely has distinct sections
            layout_info["sections"].append({
                "sheet": sheet_name,
                "header_rows": f"{min_row}-{min_row + 2}",
                "body_rows": f"{min_row + 3}-{max_row - 2}",
                "footer_rows": f"{max_row - 1}-{max_row}",
                "column_span": f"{chr(64 + min_col)}-{chr(64 + min(max_col, 26))}"
            })

        # Check for merged cells patterns
        merged = sheet.get("merged_cells", [])
        if merged:
            layout_info["merged_regions"].extend([
                {"sheet": sheet_name, "range": m}
                for m in merged[:10]  # Limit for readability
            ])

    # Recommendations based on structure
    if len(sheets) == 1:
        layout_info["recommendations"].append(
            "Single sheet - can be converted to single-page web form"
        )
    else:
        layout_info["recommendations"].append(
            f"{len(sheets)} sheets detected - consider tabbed interface or multi-page form"
        )

    return json.dumps(layout_info, ensure_ascii=False, indent=2)


# =============================================================================
# Phase 2: Input/Output Mapping Tools
# =============================================================================

@function_tool
def analyze_io_mapping(analysis_dict: str) -> str:
    """
    Analyze and map input cells to output cells.

    Phase 2 of sequential analysis - identifies:
    - Pure input cells (no formulas, referenced by formulas)
    - Output cells (contain formulas, display results)
    - Intermediate calculation cells (formulas that feed other formulas)
    - Static content cells (labels, headers, constants)
    - Data flow direction (top-down, left-to-right, mixed)

    Args:
        analysis_dict: JSON string of ExcelAnalysis data

    Returns:
        I/O mapping analysis as JSON string
    """
    import json

    try:
        analysis = json.loads(analysis_dict) if isinstance(analysis_dict, str) else analysis_dict
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid analysis data"})

    io_mapping = {
        "input_cells": [],
        "output_cells": [],
        "intermediate_cells": [],
        "static_cells": [],
        "data_flow": "unknown",
        "input_groups": [],
        "output_groups": []
    }

    # Collect input cells from all sheets
    input_cells = set()
    for sheet in analysis.get("sheets", []):
        input_cells.update(sheet.get("input_cells", []))

    # Get all cells with formulas
    formula_cells = set()
    formula_dependencies = {}

    sheets = analysis.get("sheets", [])
    for sheet in sheets:
        for formula_info in sheet.get("formulas", []):
            cell = formula_info.get("cell", "")
            # Support both 'dependencies' and 'references' keys
            refs = formula_info.get("dependencies", formula_info.get("references", []))
            formula_cells.add(cell)
            formula_dependencies[cell] = refs

    # Categorize cells
    for cell in input_cells:
        # Check if this input is used by multiple formulas (key input)
        usage_count = sum(
            1 for deps in formula_dependencies.values() if cell in deps
        )
        io_mapping["input_cells"].append({
            "cell": cell,
            "usage_count": usage_count,
            "importance": "high" if usage_count > 2 else "normal"
        })

    # Identify intermediate vs output cells
    cells_used_by_formulas = set()
    for deps in formula_dependencies.values():
        cells_used_by_formulas.update(deps)

    for cell, deps in formula_dependencies.items():
        is_intermediate = cell in cells_used_by_formulas
        cell_info = {
            "cell": cell,
            "depends_on": deps[:5],  # Limit for readability
            "is_intermediate": is_intermediate
        }

        if is_intermediate:
            io_mapping["intermediate_cells"].append(cell_info)
        else:
            io_mapping["output_cells"].append(cell_info)

    # Analyze data flow direction
    if io_mapping["input_cells"] and io_mapping["output_cells"]:
        # Extract row numbers
        input_rows = [int(re.search(r'\d+', c["cell"]).group())
                      for c in io_mapping["input_cells"] if re.search(r'\d+', c["cell"])]
        output_rows = [int(re.search(r'\d+', c["cell"]).group())
                       for c in io_mapping["output_cells"] if re.search(r'\d+', c["cell"])]

        if input_rows and output_rows:
            avg_input_row = sum(input_rows) / len(input_rows)
            avg_output_row = sum(output_rows) / len(output_rows)

            if avg_input_row < avg_output_row:
                io_mapping["data_flow"] = "top-to-bottom"
            elif avg_input_row > avg_output_row:
                io_mapping["data_flow"] = "bottom-to-top"
            else:
                io_mapping["data_flow"] = "horizontal"

    # Group inputs by row proximity
    sorted_inputs = sorted(io_mapping["input_cells"],
                           key=lambda x: x["cell"])
    if sorted_inputs:
        current_group = [sorted_inputs[0]]
        for inp in sorted_inputs[1:]:
            current_group.append(inp)
            if len(current_group) >= 3:
                io_mapping["input_groups"].append({
                    "cells": [c["cell"] for c in current_group],
                    "label": f"Input Group {len(io_mapping['input_groups']) + 1}"
                })
                current_group = []

    return json.dumps(io_mapping, ensure_ascii=False, indent=2)


# =============================================================================
# Phase 3: Formula Dependency Graph Tools
# =============================================================================

@function_tool
def build_formula_dependency_graph(analysis_dict: str) -> str:
    """
    Build a complete formula dependency graph.

    Phase 3 of sequential analysis - creates:
    - Directed graph of cell dependencies
    - Calculation order (topological sort)
    - Circular reference detection
    - Formula complexity scoring
    - Dependency depth for each output cell

    Args:
        analysis_dict: JSON string of ExcelAnalysis data

    Returns:
        Dependency graph analysis as JSON string
    """
    import json

    try:
        analysis = json.loads(analysis_dict) if isinstance(analysis_dict, str) else analysis_dict
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid analysis data"})

    graph = {
        "nodes": [],
        "edges": [],
        "calculation_order": [],
        "circular_references": [],
        "complexity_scores": {},
        "max_depth": 0,
        "formula_chains": []
    }

    # Build adjacency list
    adjacency = defaultdict(list)  # cell -> cells it depends on
    reverse_adjacency = defaultdict(list)  # cell -> cells that depend on it
    all_cells = set()

    sheets = analysis.get("sheets", [])
    for sheet in sheets:
        for formula_info in sheet.get("formulas", []):
            cell = formula_info.get("cell", "")
            # Support both 'dependencies' and 'references' keys
            refs = formula_info.get("dependencies", formula_info.get("references", []))
            formula = formula_info.get("formula", "")

            all_cells.add(cell)
            all_cells.update(refs)

            adjacency[cell] = refs
            for ref in refs:
                reverse_adjacency[ref].append(cell)

            # Add node info
            graph["nodes"].append({
                "cell": cell,
                "formula": formula[:50] if formula else "",  # Truncate long formulas
                "depends_on_count": len(refs),
                "used_by_count": len(reverse_adjacency.get(cell, []))
            })

            # Add edges
            for ref in refs:
                graph["edges"].append({
                    "from": ref,
                    "to": cell,
                    "type": "data_flow"
                })

    # Topological sort for calculation order
    in_degree = defaultdict(int)
    for cell, deps in adjacency.items():
        for dep in deps:
            in_degree[cell] += 1

    # Find cells with no dependencies (starting points)
    queue = [cell for cell in all_cells if in_degree[cell] == 0]
    calc_order = []
    visited = set()

    while queue:
        cell = queue.pop(0)
        if cell in visited:
            continue
        visited.add(cell)
        calc_order.append(cell)

        for dependent in reverse_adjacency[cell]:
            in_degree[dependent] -= 1
            if in_degree[dependent] <= 0 and dependent not in visited:
                queue.append(dependent)

    graph["calculation_order"] = calc_order[:20]  # Limit for readability

    # Detect circular references
    for cell in all_cells:
        if cell not in visited:
            graph["circular_references"].append(cell)

    # Calculate complexity scores
    def get_depth(cell: str, memo: dict = None) -> int:
        if memo is None:
            memo = {}
        if cell in memo:
            return memo[cell]
        if cell not in adjacency or not adjacency[cell]:
            memo[cell] = 0
            return 0
        depth = 1 + max(get_depth(dep, memo) for dep in adjacency[cell])
        memo[cell] = depth
        return depth

    depth_memo = {}
    for cell in adjacency:
        depth = get_depth(cell, depth_memo)
        graph["complexity_scores"][cell] = {
            "depth": depth,
            "direct_deps": len(adjacency[cell]),
            "score": depth * 10 + len(adjacency[cell])
        }
        graph["max_depth"] = max(graph["max_depth"], depth)

    # Identify key formula chains
    output_cells = [cell for cell in adjacency if not reverse_adjacency.get(cell)]
    for output in output_cells[:5]:  # Top 5 output cells
        chain = []
        current = output
        seen = set()
        while current and current not in seen:
            chain.append(current)
            seen.add(current)
            deps = adjacency.get(current, [])
            current = deps[0] if deps else None
        if len(chain) > 1:
            graph["formula_chains"].append({
                "output": output,
                "chain": chain[:10],  # Limit chain length
                "length": len(chain)
            })

    return json.dumps(graph, ensure_ascii=False, indent=2)


# =============================================================================
# Phase 4: VBA Relationship Tools
# =============================================================================

@function_tool
def analyze_vba_cell_mapping(analysis_dict: str) -> str:
    """
    Analyze VBA code to map macro relationships with cells.

    Phase 4 of sequential analysis - extracts:
    - Cell references in VBA code (Range, Cells, etc.)
    - Event triggers (Worksheet_Change, Button clicks)
    - Calculation flows in VBA
    - Data validation in VBA
    - VBA-to-JavaScript porting recommendations

    Args:
        analysis_dict: JSON string of ExcelAnalysis data

    Returns:
        VBA-cell mapping analysis as JSON string
    """
    import json

    try:
        analysis = json.loads(analysis_dict) if isinstance(analysis_dict, str) else analysis_dict
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid analysis data"})

    vba_mapping = {
        "has_vba": False,
        "modules": [],
        "cell_references": [],
        "event_handlers": [],
        "calculation_procedures": [],
        "validation_logic": [],
        "porting_recommendations": []
    }

    # Support both 'vba_modules' (from ExcelAnalysis model) and 'vba.macros' formats
    vba_modules = analysis.get("vba_modules", [])
    if not vba_modules:
        vba_info = analysis.get("vba", {})
        vba_modules = vba_info.get("macros", []) if vba_info else []

    if not vba_modules:
        vba_mapping["porting_recommendations"].append(
            "No VBA detected - pure formula conversion"
        )
        return json.dumps(vba_mapping, ensure_ascii=False, indent=2)

    vba_mapping["has_vba"] = True

    # Analyze each module
    for module in vba_modules:
        module_name = module.get("name", "Unknown")
        module_type = module.get("module_type", "Module")
        code = module.get("code", "")
        procedures = module.get("procedures", [])

        module_info = {
            "name": module_name,
            "type": module_type,
            "procedures": procedures,
            "cell_refs": []
        }

        # Extract cell references
        cell_patterns = [
            (r'Range\("([A-Z]+\d+(?::[A-Z]+\d+)?)"\)', "Range"),
            (r'Cells\((\d+),\s*(\d+)\)', "Cells"),
            (r'\[([A-Z]+\d+)\]', "Bracket"),
            (r'\.Value\s*=', "ValueAssignment"),
        ]

        for pattern, ref_type in cell_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                if isinstance(match, tuple):
                    ref = f"R{match[0]}C{match[1]}"
                else:
                    ref = match
                module_info["cell_refs"].append({
                    "reference": ref,
                    "type": ref_type
                })
                vba_mapping["cell_references"].append({
                    "module": module_name,
                    "reference": ref,
                    "type": ref_type
                })

        # Analyze procedures from module data or extract from code
        proc_list = procedures if procedures else []
        if not proc_list and code:
            # Extract from code if not provided
            proc_matches = re.findall(
                r'(?:Public |Private )?(Sub|Function)\s+(\w+)',
                code
            )
            proc_list = [name for _, name in proc_matches]

        for proc_name in proc_list:
            # Identify event handlers
            if proc_name.startswith("Worksheet_") or proc_name.startswith("Workbook_"):
                vba_mapping["event_handlers"].append({
                    "event": proc_name,
                    "module": module_name
                })
            # Identify button/control handlers
            elif proc_name.startswith("btn") or proc_name.startswith("cmd"):
                vba_mapping["event_handlers"].append({
                    "event": proc_name,
                    "module": module_name,
                    "type": "button_click"
                })

            # Identify calculation procedures
            if any(kw in proc_name.lower() for kw in ["calc", "compute", "update", "total", "sum", "get"]):
                vba_mapping["calculation_procedures"].append({
                    "procedure": proc_name,
                    "module": module_name
                })

        # Extract validation logic
        if "If" in code and ("MsgBox" in code or "Exit" in code):
            vba_mapping["validation_logic"].append({
                "module": module_name,
                "type": "conditional_validation"
            })

        vba_mapping["modules"].append(module_info)

    # Generate porting recommendations
    if vba_mapping["event_handlers"]:
        vba_mapping["porting_recommendations"].append(
            f"{len(vba_mapping['event_handlers'])} event handlers → Convert to JavaScript event listeners"
        )

    if vba_mapping["calculation_procedures"]:
        vba_mapping["porting_recommendations"].append(
            f"{len(vba_mapping['calculation_procedures'])} calculation procedures → Convert to JS functions"
        )

    if vba_mapping["validation_logic"]:
        vba_mapping["porting_recommendations"].append(
            f"{len(vba_mapping['validation_logic'])} validation blocks → Convert to form validation"
        )

    unique_cells = len(set(r["reference"] for r in vba_mapping["cell_references"]))
    if unique_cells > 0:
        vba_mapping["porting_recommendations"].append(
            f"{unique_cells} unique cell references → Map to HTML input/output elements"
        )

    return json.dumps(vba_mapping, ensure_ascii=False, indent=2)


# =============================================================================
# Additional VBA Tool for Deep Analysis
# =============================================================================

@function_tool
def get_vba_code(file_path: str, module_name: str) -> str:
    """
    Get full VBA code for a specific module.

    Use this tool when you need to see the complete code of a VBA module
    for detailed analysis. The initial analysis only shows code summaries.

    Args:
        file_path: Path to the Excel file (.xlsm)
        module_name: Exact name of the VBA module (e.g., "z_Mod_DB.bas")

    Returns:
        JSON with full module code and procedure list
    """
    import json
    result = get_vba_module_code(file_path, module_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


# =============================================================================
# Agent Definition with Sequential Analysis Flow
# =============================================================================

ANALYZER_INSTRUCTIONS = """You are an Excel file analyzer expert that performs **sequential 4-phase analysis**.

## Analysis Flow (MUST FOLLOW IN ORDER)

### Phase 1: 셀의 위치와 구조 (Cell Layout & Structure)
Analyze the physical layout first:
- Use `analyze_excel` to get raw data
- Use `analyze_layout_structure` to identify sections
- Identify: header areas, input regions, output regions, labels
- Note merged cells, borders, and visual groupings

### Phase 2: 인풋/아웃풋 매핑 (Input/Output Mapping)
After understanding structure, map data flow:
- Use `analyze_io_mapping` to categorize cells
- Identify pure inputs (user-editable cells)
- Identify outputs (formula result cells)
- Identify intermediate calculations
- Determine data flow direction (top-down, left-right)

### Phase 3: 수식 연결 관계 (Formula Dependency Graph)
Build the calculation chain:
- Use `build_formula_dependency_graph` to analyze formulas
- Create dependency tree for each output
- Calculate complexity scores
- Identify circular references (if any)
- Determine calculation order

### Phase 4: VBA 관계 파악 (VBA Relationship Extraction)
If VBA is present, extract mappings:
- Use `analyze_vba_cell_mapping` to map VBA-to-cells
- Identify event handlers and triggers
- Extract calculation procedures
- Map validation logic
- Generate porting recommendations

## Output Format

After completing all 4 phases, provide a structured summary:

```
## 분석 결과 요약 (Analysis Summary)

### 1. 레이아웃 구조 (Layout Structure)
- 시트 수: X
- 섹션 구분: 헤더, 입력 영역, 출력 영역
- 병합 셀: Y개

### 2. 입출력 매핑 (I/O Mapping)
- 입력 셀: A1, B2, ... (총 X개)
- 출력 셀: C5, D10, ... (총 Y개)
- 중간 계산 셀: (총 Z개)
- 데이터 흐름: 상단→하단

### 3. 수식 의존성 (Formula Dependencies)
- 최대 의존 깊이: X단계
- 복잡도 높은 셀: C5 (score: 25)
- 계산 순서: A1 → B2 → C5 → D10

### 4. VBA 관계 (VBA Relationships)
- VBA 유무: 있음/없음
- 이벤트 핸들러: Worksheet_Change 등
- 계산 프로시저: CalculateTotal 등
- 포팅 권장사항: ...

### 변환 권장사항 (Conversion Recommendations)
- UI 타입: 폼/테이블/계산기
- 주의사항: ...
```

Be thorough and methodical - the Planner agent depends on this sequential analysis to design the web app correctly.
"""


def create_analyzer_agent() -> Agent:
    """Create the Analyzer Agent with sequential analysis tools."""
    return Agent(
        name="Excel Analyzer",
        instructions=ANALYZER_INSTRUCTIONS,
        tools=[
            # Phase 1: Structure
            analyze_excel,
            get_sheet_cells,
            analyze_layout_structure,
            # Phase 2: I/O
            analyze_io_mapping,
            # Phase 3: Dependencies
            build_formula_dependency_graph,
            # Phase 4: VBA
            analyze_vba_cell_mapping,
            get_vba_code,  # For detailed VBA module analysis
        ],
        model="gpt-5-mini",  # Cost-optimized model for analysis
    )


def create_analyze_prompt(file_path: str) -> str:
    """
    Create a prompt for the Analyzer agent with sequential analysis flow.

    Args:
        file_path: Path to the Excel file

    Returns:
        Prompt string for the analyzer
    """
    return f"""Please analyze the Excel file following the **4-phase sequential analysis**:

File: {file_path}

## Required Analysis Flow

1. **Phase 1 - 셀의 위치와 구조 (Layout)**
   - analyze_excel → analyze_layout_structure
   - Identify sections, merged cells, visual structure

2. **Phase 2 - 인풋/아웃풋 (I/O Mapping)**
   - analyze_io_mapping
   - Categorize input, output, intermediate cells

3. **Phase 3 - 수식 연결 관계 (Dependencies)**
   - build_formula_dependency_graph
   - Build calculation chain, check complexity

4. **Phase 4 - VBA 관계 (VBA Relationships)**
   - analyze_vba_cell_mapping
   - Extract VBA-cell mappings and porting recommendations

After all 4 phases, provide the structured summary in Korean with:
- 레이아웃 구조 분석 결과
- 입출력 셀 목록 및 데이터 흐름
- 수식 의존성 그래프 요약
- VBA 매핑 및 포팅 권장사항
- 최종 변환 권장사항"""
