#!/usr/bin/env python3
"""Top 10 엑셀 파일을 웹앱으로 변환 - 해커톤용"""
import asyncio
import json
from pathlib import Path

from src.orchestrator import convert_excel_to_webapp, ConversionProgress
from src.tracing import add_json_tracing

# Top 10 파일 정보 (선정 이유 포함)
TOP10_FILES = [
    {
        "name": "간이영수증",
        "path": "excel_files/엑셀 간이영수증 표준 양식 v2.0.xlsx",
        "output": "demos/01-receipt.html",
        "category": "수식풍부 (XLSX)",
        "reason": "233개 수식, VLOOKUP/IF/SUM 등 핵심 함수 - 변환 기술력 시연에 최적",
        "functions": ["IF", "SUM", "TEXT", "TODAY", "VLOOKUP"],
        "formulas": 233
    },
    {
        "name": "종합소득세 계산기",
        "path": "excel_files/종합소득세 엑셀 간이 계산기 v2.1.xlsx",
        "output": "demos/02-income-tax.html",
        "category": "세금계산",
        "reason": "세금 계산 로직 → JS 함수 변환 - 실용적 비즈니스 가치",
        "functions": ["VLOOKUP", "IFERROR", "MAX", "SUM"],
        "formulas": 24
    },
    {
        "name": "4대보험 자동계산기",
        "path": "excel_files/4대보험_자동계산기_엑셀템플릿.xlsx",
        "output": "demos/03-insurance.html",
        "category": "보험/급여",
        "reason": "4대보험 자동 계산 - HR 도메인 실용성",
        "functions": ["자동계산"],
        "formulas": 6
    },
    {
        "name": "거래명세표 (자동계산)",
        "path": "excel_files/엑셀서식(20160517)/거래명세표(자동계산)/3.xlsx",
        "output": "demos/04-invoice-auto.html",
        "category": "자동화",
        "reason": "동적 계산 로직 포함 - 자동화 기능 시연",
        "functions": ["자동계산"],
        "formulas": 0
    },
    {
        "name": "계산서",
        "path": "excel_files/엑셀서식(20160517)/계산서/계산서.xlsx",
        "output": "demos/05-statement.html",
        "category": "세무/회계",
        "reason": "기본 세무 양식 - 비즈니스 실용성",
        "functions": [],
        "formulas": 0
    },
    {
        "name": "인사기록카드",
        "path": "excel_files/엑셀서식(20160517)/인사기록카드(외국인근로자관리)/3.xlsx",
        "output": "demos/06-hr-record.html",
        "category": "인사/HR",
        "reason": "HR 문서 양식 - 도메인 다양성",
        "functions": [],
        "formulas": 0
    },
    {
        "name": "거래명세표",
        "path": "excel_files/엑셀서식(20160517)/거래명세표1/거래명세표1.xlsx",
        "output": "demos/07-invoice.html",
        "category": "거래/B2B",
        "reason": "B2B 거래 양식 - 일반 비즈니스 활용",
        "functions": [],
        "formulas": 0
    },
    {
        "name": "자금집행품의서",
        "path": "excel_files/엑셀서식(20160517)/자금집행품의서외/3.xlsx",
        "output": "demos/08-fund-request.html",
        "category": "재무/자금",
        "reason": "자금 관리 양식 - 재무 도메인",
        "functions": [],
        "formulas": 0
    },
    {
        "name": "시공계획서",
        "path": "excel_files/엑셀서식(20160517)/시공계획서(흙막이공사)/3.xlsx",
        "output": "demos/09-construction.html",
        "category": "건설/공사",
        "reason": "건설 산업 문서 - 산업별 다양성",
        "functions": [],
        "formulas": 0
    },
    {
        "name": "가계부 (자동화)",
        "path": "excel_files/엑셀서식(20160517)/가계부(자동화엑셀)/3.xlsx",
        "output": "demos/10-household.html",
        "category": "개인용",
        "reason": "가계부 자동화 - 개인 사용자 타겟",
        "functions": ["자동화"],
        "formulas": 0
    },
]


async def convert_single(file_info: dict, base_path: Path) -> dict:
    """단일 파일 변환"""
    excel_path = base_path / file_info["path"]
    output_path = base_path / file_info["output"]

    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def progress_callback(progress: ConversionProgress):
        print(f"  [{progress.progress:.0%}] {progress.message}")

    print(f"\n{'='*60}")
    print(f"변환 중: {file_info['name']}")
    print(f"카테고리: {file_info['category']}")
    print(f"선정 이유: {file_info['reason']}")
    print(f"{'='*60}")

    try:
        result = await convert_excel_to_webapp(str(excel_path), progress_callback)

        if result.success:
            # HTML에 선정 이유 메타데이터 추가
            html = add_selection_metadata(result.app.html, file_info)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"✓ 성공: {output_path}")
            return {"name": file_info["name"], "success": True, "output": str(output_path)}
        else:
            print(f"✗ 실패: {result.message}")
            return {"name": file_info["name"], "success": False, "error": result.message}
    except Exception as e:
        print(f"✗ 에러: {e}")
        return {"name": file_info["name"], "success": False, "error": str(e)}


def add_selection_metadata(html: str, file_info: dict) -> str:
    """HTML에 선정 이유 배너 추가"""
    banner = f'''
<!-- 해커톤 선정 정보 -->
<div id="selection-banner" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    z-index: 10000;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
">
    <div>
        <strong>📊 {file_info["name"]}</strong>
        <span style="margin-left: 10px; opacity: 0.9;">| {file_info["category"]}</span>
    </div>
    <div style="display: flex; align-items: center; gap: 15px;">
        <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 12px; font-size: 12px;">
            {file_info.get("formulas", 0)}개 수식
        </span>
        <button onclick="document.getElementById('selection-info').style.display='block'"
                style="background: white; color: #667eea; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 500;">
            선정 이유 보기
        </button>
    </div>
</div>

<div id="selection-info" style="
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 10001;
    display: none;
    justify-content: center;
    align-items: center;
" onclick="this.style.display='none'">
    <div style="
        background: white;
        padding: 30px;
        border-radius: 16px;
        max-width: 500px;
        margin: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    " onclick="event.stopPropagation()">
        <h2 style="margin: 0 0 15px; color: #333;">🏆 해커톤 선정 이유</h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <strong style="color: #667eea;">{file_info["category"]}</strong>
            <p style="margin: 10px 0 0; color: #555; line-height: 1.6;">{file_info["reason"]}</p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            {"".join(f'<span style="background: #e3e8ff; color: #4c5fd5; padding: 4px 10px; border-radius: 12px; font-size: 12px;">{fn}</span>' for fn in file_info.get("functions", [])[:5])}
        </div>
        <button onclick="document.getElementById('selection-info').style.display='none'"
                style="margin-top: 20px; width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
            닫기
        </button>
    </div>
</div>

<style>
body {{ padding-top: 56px !important; }}
</style>
'''

    # </body> 앞에 삽입
    if '</body>' in html:
        html = html.replace('</body>', banner + '</body>')
    else:
        html += banner

    return html


async def main():
    """메인 함수"""
    base_path = Path(__file__).parent

    print("🚀 해커톤용 Top 10 Excel → WebApp 변환 시작")
    print(f"총 {len(TOP10_FILES)}개 파일 변환 예정\n")

    results = []
    for file_info in TOP10_FILES:
        result = await convert_single(file_info, base_path)
        results.append(result)

    # 결과 요약
    print("\n" + "="*60)
    print("변환 결과 요약")
    print("="*60)

    success = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"✓ 성공: {len(success)}개")
    print(f"✗ 실패: {len(failed)}개")

    if failed:
        print("\n실패 목록:")
        for f in failed:
            print(f"  - {f['name']}: {f.get('error', 'Unknown')}")

    # 결과 저장
    with open(base_path / "conversion_results.json", 'w', encoding='utf-8') as f:
        json.dump({
            "total": len(results),
            "success": len(success),
            "failed": len(failed),
            "results": results,
            "files_info": TOP10_FILES
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과가 conversion_results.json에 저장되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
