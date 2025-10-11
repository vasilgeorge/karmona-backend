"""
User history endpoints.
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import HistoryResponse
from app.services import SupabaseService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{user_id}", response_model=HistoryResponse)
async def get_user_history(
    user_id: str, limit: int = Query(default=7, ge=1, le=30)
) -> HistoryResponse:
    """
    Get user's karma history (last N days).

    Returns:
    - List of daily reports
    - Average karma score
    """
    try:
        supabase_service = SupabaseService()

        # Get user to verify exists
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get history
        reports = await supabase_service.get_user_history(user_id, limit)

        # Calculate average
        avg_score = None
        if reports:
            avg_score = sum(r.karma_score for r in reports) / len(reports)

        return HistoryResponse(user_id=user_id, reports=reports, avg_karma_score=avg_score)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

