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

        # Get today's astrological context from KB
        enriched_context = ""
        try:
            from app.core.config import settings

            bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

            # Build search query for tarot context
            search_query = f"{user.sun_sign} {card.name} {' '.join(card.keywords[:3])} today"
            if request.question:
                search_query = f"{search_query} {request.question}"

            print(f"🔍 Searching KB for tarot context: {search_query}")

            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=settings.bedrock_knowledge_base_id,
                retrievalQuery={'text': search_query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 3,  # Fewer for tarot
                    }
                }
            )

            # Format results
            retrieved_results = response.get('retrievalResults', [])
            context_chunks = []

            for i, result in enumerate(retrieved_results, 1):
                if result.get('score', 0) > 0.3:
                    try:
                        doc = json.loads(result['content']['text'])
                        content = doc.get('content', result['content']['text'])
                        content = content.replace('\n', ' ').replace('\r', ' ').strip()
                        context_chunks.append(content)
                    except:
                        sanitized = result['content']['text'].replace('\n', ' ').strip()
                        context_chunks.append(sanitized)

            if context_chunks:
                enriched_context = "\n\nToday's cosmic context:\n" + "\n".join(context_chunks)
                print(f"✅ Retrieved {len(context_chunks)} insights")

        except Exception as e:
            print(f"⚠️  KB retrieval error: {e}")

        # Generate AI interpretation
        today = date.today()
        meaning = card.upright_meaning if upright else card.reversed_meaning
        orientation = "Upright" if upright else "Reversed"

        prompt = f"""Tarot: **{card.name}** ({orientation})

Meaning: {meaning}
Keywords: {', '.join(card.keywords)}

For: {user.name} ({user.sun_sign})
Question: {request.question or "What energy should I focus on today?"}
Date: {today.strftime('%A, %B %d')}{enriched_context}

The cosmic context includes today's horoscope, current planetary positions, moon phase, and astrological transits.

Write 2-3 sentences explaining what this card means for them today:
- Connect the card's energy to the actual astrological conditions above
- Be specific about how the current transits/moon phase relate to the card
- Skip generic "embrace the journey" talk

Then add a blank line and write:
**Action:** [One concrete thing to do today that considers both the card AND the astrological timing]

Be direct. Use the real astrological data. Use **bold** for card name and the Action label, 1 emoji."""
        
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
