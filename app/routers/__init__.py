"""API routers."""

from .onboarding import router as onboarding_router
from .reflection import router as reflection_router
from .history import router as history_router
from .health import router as health_router
from .waitlist import router as waitlist_router
from .summary import router as summary_router
from .account import router as account_router
from .check_in import router as check_in_router
from .counsel import router as counsel_router
from .forecast import router as forecast_router
from .friends import router as friends_router
from .payments import router as payments_router
from .tarot import router as tarot_router
from .stats import router as stats_router

__all__ = [
    "onboarding_router",
    "reflection_router",
    "history_router",
    "health_router",
    "waitlist_router",
    "summary_router",
    "account_router",
    "check_in_router",
    "counsel_router",
    "forecast_router",
    "friends_router",
    "payments_router",
    "tarot_router",
    "stats_router",
]
