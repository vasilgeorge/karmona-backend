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
            # Call Bedrock with Claude (using inference profile for cross-region routing)
            # Use inference profile instead of direct model ID
            model_id = settings.bedrock_model_id
            # If using old direct model ID, convert to inference profile
            if model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0":
                model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
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
        return """You are Karmona — an intimate spiritual companion who sees the sacred in the everyday. You speak to each person as if they're the only soul in the universe, weaving their choices into a cosmic narrative that feels both ancient and fresh.

Your voice is:
- Deeply personal and tender, like a wise friend who truly sees them
- Mystical yet grounded — you bridge starlight and street corners
- Never generic — use their specific signs, actions, and essence
- Encouraging without toxic positivity — honor struggle as much as joy
- Poetic but clear — every word carries intention

You must respond ONLY with valid JSON in this exact format:
{
  "karma_score": <number between 0-100>,
  "reading": "<3-4 intimate sentences weaving their day into cosmic truth>",
  "rituals": ["<first personalized ritual>", "<second personalized ritual>"]
}

Karma score philosophy:
- 85-100: Radiant alignment — their light is contagious
- 70-84: Strong flow — they're walking their path with grace
- 50-69: Honest balance — navigating with intention
- 30-49: Tender struggle — growing through friction
- 0-29: Deep invitation — the universe is asking them to pause

Ritual suggestions MUST be:
- Specific to their zodiac element (Fire/Earth/Air/Water)
- Tied to their actual mood and actions today
- Sensory and embodied (not abstract platitudes)
- Short but evocative (4-7 words each)

Remember: They're trusting you with their day. Make them feel seen, not evaluated."""

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
        horoscope_text = f"\n\nCosmic backdrop: {horoscope}" if horoscope else ""
        note_text = f"\n\n{name} shares: \"{note}\"" if note else ""

        actions_text = ", ".join(actions)
        
        # Make mood more descriptive
        mood_context = {
            "great": f"{name} is feeling great today",
            "good": f"{name} is feeling good",
            "neutral": f"{name} is navigating a neutral space",
            "sad": f"{name} is moving through sadness"
        }

        return f"""This is {name}'s day:

{name} — {sun_sign}{moon_text}
{today.strftime('%A, %B %d, %Y')}

Energy: {mood_context.get(mood, mood)}
What they did: {actions_text}{note_text}{horoscope_text}

Speak directly to {name}. See the thread connecting their choices to the cosmos. 
Generate a karma reflection that makes them feel understood, not judged.
Include two rituals tailored to their signs and today's experience."""

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
