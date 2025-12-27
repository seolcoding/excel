"""FastAPI routes for Excel to WebApp conversion."""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.orchestrator import (
    ExcelToWebAppOrchestrator,
    ConversionProgress,
    convert_excel_to_webapp,
)
from src.models import ConversionResult, GeneratedWebApp


router = APIRouter(prefix="/api/v1", tags=["conversion"])


# In-memory storage for conversion jobs (would use Redis/DB in production)
conversion_jobs: dict[str, dict] = {}


class ConversionRequest(BaseModel):
    """Request to start a conversion."""
    max_iterations: int = 3
    min_pass_rate: float = 0.9


class ConversionStatus(BaseModel):
    """Status of a conversion job."""
    job_id: str
    status: str  # 'pending', 'analyzing', 'planning', 'generating', 'complete', 'failed'
    progress: float
    message: str
    result: Optional[dict] = None


class DownloadResponse(BaseModel):
    """Response with download information."""
    filename: str
    html: str


@router.post("/convert", response_model=ConversionStatus)
async def start_conversion(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """
    Start an Excel to WebApp conversion.

    Upload an Excel file (.xlsx or .xlsm) and receive a job ID
    to track the conversion progress.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".xlsx", ".xlsm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Use .xlsx or .xlsm",
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file to temp directory
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir) / file.filename

    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    # Initialize job status
    conversion_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "message": "변환 대기 중...",
        "file_path": str(temp_path),
        "original_filename": file.filename,
        "result": None,
    }

    # Start conversion in background
    if background_tasks:
        background_tasks.add_task(run_conversion, job_id)
    else:
        # For testing without background tasks
        await run_conversion_async(job_id)

    return ConversionStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="변환 시작됨",
    )


async def run_conversion_async(job_id: str):
    """Run conversion asynchronously."""
    job = conversion_jobs.get(job_id)
    if not job:
        return

    file_path = job["file_path"]

    def progress_callback(progress: ConversionProgress):
        job["status"] = progress.stage
        job["progress"] = progress.progress
        job["message"] = progress.message

    try:
        result = await convert_excel_to_webapp(file_path, progress_callback)

        if result.success:
            job["status"] = "complete"
            job["progress"] = 1.0
            job["message"] = "변환 완료!"
            job["result"] = {
                "app_name": result.app.app_name,
                "html": result.app.html,
                "iterations": result.iterations_used,
                "pass_rate": result.final_pass_rate,
            }
        else:
            job["status"] = "failed"
            job["message"] = result.message

    except Exception as e:
        job["status"] = "failed"
        job["message"] = f"변환 오류: {str(e)}"

    finally:
        # Clean up temp file
        try:
            os.unlink(file_path)
            os.rmdir(Path(file_path).parent)
        except Exception:
            pass


def run_conversion(job_id: str):
    """Run conversion in background (sync wrapper)."""
    import asyncio
    asyncio.run(run_conversion_async(job_id))


@router.get("/status/{job_id}", response_model=ConversionStatus)
async def get_conversion_status(job_id: str):
    """
    Get the status of a conversion job.

    Poll this endpoint to track progress.
    """
    job = conversion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return ConversionStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result=job.get("result"),
    )


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """
    Download the generated web app HTML.

    Returns the complete HTML file ready for use.
    """
    job = conversion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Conversion not complete. Status: {job['status']}",
        )

    result = job.get("result")
    if not result or not result.get("html"):
        raise HTTPException(status_code=500, detail="No HTML generated")

    # Generate filename
    original = job.get("original_filename", "webapp.xlsx")
    base_name = Path(original).stem
    filename = f"{base_name}_webapp.html"

    return HTMLResponse(
        content=result["html"],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/html; charset=utf-8",
        },
    )


@router.get("/preview/{job_id}")
async def preview_result(job_id: str):
    """
    Preview the generated web app in browser.

    Returns HTML that renders directly.
    """
    job = conversion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Conversion not complete. Status: {job['status']}",
        )

    result = job.get("result")
    if not result or not result.get("html"):
        raise HTTPException(status_code=500, detail="No HTML generated")

    return HTMLResponse(content=result["html"])


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a conversion job and its results.
    """
    if job_id not in conversion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = conversion_jobs.pop(job_id)

    # Clean up temp file if still exists
    file_path = job.get("file_path")
    if file_path:
        try:
            os.unlink(file_path)
            os.rmdir(Path(file_path).parent)
        except Exception:
            pass

    return {"message": "Job deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "excel-to-webapp",
        "version": "1.0.0",
    }
