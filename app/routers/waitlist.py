"""
Waitlist subscription endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.services import SupabaseService

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


class WaitlistRequest(BaseModel):
    """Waitlist subscription request."""

    email: EmailStr
    name: str | None = None


class WaitlistResponse(BaseModel):
    """Waitlist subscription response."""

    message: str
    email: str
    already_subscribed: bool = False


@router.post("/subscribe", response_model=WaitlistResponse)
async def subscribe_to_waitlist(request: WaitlistRequest) -> WaitlistResponse:
    """
    Subscribe an email to the waitlist.
    Handles duplicates gracefully.
    """
    try:
        supabase_service = SupabaseService()

        # Try to insert the email
        data = {
            "email": request.email,
            "name": request.name,
            "source": "landing",
        }

        response = supabase_service.client.table("waitlist_emails").insert(data).execute()

        if response.data:
            return WaitlistResponse(
                message="You're on the list! We'll notify you when we launch.",
                email=request.email,
                already_subscribed=False,
            )

        # If no data returned, something went wrong
        raise HTTPException(status_code=500, detail="Failed to add to waitlist")

    except Exception as e:
        error_message = str(e).lower()

        # Check if it's a duplicate email error
        if "duplicate" in error_message or "unique" in error_message:
            return WaitlistResponse(
                message="You're already on the list! We'll be in touch soon.",
                email=request.email,
                already_subscribed=True,
            )

        # Other errors
        raise HTTPException(status_code=500, detail=f"Waitlist subscription failed: {str(e)}")

