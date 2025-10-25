"""
Weekly forecast endpoints.
"""

from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import CurrentUserId
from app.services import SupabaseService, BedrockService
import json
import boto3
from app.core.config import settings

router = APIRouter(prefix="/forecast", tags=["forecast"])


class WeeklyForecastResponse(BaseModel):
    """Weekly forecast response."""
    
    forecast: str
    sun_sign: str
    week_start: str
    week_end: str


@router.get("/week", response_model=WeeklyForecastResponse)
async def get_weekly_forecast(user_id: CurrentUserId) -> WeeklyForecastResponse:
    """
    Get this week's astrological forecast for the user.
    Personalized based on their sun sign.
    """
    try:
        supabase_service = SupabaseService()
        
        # Get user for sun sign
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is premium (PREMIUM ONLY FEATURE)
        if user.subscription_tier != "premium" or user.subscription_status != "active":
            raise HTTPException(
                status_code=403,
                detail="Weekly Forecast is a premium feature. Upgrade to access personalized weekly guidance."
            )
        
        # Calculate current week (Sunday to Saturday)
        today = date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - timedelta(days=days_since_sunday)
        week_end = week_start + timedelta(days=6)
        
        # Check if forecast already exists for this week
        existing_forecast = supabase_service.client.table("weekly_forecasts").select("*").eq(
            "user_id", user_id
        ).eq(
            "week_start", week_start.isoformat()
        ).execute()
        
        if existing_forecast.data and len(existing_forecast.data) > 0:
            # Return cached forecast
            cached = existing_forecast.data[0]
            print(f"✅ Returning cached forecast for week {week_start}")
            return WeeklyForecastResponse(
                forecast=cached["forecast"],
                sun_sign=cached["sun_sign"],
                week_start=cached["week_start"],
                week_end=cached["week_end"],
            )
        
        # DISABLED: AWS Knowledge Base has been migrated to Supabase pgvector
        # TODO: Re-implement using SupabaseVectorService if needed for forecasts
        enriched_context = ""
        print("ℹ️  KB retrieval skipped for forecast (migrated to Supabase)")

        # Generate new weekly forecast using Claude
        print(f"🤖 Generating new forecast for {user.sun_sign}, week {week_start}")
        prompt = f"""Generate a weekly forecast for {user.sun_sign}.

Week: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}{enriched_context}

The astrological context includes:
- Weekly horoscopes from professional astrologers
- Current planetary transits and aspects
- Moon phases and void-of-course times this week
- Retrograde planets (if any)
- Upcoming eclipses or significant celestial events

Write 2 concise paragraphs (2-3 sentences each):
1. What's actually happening this week for {user.sun_sign} based on the real transits and moon phases above
2. One specific, practical action they can take this week, timed with the actual astrological conditions

Be direct. Use the actual planetary data. Skip generic "your rising aligns with" talk. Use **bold** for key points, add 1 emoji."""
        
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
        forecast_text = response_body["content"][0]["text"]
        
        # Store in database for caching
        try:
            supabase_service.client.table("weekly_forecasts").insert({
                "user_id": user_id,
                "sun_sign": user.sun_sign,
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "forecast": forecast_text,
            }).execute()
            print(f"✅ Cached forecast in database")
        except Exception as db_error:
            print(f"⚠️  Failed to cache forecast: {db_error}")
            # Continue anyway, forecast was generated
        
        return WeeklyForecastResponse(
            forecast=forecast_text,
            sun_sign=user.sun_sign,
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

