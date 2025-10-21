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
    friend_id: Optional[UUID] = Field(None, description="ID of friend to include in counsel context")


class CounselResponse(BaseModel):
    """AI-generated cosmic guidance"""
    id: UUID
    question: str
    answer: str
    category: Optional[str]
    context: dict  # Sun sign, moon sign, mood, energy
    asked_at: datetime
    friend_id: Optional[UUID] = None
    friend_nickname: Optional[str] = None
    friend_sun_sign: Optional[str] = None
    friend_moon_sign: Optional[str] = None


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
        
        # Check if user is premium
        is_premium = (
            user.subscription_tier == "premium" and 
            user.subscription_status == "active"
        )
        
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
        
        # Get friend data if friend_id provided
        friend_context = ""
        if request.friend_id:
            friend_result = supabase_service.client.table("friends").select("*").eq(
                "id", str(request.friend_id)
            ).eq("user_id", str(user_id)).execute()
            
            if friend_result.data:
                friend = friend_result.data[0]
                friend_context = f"""
FRIEND CONTEXT:
- Name: {friend['nickname']}
- Sun Sign: {friend['sun_sign']}
- Moon Sign: {friend['moon_sign'] or 'Unknown'}
- Age: {friend['age'] or 'Unknown'}
- Relationship: {friend['relationship_type']}
- Location: {friend['current_location'] or 'Unknown'}
- Notes: {friend['notes'] or 'None'}
"""
        
        # Get cosmic context from KB
        # Build a semantic query from the user's question + their profile
        try:
            # Use retrieve() directly with a custom query for counsel
            import boto3
            from app.core.config import settings

            bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

            # Build search query: user's question + their astrological profile
            search_query = f"{user.sun_sign} {request.question}"
            if user.moon_sign:
                search_query = f"{search_query} {user.moon_sign} moon"
            if request.category:
                search_query = f"{search_query} {request.category}"

            print(f"🔍 Searching KB for counsel: {search_query}")

            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=settings.bedrock_knowledge_base_id,
                retrievalQuery={'text': search_query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5,
                    }
                }
            )

            # Format results
            retrieved_results = response.get('retrievalResults', [])
            context_chunks = []

            for i, result in enumerate(retrieved_results, 1):
                if result.get('score', 0) > 0.3:
                    try:
                        import json
                        doc = json.loads(result['content']['text'])
                        content = doc.get('content', result['content']['text'])
                        content = content.replace('\n', ' ').replace('\r', ' ').strip()
                        context_chunks.append(f"Insight {i}: {content}")
                    except:
                        sanitized = result['content']['text'].replace('\n', ' ').strip()
                        context_chunks.append(f"Insight {i}: {sanitized}")

            if context_chunks:
                enriched_context = "ASTROLOGICAL CONTEXT:\n" + "\n".join(context_chunks)
                print(f"✅ Retrieved {len(context_chunks)} insights from KB")
            else:
                enriched_context = ""
                print("⚠️  No relevant KB results")

        except Exception as e:
            print(f"⚠️  KB retrieval error: {e}")
            enriched_context = ""
        
        # Generate AI guidance
        prompt = f"""Cosmic counselor giving straightforward advice based on real-time astrological data.

Profile:
- Sun: {user.sun_sign}
- Moon: {user.moon_sign or 'Unknown'}
{f"- Mood: {check_in['mood']}" if check_in else ''}
{f"- Energy: {check_in['energy_level']}/10" if check_in else ''}

{friend_context if friend_context else ""}

Question: "{request.question}"
{f"Category: {request.category}" if request.category else ''}

{enriched_context if enriched_context else ""}

The context above includes:
- Today's horoscopes from multiple astrologers (Astrostyle, Cafe Astrology)
- Current planetary positions and transits
- Moon phase and current moon sign
- Planets in retrograde (if any)
- Spiritual wisdom and timing guidance

Give 3-4 direct sentences:
1. Address their question directly - no empathy theatre
2. One astrological insight from the data above that actually applies to their situation
3. If a friend is mentioned, consider their astrological compatibility and relationship dynamics
4. Specific action to take today
5. Timing note if relevant (moon phase, retrograde, transit)

Be real. Use the actual astrological data. Skip generic "embrace your power" bullshit."""

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
            modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Use inference profile
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body["content"][0]["text"].strip()
        
        # Get friend data if friend_id provided (for storage)
        friend_data = None
        if request.friend_id:
            friend_result = supabase_service.client.table("friends").select("*").eq(
                "id", str(request.friend_id)
            ).eq("user_id", str(user_id)).execute()
            
            if friend_result.data:
                friend_data = friend_result.data[0]
        
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
            "friend_id": str(request.friend_id) if request.friend_id else None,
            "friend_nickname": friend_data["nickname"] if friend_data else None,
            "friend_sun_sign": friend_data["sun_sign"] if friend_data else None,
            "friend_moon_sign": friend_data["moon_sign"] if friend_data else None,
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
            asked_at=datetime.fromisoformat(counsel["asked_at"].replace("Z", "+00:00")),
            friend_id=counsel.get("friend_id"),
            friend_nickname=counsel.get("friend_nickname"),
            friend_sun_sign=counsel.get("friend_sun_sign"),
            friend_moon_sign=counsel.get("friend_moon_sign")
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


@router.delete("/{question_id}")
async def delete_question(
    question_id: UUID,
    user_id: CurrentUserId,
) -> dict:
    """Delete a counsel question"""
    try:
        supabase_service = SupabaseService()

        # Check if question exists and belongs to user
        existing = supabase_service.client.table("cosmic_counsel").select("id").eq(
            "id", str(question_id)
        ).eq("user_id", str(user_id)).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Question not found or access denied")

        # Delete the question
        supabase_service.client.table("cosmic_counsel").delete().eq(
            "id", str(question_id)
        ).eq("user_id", str(user_id)).execute()

        return {"message": "Question deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete question: {str(e)}")
