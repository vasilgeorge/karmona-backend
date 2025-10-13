"""
User account management endpoints.
"""

from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.auth import CurrentUserId
from app.services import SupabaseService, AstrologyService
from app.models.schemas import UserProfile

router = APIRouter(prefix="/account", tags=["account"])


class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""
    
    name: str | None = None
    email: EmailStr | None = None
    birthdate: date | None = None
    birth_time: str | None = None
    birth_place: str | None = None


class UpdateProfileResponse(BaseModel):
    """Response after updating profile."""
    
    user: UserProfile
    message: str
    recalculated_astrology: bool = False


@router.get("/profile", response_model=UserProfile)
async def get_profile(user_id: CurrentUserId) -> UserProfile:
    """
    Get current user's profile information.
    """
    try:
        supabase_service = SupabaseService()
        user = await supabase_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.patch("/profile", response_model=UpdateProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: CurrentUserId,
) -> UpdateProfileResponse:
    """
    Update user profile information.
    
    If birth data is updated, recalculates astrology.
    """
    try:
        supabase_service = SupabaseService()
        astrology_service = AstrologyService()
        
        # Get current user
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update data
        update_data = {}
        recalculated = False
        
        if request.name is not None:
            update_data["name"] = request.name
        
        if request.email is not None:
            update_data["email"] = request.email
        
        # If birth data changed, recalculate astrology
        if request.birthdate is not None:
            update_data["birthdate"] = request.birthdate.isoformat()
            
            # Recalculate sun sign
            sun_sign = astrology_service.calculate_sun_sign(request.birthdate)
            update_data["sun_sign"] = sun_sign
            recalculated = True
        
        if request.birth_time is not None:
            update_data["birth_time"] = request.birth_time
            
            # Recalculate moon sign if we have all needed data
            birthdate = request.birthdate or user.birthdate
            birth_place = request.birth_place or user.birth_place
            
            moon_sign = astrology_service.calculate_moon_sign(
                birthdate, request.birth_time, birth_place
            )
            if moon_sign:
                update_data["moon_sign"] = moon_sign
                recalculated = True
        
        if request.birth_place is not None:
            update_data["birth_place"] = request.birth_place
        
        # Update in database
        if update_data:
            response = supabase_service.client.table("users").update(
                update_data
            ).eq("id", user_id).execute()
            
            if not response.data:
                raise Exception("Failed to update profile")
            
            # Get updated user
            updated_user = await supabase_service.get_user(user_id)
            
            return UpdateProfileResponse(
                user=updated_user,
                message="Profile updated successfully" + (" (astrology recalculated)" if recalculated else ""),
                recalculated_astrology=recalculated,
            )
        else:
            return UpdateProfileResponse(
                user=user,
                message="No changes made",
                recalculated_astrology=False,
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

