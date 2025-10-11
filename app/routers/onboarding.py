"""
User onboarding endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import OnboardingRequest, OnboardingResponse
from app.services import SupabaseService, AstrologyService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/", response_model=OnboardingResponse)
async def onboard_user(request: OnboardingRequest) -> OnboardingResponse:
    """
    Onboard a new user with their birth information.
    Calculates zodiac signs and stores in database.
    """
    try:
        # Initialize services
        astrology_service = AstrologyService()
        supabase_service = SupabaseService()

        # Calculate astrology data
        astrology_data = await astrology_service.get_astrology_data(
            birthdate=request.birthdate,
            birth_time=request.birth_time,
            birth_place=request.birth_place,
        )

        # Create user in database
        user = await supabase_service.create_user(
            name=request.name,
            email=request.email,
            birthdate=request.birthdate,
            birth_time=request.birth_time,
            birth_place=request.birth_place,
            sun_sign=astrology_data.sun_sign,
            moon_sign=astrology_data.moon_sign,
        )

        return OnboardingResponse(
            user_id=user.id,
            name=user.name,
            sun_sign=user.sun_sign,
            moon_sign=user.moon_sign,
            message=f"Welcome to Karmona, {user.name}! ✨",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

