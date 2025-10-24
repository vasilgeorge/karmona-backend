"""
User statistics endpoint for progress tracking.
"""

from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import CurrentUserId
from app.services import SupabaseService

router = APIRouter(prefix="/stats", tags=["stats"])


class UserStatsResponse(BaseModel):
    """User progress statistics"""
    check_in_streak: int
    total_reflections: int
    total_check_ins: int
    days_active: int
    member_since: str  # Date user joined


@router.get("", response_model=UserStatsResponse)
async def get_user_stats(user_id: CurrentUserId) -> UserStatsResponse:
    """
    Get user's progress statistics.

    Returns:
    - check_in_streak: Consecutive days of check-ins (breaks if missed a day)
    - total_reflections: Total number of reflections generated
    - total_check_ins: Total number of check-ins completed
    - days_active: Days since account creation
    - member_since: Date user joined
    """
    try:
        supabase_service = SupabaseService()

        # Get user to find member_since
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        member_since = user.created_at
        days_active = (date.today() - member_since.date()).days + 1

        # Get total reflections count
        reflections_result = supabase_service.client.table("daily_reports").select(
            "id", count="exact"
        ).eq("user_id", str(user_id)).execute()
        total_reflections = reflections_result.count or 0

        # Get total check-ins count
        check_ins_result = supabase_service.client.table("daily_check_ins").select(
            "id", count="exact"
        ).eq("user_id", str(user_id)).execute()
        total_check_ins = check_ins_result.count or 0

        # Calculate check-in streak
        check_ins = supabase_service.client.table("daily_check_ins").select(
            "check_in_date"
        ).eq("user_id", str(user_id)).order(
            "check_in_date", desc=True
        ).execute()

        streak = 0
        if check_ins.data:
            # Convert to dates and sort descending
            dates = sorted(
                [date.fromisoformat(item["check_in_date"]) for item in check_ins.data],
                reverse=True
            )

            # Start from today or most recent check-in
            current_date = date.today()

            # If latest check-in is not today or yesterday, streak is 0
            if dates[0] < current_date - timedelta(days=1):
                streak = 0
            else:
                # Count consecutive days
                for check_date in dates:
                    if check_date == current_date or check_date == current_date - timedelta(days=1):
                        streak += 1
                        current_date = check_date - timedelta(days=1)
                    else:
                        break

        return UserStatsResponse(
            check_in_streak=streak,
            total_reflections=total_reflections,
            total_check_ins=total_check_ins,
            days_active=days_active,
            member_since=member_since.date().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
