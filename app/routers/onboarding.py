"""
User onboarding endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUserId
from app.models.schemas import OnboardingRequest, OnboardingResponse
from app.services import SupabaseService, AstrologyService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/", response_model=OnboardingResponse)
async def onboard_user(
    request: OnboardingRequest,
    user_id: CurrentUserId,  # Get authenticated user_id from JWT
) -> OnboardingResponse:
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

        # Check if user already exists
        existing_user = await supabase_service.get_user(user_id)
        
        if existing_user:
            # User exists - update their profile instead
            print(f"User {user_id} already exists, updating profile...")
            data = {
                "name": request.name,
                "email": request.email,
                "birthdate": request.birthdate.isoformat(),
                "birth_time": request.birth_time,
                "birth_place": request.birth_place,
                "sun_sign": astrology_data.sun_sign,
                "moon_sign": astrology_data.moon_sign,
            }
            
            result = supabase_service.client.table("users").update(data).eq(
                "id", str(user_id)
            ).execute()
            
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to update user")
            
            user_data = result.data[0]
            from app.models.schemas import UserProfile
            from datetime import datetime
            user = UserProfile(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                birthdate=datetime.fromisoformat(user_data["birthdate"]).date(),
                birth_time=user_data.get("birth_time"),
                birth_place=user_data.get("birth_place"),
                sun_sign=user_data["sun_sign"],
                moon_sign=user_data.get("moon_sign"),
                created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00")),
                subscription_tier=user_data.get("subscription_tier", "free"),
                subscription_status=user_data.get("subscription_status", "free"),
                stripe_customer_id=user_data.get("stripe_customer_id"),
                stripe_subscription_id=user_data.get("stripe_subscription_id"),
                subscription_period_end=datetime.fromisoformat(user_data["subscription_period_end"].replace("Z", "+00:00")) if user_data.get("subscription_period_end") else None,
            )
        else:
            # Create new user in database
            user = await supabase_service.create_user(
                name=request.name,
                email=request.email,
                birthdate=request.birthdate,
                birth_time=request.birth_time,
                birth_place=request.birth_place,
                sun_sign=astrology_data.sun_sign,
                moon_sign=astrology_data.moon_sign,
                user_id=user_id,  # Use the auth user_id from JWT token
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
