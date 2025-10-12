"""
Daily reflection generation endpoints.
"""

from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUserId
from app.models.schemas import DailyInputRequest, ReflectionResponse
from app.services import SupabaseService, AstrologyService, BedrockService

router = APIRouter(prefix="/reflection", tags=["reflection"])


@router.get("/today", response_model=ReflectionResponse | None)
async def get_today_reflection(user_id: CurrentUserId) -> ReflectionResponse | None:
    """
    Get today's reflection if it exists, otherwise return None.
    """
    try:
        supabase_service = SupabaseService()
        today = date.today()
        
        existing_report = await supabase_service.get_report_by_date(user_id, today)
        
        if existing_report:
            return ReflectionResponse(
                karma_score=existing_report.karma_score,
                reading=existing_report.reading,
                rituals=existing_report.rituals,
                report_id=existing_report.id,
                created_at=existing_report.created_at,
            )
        
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reflection: {str(e)}")


@router.post("/generate", response_model=ReflectionResponse)
async def generate_reflection(
    request: DailyInputRequest,
    user_id: CurrentUserId,  # Authenticated user_id from JWT
) -> ReflectionResponse:
    """
    Generate a daily karma reflection based on user's mood and actions.

    This endpoint:
    1. Fetches user's astrology data
    2. Gets today's horoscope
    3. Generates AI reflection via Bedrock
    4. Stores the report in database
    5. Returns the reflection
    """
    try:
        # Initialize services
        supabase_service = SupabaseService()
        astrology_service = AstrologyService()
        bedrock_service = BedrockService()

        # Get user data (using authenticated user_id from JWT)
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user already has a report for today
        today = date.today()
        existing_report = await supabase_service.get_report_by_date(user_id, today)
        if existing_report:
            return ReflectionResponse(
                karma_score=existing_report.karma_score,
                reading=existing_report.reading,
                rituals=existing_report.rituals,
                report_id=existing_report.id,
                created_at=existing_report.created_at,
            )

        # Get today's horoscope
        horoscope = await astrology_service.get_daily_horoscope(user.sun_sign)

        # Generate reflection via Bedrock
        bedrock_reflection = await bedrock_service.generate_reflection(
            name=user.name,
            sun_sign=user.sun_sign,
            moon_sign=user.moon_sign,
            mood=request.mood,
            actions=request.actions,
            note=request.note,
            horoscope=horoscope,
            today=today,
        )

        # Store in database (using authenticated user_id)
        report = await supabase_service.create_daily_report(
            user_id=user_id,
            report_date=today,
            mood=request.mood,
            actions=request.actions,
            karma_score=bedrock_reflection.karma_score,
            reading=bedrock_reflection.reading,
            rituals=bedrock_reflection.rituals,
            note=request.note,
        )

        return ReflectionResponse(
            karma_score=report.karma_score,
            reading=report.reading,
            rituals=report.rituals,
            report_id=report.id,
            created_at=report.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reflection generation failed: {str(e)}")
