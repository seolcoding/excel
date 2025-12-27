"""FastAPI application for Excel to WebApp conversion."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Excel to WebApp Converter",
        description="Convert Excel files (.xlsx, .xlsm) to standalone web applications",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router)

    @app.get("/")
    async def root():
        """Root endpoint with API info."""
        return {
            "name": "Excel to WebApp Converter API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "convert": "POST /api/v1/convert - Upload Excel and start conversion",
                "status": "GET /api/v1/status/{job_id} - Check conversion status",
                "download": "GET /api/v1/download/{job_id} - Download generated HTML",
                "preview": "GET /api/v1/preview/{job_id} - Preview in browser",
            },
        }

    return app


# Create default app instance
app = create_app()


__all__ = ["app", "create_app"]
