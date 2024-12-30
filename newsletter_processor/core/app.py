from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from ..api.routes.search import router as search_router
from ..api.routes.admin import router as admin_router
from .config import get_settings
from .logging import setup_logging
from ..services.scheduler import start_scheduler

settings = get_settings()
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    app = FastAPI(
        title=settings.SERVICE_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(search_router, prefix=settings.API_V1_STR, tags=["search"])
    app.include_router(admin_router, prefix=settings.API_V1_STR, tags=["admin"])

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting newsletter processor service")
        scheduler = start_scheduler()
        app.state.scheduler = scheduler

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down newsletter processor service")
        if hasattr(app.state, "scheduler"):
            app.state.scheduler.shutdown()

    return app 