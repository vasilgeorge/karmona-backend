"""
AWS Bedrock service for AI-powered reflection generation.
"""

import json
from datetime import date

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.schemas import BedrockReflection, MoodType, ActionType


class BedrockService:
    """Service for generating karma reflections using AWS Bedrock."""

    def __init__(self) -> None:
        """Initialize Bedrock client."""
        session_kwargs = {"region_name": settings.aws_region}

        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": settings.aws_access_key_id,
                    "aws_secret_access_key": settings.aws_secret_access_key,
                }
            )

        self.bedrock_runtime = boto3.client("bedrock-runtime", **session_kwargs)

    async def generate_reflection(
        self,
        name: str,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: list[ActionType],
        note: str | None,
        horoscope: str | None,
        today: date,
    ) -> BedrockReflection:
        """
        Generate a karma reflection using Claude via Bedrock.
        """

        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            name, sun_sign, moon_sign, mood, actions, note, horoscope, today
        )

        try:
            # Call Bedrock with Claude
            response = self.bedrock_runtime.invoke_model(
                modelId=settings.bedrock_model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 500,
                        "temperature": 0.8,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    }
                ),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"]

            # Parse JSON from Claude's response
            reflection_data = json.loads(content)

            return BedrockReflection(
                karma_score=reflection_data["karma_score"],
                reading=reflection_data["reading"],
                rituals=reflection_data["rituals"],
            )

        except (ClientError, json.JSONDecodeError, KeyError) as e:
            print(f"Error generating reflection: {e}")
            # Fallback reflection
            return self._get_fallback_reflection(mood, actions)

    def _build_system_prompt(self) -> str:
        """Build the system prompt for Claude."""
        return """You are Karmona — a gentle, poetic AI guide who blends astrology and karma reflection.

Your tone is:
- Warm, mystical, encouraging
- Never judgmental
- Poetic but accessible
- Focused on growth and balance

You must respond ONLY with valid JSON in this exact format:
{
  "karma_score": <number between 0-100>,
  "reading": "<2-3 sentences connecting their actions to cosmic energy>",
  "rituals": ["<first ritual suggestion>", "<second ritual suggestion>"]
}

Karma score guidelines:
- 80-100: Exceptional balance and positive actions
- 60-79: Good energy, mostly positive
- 40-59: Neutral, mixed energy
- 20-39: Challenging day, room for growth
- 0-19: Difficult energy, needs rebalancing

Ritual suggestions should be:
- Simple, doable actions (3-5 words each)
- Connected to their zodiac element
- Emotionally or spiritually rebalancing"""

    def _build_user_prompt(
        self,
        name: str,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: list[ActionType],
        note: str | None,
        horoscope: str | None,
        today: date,
    ) -> str:
        """Build the user prompt with context."""
        moon_text = f", Moon in {moon_sign}" if moon_sign else ""
        horoscope_text = f"\n\nToday's cosmic energy: {horoscope}" if horoscope else ""
        note_text = f"\n\nPersonal note: {note}" if note else ""

        actions_text = ", ".join(actions)

        return f"""Generate a karma reflection for:

Name: {name}
Sun sign: {sun_sign}{moon_text}
Date: {today.strftime('%B %d, %Y')}
Mood: {mood}
Actions today: {actions_text}{horoscope_text}{note_text}

Create a reflection connecting their actions to their astrological energy and suggest two rituals."""

    def _get_fallback_reflection(
        self, mood: MoodType, actions: list[ActionType]
    ) -> BedrockReflection:
        """Provide a fallback reflection if API fails."""
        # Simple scoring logic
        positive_actions = {"helped", "loved", "meditated", "rested", "created", "learned"}
        score = 50  # Base

        for action in actions:
            if action in positive_actions:
                score += 8
            else:
                score -= 5

        # Adjust for mood
        mood_adjustments = {"great": 10, "good": 5, "neutral": 0, "sad": -10}
        score += mood_adjustments.get(mood, 0)

        score = max(0, min(100, score))  # Clamp to 0-100

        return BedrockReflection(
            karma_score=score,
            reading="Your energy today reflects a journey of self-discovery. The cosmos reminds you that every action ripples through the universe. Continue to nurture your inner light.",
            rituals=["Write gratitude list", "Five mindful breaths"],
        )
