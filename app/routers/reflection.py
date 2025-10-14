"""
Daily reflection generation endpoints.
"""

from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUserId
from app.models.schemas import DailyInputRequest, ReflectionResponse
from app.services import SupabaseService, AstrologyService, BedrockService
from app.services.kb_retrieval_service import KBRetrievalService

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
        kb_retrieval_service = KBRetrievalService()

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
        
        # If mood/actions not provided, fetch from daily check-in
        mood = request.mood
        actions = request.actions
        note = request.note
        
        if not mood or not actions:
            # Fetch today's check-in
            check_in_result = supabase_service.client.table("daily_check_ins").select("*").eq(
                "user_id", str(user_id)
            ).eq("check_in_date", today.isoformat()).execute()
            
            if not check_in_result.data:
                raise HTTPException(
                    status_code=400,
                    detail="Please complete your daily check-in first"
                )
            
            check_in = check_in_result.data[0]
            
            # Map check-in data to mood/actions
            # Mood mapping: great -> great, good -> good, okay -> neutral, low/struggling -> sad
            mood_map = {
                "great": "great",
                "good": "good",
                "okay": "neutral",
                "low": "sad",
                "struggling": "sad",
            }
            mood = mood_map.get(check_in["mood"], "neutral")
            
            # Generate actions based on check-in data
            actions = []
            
            # Energy-based actions
            if check_in["energy_level"] >= 7:
                actions.append("exercised")
            elif check_in["energy_level"] <= 3:
                actions.append("rested")
            
            # Sleep-based actions
            if check_in["sleep_quality"] in ["excellent", "good"]:
                actions.append("rested")
            
            # Mood-based actions
            if check_in["mood"] in ["great", "good"]:
                actions.append("meditated")
                if check_in.get("gratitude"):
                    actions.append("loved")
            
            # Ensure we have at least one action
            if not actions:
                actions = ["meditated"]
            
            # Use check-in text as note if available
            if not note:
                note_parts = []
                if check_in.get("feelings"):
                    note_parts.append(f"Feeling: {check_in['feelings']}")
                if check_in.get("challenges"):
                    note_parts.append(f"Challenges: {check_in['challenges']}")
                if check_in.get("gratitude"):
                    note_parts.append(f"Grateful for: {check_in['gratitude']}")
                note = " | ".join(note_parts) if note_parts else None

        # Get today's horoscope (legacy API - still useful)
        horoscope = await astrology_service.get_daily_horoscope(user.sun_sign)
        
        # NEW: Get zodiac element for KB search
        zodiac_element = astrology_service.get_zodiac_element(user.sun_sign)
        
        # NEW: Retrieve enriched context from Knowledge Base (with timeout)
        print(f"🔍 Retrieving KB context for {user.sun_sign}...")
        try:
            enriched_context = await kb_retrieval_service.retrieve_context(
                sun_sign=user.sun_sign,
                moon_sign=user.moon_sign,
                mood=request.mood,
                actions=request.actions,
                zodiac_element=zodiac_element,
                max_results=5,
            )
        except Exception as kb_error:
            print(f"⚠️  KB retrieval failed: {kb_error}, continuing without enriched context")
            enriched_context = ""  # Continue without KB data if it fails

        # Generate reflection via Bedrock with enriched KB data
        bedrock_reflection = await bedrock_service.generate_reflection(
            name=user.name,
            sun_sign=user.sun_sign,
            moon_sign=user.moon_sign,
            mood=mood,
            actions=actions,
            note=note,
            horoscope=horoscope,
            enriched_context=enriched_context,  # NEW: KB-enhanced data
            today=today,
        )

        # Store in database (using authenticated user_id)
        report = await supabase_service.create_daily_report(
            user_id=user_id,
            report_date=today,
            mood=mood,
            actions=actions,
            karma_score=bedrock_reflection.karma_score,
            reading=bedrock_reflection.reading,
            rituals=bedrock_reflection.rituals,
            note=note,
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
