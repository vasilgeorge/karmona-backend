"""
Journey summary endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.core.auth import CurrentUserId
from app.services import SupabaseService, BedrockService
from pydantic import BaseModel

router = APIRouter(prefix="/summary", tags=["summary"])


class JourneySummaryResponse(BaseModel):
    """Journey summary response."""
    
    summary: str
    reflections_analyzed: int
    time_period: str


@router.post("/journey", response_model=JourneySummaryResponse)
async def generate_journey_summary(
    user_id: CurrentUserId,
    days: int = 7,
) -> JourneySummaryResponse:
    """
    Generate a summary of the user's spiritual journey based on recent reflections.
    
    Args:
        days: Number of days to analyze (default 7)
        
    Returns:
        AI-generated summary of their journey
    """
    try:
        supabase_service = SupabaseService()
        bedrock_service = BedrockService()
        
        # Get user's recent reflections
        reports = await supabase_service.get_user_history(user_id, limit=days)
        
        if not reports:
            raise HTTPException(status_code=404, detail="No reflections found")
        
        # Get user info for context
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build summary prompt for Claude
        reflections_text = []
        for report in reports:
            date_str = report.date.strftime('%b %d')
            reflections_text.append(
                f"{date_str}: Karma {report.karma_score}, Mood: {report.mood}, "
                f"Actions: {', '.join(report.actions[:3])}"
            )
        
        prompt = f"""Analyze {user.name}'s spiritual journey over the past {len(reports)} days:

{chr(10).join(reflections_text)}

**{user.name}** is a **{user.sun_sign}**{' with Moon in ' + user.moon_sign if user.moon_sign else ''}.

Write a warm, insightful summary (2-3 paragraphs) that:
1. Identifies patterns in their moods and actions
2. Highlights growth or themes in their journey  
3. Offers gentle guidance based on their astrology

Use **bold** for key insights, *italics* for emphasis, and 1-2 emojis. Keep it encouraging and specific to them."""
        
        # Generate summary using Claude
        import json
        import boto3
        from app.core.config import settings
        
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
                "max_tokens": 400,
                "temperature": 0.7,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            }),
        )
        
        response_body = json.loads(response["body"].read())
        summary_text = response_body["content"][0]["text"]
        
        return JourneySummaryResponse(
            summary=summary_text,
            reflections_analyzed=len(reports),
            time_period=f"Last {len(reports)} days",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

