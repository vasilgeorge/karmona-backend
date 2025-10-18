"""
Tarot reading endpoints.
"""

import json
import random
from datetime import date
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import CurrentUserId
from app.services import SupabaseService
import boto3
from app.core.config import settings

router = APIRouter(prefix="/tarot", tags=["tarot"])


class TarotCard(BaseModel):
    """Tarot card model."""
    id: int
    name: str
    arcana: str
    number: int
    upright_meaning: str
    reversed_meaning: str
    keywords: list[str]
    image: str


class DrawCardRequest(BaseModel):
    """Draw card request."""
    question: str | None = None


class TarotReadingResponse(BaseModel):
    """Tarot reading response."""
    card: TarotCard
    upright: bool
    interpretation: str
    question: str | None


# Load tarot cards
TAROT_CARDS_PATH = Path(__file__).parent.parent / "data" / "tarot_cards.json"
with open(TAROT_CARDS_PATH) as f:
    TAROT_CARDS = json.load(f)


@router.post("/draw", response_model=TarotReadingResponse)
async def draw_daily_card(
    request: DrawCardRequest,
    user_id: CurrentUserId,
) -> TarotReadingResponse:
    """
    Draw a single tarot card with AI interpretation.
    """
    try:
        supabase_service = SupabaseService()
        
        # Get user for personalization
        user = await supabase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Randomly select a card
        card_data = random.choice(TAROT_CARDS)
        card = TarotCard(**card_data)
        
        # Randomly determine upright or reversed
        upright = random.choice([True, False])
        
        # Generate AI interpretation
        today = date.today()
        meaning = card.upright_meaning if upright else card.reversed_meaning
        orientation = "Upright" if upright else "Reversed"
        
        prompt = f"""Tarot: **{card.name}** ({orientation})

Meaning: {meaning}
Keywords: {', '.join(card.keywords)}

For: {user.name} ({user.sun_sign})
Question: {request.question or "What energy should I focus on today?"}
Date: {today.strftime('%A, %B %d')}

Write 2-3 sentences:
1. What this card means for them today - be specific, skip generic "embrace the journey" talk
2. One concrete action to take

Be direct. Use **bold** for card name, 1 emoji."""
        
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
                "max_tokens": 300,
                "temperature": 0.8,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            }),
        )
        
        response_body = json.loads(response["body"].read())
        interpretation = response_body["content"][0]["text"]
        
        return TarotReadingResponse(
            card=card,
            upright=upright,
            interpretation=interpretation,
            question=request.question,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tarot reading failed: {str(e)}")
