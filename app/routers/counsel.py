"""
Cosmic Counsel Router

Provides AI-powered guidance for user decisions based on their astrological profile
and current state.
"""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import CurrentUserId
from app.services import SupabaseService, BedrockService
from app.services.kb_retrieval_service import KBRetrievalService

router = APIRouter(prefix="/counsel", tags=["counsel"])


# Request/Response Models
class CounselRequest(BaseModel):
    """Request for cosmic guidance"""
    question: str = Field(..., min_length=10, max_length=500, description="User's question")
    category: Optional[str] = Field(None, description="career, love, finance, life_change, relationships, other")


class CounselResponse(BaseModel):
    """AI-generated cosmic guidance"""
    id: UUID
    question: str
    answer: str
    category: Optional[str]
    context: dict  # Sun sign, moon sign, mood, energy
    asked_at: datetime


class CounselHistoryResponse(BaseModel):
    """List of past counsel questions"""
    questions: List[CounselResponse]
    total: int
    remaining_today: int  # Questions remaining today (for premium users)


@router.post("", response_model=CounselResponse)
async def ask_question(
    request: CounselRequest,
    user_id: CurrentUserId,
) -> CounselResponse:
    """
    Ask a question and receive cosmic guidance.
    
    Premium users: 5 questions/day
    Free users: 0 questions/day (must upgrade)
    """
    try:
        supabase_service = SupabaseService()
        bedrock_service = BedrockService()
        kb_service = KBRetrievalService()
        
        # Get user data
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is premium (for now, all users are premium - implement later)
        # TODO: Add premium check once Stripe is integrated
        is_premium = True
        
        if not is_premium:
            raise HTTPException(
                status_code=403,
                detail="Cosmic Counsel is a premium feature. Upgrade to access personalized guidance."
            )
        
        # Check daily limit (5 questions/day for premium)
        today = date.today()
        existing_questions = supabase_service.client.table("cosmic_counsel").select("id").eq(
            "user_id", str(user_id)
        ).gte("asked_at", today.isoformat()).execute()
        
        if len(existing_questions.data) >= 5:
            raise HTTPException(
                status_code=429,
                detail="Daily limit reached. You can ask 5 questions per day. Try again tomorrow!"
            )
        
        # Get today's check-in for context
        check_in_result = supabase_service.client.table("daily_check_ins").select("*").eq(
            "user_id", str(user_id)
        ).eq("check_in_date", today.isoformat()).execute()
        
        check_in = check_in_result.data[0] if check_in_result.data else None
        
        # Get cosmic context from KB
        try:
            enriched_context = await kb_service.retrieve_context(
                sun_sign=user.sun_sign,
                question=request.question
            )
        except Exception:
            enriched_context = ""
        
        # Generate AI guidance
        prompt = f"""You are a wise cosmic counselor providing guidance based on astrology and current energy.

User's Profile:
- Sun Sign: {user.sun_sign}
- Moon Sign: {user.moon_sign or 'Unknown'}
{f"- Current Mood: {check_in['mood']}" if check_in else ''}
{f"- Energy Level: {check_in['energy_level']}/10" if check_in else ''}
{f"- Sleep Quality: {check_in['sleep_quality']}" if check_in else ''}

Current Cosmic Energy:
{enriched_context}

User's Question: "{request.question}"
{f"Category: {request.category}" if request.category else ''}

Provide clear, practical guidance in 3-4 sentences:
1. Acknowledge their question with empathy
2. Astrological insight (how their sign influences this)
3. Specific actionable advice
4. Timing consideration (if relevant - "Today is good for..." or "Wait until...")

Be warm, wise, and actionable. Focus on empowerment, not predictions."""

        # Use Bedrock to generate guidance
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        response = bedrock_service.bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body["content"][0]["text"].strip()
        
        # Store in database
        data = {
            "user_id": str(user_id),
            "question": request.question,
            "category": request.category,
            "answer": answer,
            "sun_sign": user.sun_sign,
            "moon_sign": user.moon_sign,
            "mood": check_in["mood"] if check_in else None,
            "energy_level": check_in["energy_level"] if check_in else None,
        }
        
        result = supabase_service.client.table("cosmic_counsel").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save guidance")
        
        counsel = result.data[0]
        
        return CounselResponse(
            id=counsel["id"],
            question=counsel["question"],
            answer=counsel["answer"],
            category=counsel["category"],
            context={
                "sun_sign": counsel["sun_sign"],
                "moon_sign": counsel["moon_sign"],
                "mood": counsel["mood"],
                "energy_level": counsel["energy_level"],
            },
            asked_at=datetime.fromisoformat(counsel["asked_at"].replace("Z", "+00:00"))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate guidance: {str(e)}")


@router.get("/history", response_model=CounselHistoryResponse)
async def get_history(
    user_id: CurrentUserId,
    days: Optional[int] = None,  # None = all time, 1 = today, 7 = last week
) -> CounselHistoryResponse:
    """Get user's counsel history with optional time filter"""
    try:
        supabase_service = SupabaseService()
        
        # Build query
        query = supabase_service.client.table("cosmic_counsel").select("*").eq(
            "user_id", str(user_id)
        ).order("asked_at", desc=True)
        
        # Apply time filter
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            query = query.gte("asked_at", cutoff.isoformat())
        
        result = query.execute()
        
        # Calculate remaining questions for today
        today = date.today()
        today_questions = supabase_service.client.table("cosmic_counsel").select("id").eq(
            "user_id", str(user_id)
        ).gte("asked_at", today.isoformat()).execute()
        
        remaining_today = max(0, 5 - len(today_questions.data))
        
        questions = [
            CounselResponse(
                id=q["id"],
                question=q["question"],
                answer=q["answer"],
                category=q["category"],
                context={
                    "sun_sign": q["sun_sign"],
                    "moon_sign": q["moon_sign"],
                    "mood": q["mood"],
                    "energy_level": q["energy_level"],
                },
                asked_at=datetime.fromisoformat(q["asked_at"].replace("Z", "+00:00"))
            )
            for q in result.data
        ]
        
        return CounselHistoryResponse(
            questions=questions,
            total=len(questions),
            remaining_today=remaining_today
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_stats(user_id: CurrentUserId) -> dict:
    """Get user's counsel usage stats"""
    try:
        supabase_service = SupabaseService()
        today = date.today()
        
        # Questions asked today
        today_result = supabase_service.client.table("cosmic_counsel").select("id").eq(
            "user_id", str(user_id)
        ).gte("asked_at", today.isoformat()).execute()
        
        # Total questions
        total_result = supabase_service.client.table("cosmic_counsel").select("id").eq(
            "user_id", str(user_id)
        ).execute()
        
        return {
            "asked_today": len(today_result.data),
            "remaining_today": max(0, 5 - len(today_result.data)),
            "total_questions": len(total_result.data),
            "daily_limit": 5,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
