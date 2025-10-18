"""
Friends and compatibility endpoints.
"""

from datetime import date
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import CurrentUserId
from app.services import SupabaseService, AstrologyService
import json
import boto3
from app.core.config import settings

router = APIRouter(prefix="/friends", tags=["friends"])


class Friend(BaseModel):
    """Friend model."""
    id: str
    nickname: str
    sun_sign: str
    moon_sign: str | None
    birth_location: str | None
    current_location: str | None
    age: int | None
    relationship_type: str
    notes: str | None
    created_at: str


class AddFriendRequest(BaseModel):
    """Add friend request."""
    nickname: str
    sun_sign: str
    moon_sign: str | None = None
    birth_location: str | None = None
    current_location: str | None = None
    age: int | None = None
    relationship_type: str
    notes: str | None = None


class CompatibilityReportResponse(BaseModel):
    """Compatibility report response."""
    report: str
    friend_nickname: str
    relationship_type: str
    generated_today: bool


@router.get("/", response_model=List[Friend])
async def get_friends(user_id: CurrentUserId) -> List[Friend]:
    """Get all friends for the current user."""
    try:
        supabase_service = SupabaseService()
        
        response = supabase_service.client.table("friends").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        
        # Note: Could add has_report_today flag here by checking compatibility_reports table
        # For now, frontend will check by trying to fetch (cached reports return instantly)
        
        return [Friend(**friend) for friend in response.data]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get friends: {str(e)}")


@router.post("/", response_model=Friend)
async def add_friend(
    request: AddFriendRequest,
    user_id: CurrentUserId,
) -> Friend:
    """Add a new friend. Free users limited to 3, premium unlimited."""
    try:
        supabase_service = SupabaseService()
        
        # Get user to check subscription
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check limits for free users
        is_premium = (user.subscription_tier == "premium" and user.subscription_status == "active")
        
        if not is_premium:
            # Count existing friends
            existing_friends = supabase_service.client.table("friends").select("id").eq(
                "user_id", str(user_id)
            ).execute()
            
            if len(existing_friends.data) >= 3:
                raise HTTPException(
                    status_code=403,
                    detail="Free tier limited to 3 connections. Upgrade to premium for unlimited connections."
                )
        
        friend_data = {
            "user_id": user_id,
            **request.dict()
        }
        
        response = supabase_service.client.table("friends").insert(
            friend_data
        ).execute()
        
        if not response.data:
            raise Exception("Failed to add friend")
        
        return Friend(**response.data[0])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add friend: {str(e)}")


@router.delete("/{friend_id}")
async def delete_friend(friend_id: str, user_id: CurrentUserId):
    """Delete a friend."""
    try:
        supabase_service = SupabaseService()
        
        # Verify ownership
        friend = supabase_service.client.table("friends").select("*").eq(
            "id", friend_id
        ).eq("user_id", user_id).execute()
        
        if not friend.data:
            raise HTTPException(status_code=404, detail="Friend not found")
        
        supabase_service.client.table("friends").delete().eq("id", friend_id).execute()
        
        return {"message": "Friend deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete friend: {str(e)}")


@router.post("/{friend_id}/compatibility", response_model=CompatibilityReportResponse)
async def generate_compatibility_report(
    friend_id: str,
    user_id: CurrentUserId,
) -> CompatibilityReportResponse:
    """
    Generate compatibility report between user and friend.
    Cached per day - same friend gets same report for the day.
    """
    try:
        supabase_service = SupabaseService()
        astrology_service = AstrologyService()
        
        # Get user
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get friend
        friend_response = supabase_service.client.table("friends").select("*").eq(
            "id", friend_id
        ).eq("user_id", user_id).execute()
        
        if not friend_response.data:
            raise HTTPException(status_code=404, detail="Friend not found")
        
        friend = friend_response.data[0]
        
        # Check for cached report today
        today = date.today()
        cached_report = supabase_service.client.table("compatibility_reports").select("*").eq(
            "friend_id", friend_id
        ).eq("generated_date", today.isoformat()).execute()
        
        if cached_report.data and len(cached_report.data) > 0:
            print(f"✅ Returning cached compatibility report")
            return CompatibilityReportResponse(
                report=cached_report.data[0]["report"],
                friend_nickname=friend["nickname"],
                relationship_type=friend["relationship_type"],
                generated_today=True,
            )
        
        # Generate new compatibility report
        print(f"🤖 Generating compatibility report: {user.name} + {friend['nickname']}")
        
        # Get elements
        user_element = astrology_service.get_zodiac_element(user.sun_sign)
        friend_element = astrology_service.get_zodiac_element(friend["sun_sign"])
        
        # Relationship-specific prompts
        relationship_prompts = {
            'romantic': 'Focus on emotional connection, communication styles, and attraction dynamics.',
            'professional': 'Focus on work styles, collaboration, and professional strengths.',
            'friend': 'Focus on shared interests, communication, and how to support each other.',
            'family': 'Focus on understanding differences, family dynamics, and patience.',
            'acquaintance': 'Focus on first impressions and potential for deeper connection.',
            'mentor': 'Focus on learning dynamic, guidance style, and growth opportunities.',
        }
        
        context = relationship_prompts.get(friend['relationship_type'], 'Focus on how they interact and connect.')
        
        prompt = f"""Compatibility: **{user.sun_sign}** + **{friend['sun_sign']}** ({friend['relationship_type']})

{context}

Write 2-3 sentences for TODAY ({today.strftime('%A')}):
1. One real dynamic between these signs - skip generic "water meets fire" bullshit
2. One specific thing to do or avoid today

Be direct and practical. Use **bold** for signs, 1 emoji."""
        
        bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        
        response = bedrock_runtime.invoke_model(
            modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.8,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            }),
        )
        
        response_body = json.loads(response["body"].read())
        report_text = response_body["content"][0]["text"]
        
        # Cache in database
        try:
            supabase_service.client.table("compatibility_reports").insert({
                "user_id": user_id,
                "friend_id": friend_id,
                "report": report_text,
                "relationship_type": friend["relationship_type"],
                "generated_date": today.isoformat(),
            }).execute()
            print(f"✅ Cached compatibility report")
        except Exception as db_error:
            print(f"⚠️  Failed to cache report: {db_error}")
        
        return CompatibilityReportResponse(
            report=report_text,
            friend_nickname=friend["nickname"],
            relationship_type=friend["relationship_type"],
            generated_today=True,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility generation failed: {str(e)}")
