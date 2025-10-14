"""
Karmona Backend API

AI-powered karma reflection API that blends astrology and daily journaling.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    health_router,
    onboarding_router,
    reflection_router,
    history_router,
    waitlist_router,
    summary_router,
    account_router,
    check_in_router,
    counsel_router,
    forecast_router,
    friends_router,
    tarot_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    # Startup
    print(f"🌙 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 API prefix: {settings.api_v1_prefix}")
    print(f"🔧 Debug mode: {settings.debug}")
    
    # NOTE: Daily scraper automation removed to fix Railway build timeout
    # Run manually with: python scripts/run_daily_scrape.py
    # Or set up external cron (GitHub Actions, AWS EventBridge)

    yield

    # Shutdown
    print("👋 Shutting down Karmona API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered karma reflection API blending astrology and daily journaling",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


# Include routers
app.include_router(health_router)
app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
app.include_router(reflection_router, prefix=settings.api_v1_prefix)
app.include_router(history_router, prefix=settings.api_v1_prefix)
app.include_router(waitlist_router, prefix=settings.api_v1_prefix)
app.include_router(summary_router, prefix=settings.api_v1_prefix)
app.include_router(account_router, prefix=settings.api_v1_prefix)
app.include_router(check_in_router, prefix=settings.api_v1_prefix)
app.include_router(counsel_router, prefix=settings.api_v1_prefix)
app.include_router(forecast_router, prefix=settings.api_v1_prefix)
app.include_router(friends_router, prefix=settings.api_v1_prefix)
app.include_router(tarot_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
