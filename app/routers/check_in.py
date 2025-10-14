"""
Daily Check-In Router

Handles user's daily wellness check-in data that enriches all AI content.
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import CurrentUserId
from app.services import SupabaseService

router = APIRouter(prefix="/check-in", tags=["check-in"])


# Request/Response Models
class CheckInRequest(BaseModel):
    """Daily check-in submission"""
    mood: str = Field(..., description="Overall mood: great, good, okay, low, struggling")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level 1-10")
    sleep_quality: str = Field(..., description="Sleep quality: excellent, good, fair, poor, terrible")
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description="Hours of sleep")
    on_menstrual_cycle: Optional[bool] = Field(None, description="Currently on menstrual cycle (null if N/A)")
    cycle_phase: Optional[str] = Field(None, description="Cycle phase if applicable")
    feelings: Optional[str] = Field(None, description="How you're feeling today")
    challenges: Optional[str] = Field(None, description="Any challenges or concerns")
    gratitude: Optional[str] = Field(None, description="What you're grateful for")
    notes: Optional[str] = Field(None, description="Any additional notes")


class CheckInResponse(BaseModel):
    """Daily check-in data"""
    id: UUID
    user_id: UUID
    mood: str
    energy_level: int
    sleep_quality: str
    sleep_hours: Optional[float]
    on_menstrual_cycle: Optional[bool]
    cycle_phase: Optional[str]
    feelings: Optional[str]
    challenges: Optional[str]
    gratitude: Optional[str]
    notes: Optional[str]
    check_in_date: date
    created_at: datetime


class CheckInStatusResponse(BaseModel):
    """Check-in status for today"""
    needs_check_in: bool
    last_check_in_date: Optional[date]
    hours_since_last: Optional[float]


@router.get("/status", response_model=CheckInStatusResponse)
async def get_check_in_status(user_id: CurrentUserId) -> CheckInStatusResponse:
    """
    Check if user needs to complete today's check-in.
    
    Returns needs_check_in=True if:
    - No check-in exists for today, OR
    - Last check-in was more than 24 hours ago
    """
    try:
        supabase_service = SupabaseService()
        # Get most recent check-in
        result = await supabase_service.supabase.table("daily_check_ins").select("*").eq(
            "user_id", str(user_id)
        ).order("check_in_date", desc=True).limit(1).execute()
        
        if not result.data:
            # No check-ins at all
            return CheckInStatusResponse(
                needs_check_in=True,
                last_check_in_date=None,
                hours_since_last=None
            )
        
        last_check_in = result.data[0]
        last_date = datetime.strptime(last_check_in["check_in_date"], "%Y-%m-%d").date()
        today = date.today()
        
        # Check if today's check-in exists
        if last_date >= today:
            return CheckInStatusResponse(
                needs_check_in=False,
                last_check_in_date=last_date,
                hours_since_last=0.0
            )
        
        # Calculate hours since last check-in
        last_created = datetime.fromisoformat(last_check_in["created_at"].replace("Z", "+00:00"))
        hours_since = (datetime.now(last_created.tzinfo) - last_created).total_seconds() / 3600
        
        return CheckInStatusResponse(
            needs_check_in=True,
            last_check_in_date=last_date,
            hours_since_last=round(hours_since, 1)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")


@router.post("", response_model=CheckInResponse)
async def submit_check_in(
    request: CheckInRequest,
    user_id: CurrentUserId,
) -> CheckInResponse:
    """Submit daily check-in"""
    try:
        supabase_service = SupabaseService()
        today = date.today()
        
        # Check if already checked in today
        existing = await supabase_service.supabase.table("daily_check_ins").select("id").eq(
            "user_id", str(user_id)
        ).eq("check_in_date", today.isoformat()).execute()
        
        if existing.data:
            raise HTTPException(
                status_code=400, 
                detail="You've already completed today's check-in"
            )
        
        # Insert check-in
        data = {
            "user_id": str(user_id),
            "mood": request.mood,
            "energy_level": request.energy_level,
            "sleep_quality": request.sleep_quality,
            "sleep_hours": request.sleep_hours,
            "on_menstrual_cycle": request.on_menstrual_cycle,
            "cycle_phase": request.cycle_phase,
            "feelings": request.feelings,
            "challenges": request.challenges,
            "gratitude": request.gratitude,
            "notes": request.notes,
            "check_in_date": today.isoformat(),
        }
        
        result = await supabase_service.supabase.table("daily_check_ins").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save check-in")
        
        return CheckInResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit check-in: {str(e)}")


@router.get("/latest", response_model=Optional[CheckInResponse])
async def get_latest_check_in(user_id: CurrentUserId) -> Optional[CheckInResponse]:
    """
    Get user's most recent check-in data.
    Used to enrich AI-generated content with current wellness context.
    """
    try:
        supabase_service = SupabaseService()
        result = await supabase_service.supabase.table("daily_check_ins").select("*").eq(
            "user_id", str(user_id)
        ).order("check_in_date", desc=True).limit(1).execute()
        
        if not result.data:
            return None
        
        return CheckInResponse(**result.data[0])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest check-in: {str(e)}")

