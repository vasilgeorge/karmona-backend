"""API routers."""

from .onboarding import router as onboarding_router
from .reflection import router as reflection_router
from .history import router as history_router
from .health import router as health_router
from .waitlist import router as waitlist_router
from .summary import router as summary_router

__all__ = [
    "onboarding_router",
    "reflection_router",
    "history_router",
    "health_router",
    "waitlist_router",
    "summary_router",
]
