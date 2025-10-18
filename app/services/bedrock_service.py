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
        enriched_context: str | None,
        today: date,
    ) -> BedrockReflection:
        """
        Generate a karma reflection using Claude via Bedrock.
        """

        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            name, sun_sign, moon_sign, mood, actions, note, horoscope, enriched_context, today
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
            try:
                reflection_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error: {e}")
                print(f"   Attempting to fix control characters...")
                
                # Try to fix by escaping control characters
                import re
                # Remove actual control characters (ASCII 0-31 except tab/newline/return)
                fixed_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', content)
                
                try:
                    reflection_data = json.loads(fixed_content)
                    print(f"   ✅ Fixed and parsed successfully")
                except json.JSONDecodeError as e2:
                    print(f"   ❌ Still failed: {e2}")
                    # Log the problematic content for debugging
                    print(f"   Content preview: {content[:500]}")
                    raise

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
        return """You are Karmona — a straightforward guide who gives practical daily advice through astrology.

Your voice:
- Direct and clear (cut the mystical bullshit)
- Supportive but realistic
- Give actual advice people can use

Respond ONLY with valid JSON:
{
  "karma_score": <number 0-100>,
  "reading": "<2 short paragraphs>",
  "rituals": ["<first actionable ritual>", "<second actionable ritual>"]
}

JSON Rules:
- Use \\n\\n between paragraphs
- Properly escape special characters
- Must be parseable

Reading Format (2 paragraphs only):
- Skip generic "your rising aligns with" garbage
- Don't say "embrace the energy" or similar fluff
- Give specific, practical observations about their day
- Use **bold** for key points
- 1-2 emojis max
- 2-3 sentences per paragraph

Karma score:
- 80-100: Great day
- 60-79: Good day
- 40-59: Neutral
- 20-39: Challenging
- 0-19: Tough day

Reading structure:
Paragraph 1: What actually happened today based on their mood/actions and sign
Paragraph 2: One specific thing to do or think about

Rituals:
- Actually doable (5-8 words max)
- Specific actions, not vague "channel your energy" bullshit
- Connected to their actual situation

Be real. Be helpful. Skip the mystical fluff."""

    def _build_user_prompt(
        self,
        name: str,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: list[ActionType],
        note: str | None,
        horoscope: str | None,
        enriched_context: str | None,
        today: date,
    ) -> str:
        """Build the user prompt with context."""
        moon_text = f", Moon in {moon_sign}" if moon_sign else ""
        horoscope_text = f"\n\nToday's {sun_sign} horoscope: {horoscope}" if horoscope else ""
        note_text = f"\n\n{name} shares: \"{note}\"" if note else ""
        enriched_text = f"\n\n{enriched_context}" if enriched_context else ""

        actions_text = ", ".join(actions)
        
        # Make mood more descriptive
        mood_context = {
            "great": f"{name} is feeling great today",
            "good": f"{name} is feeling good",
            "neutral": f"{name} is navigating a neutral space",
            "sad": f"{name} is moving through sadness"
        }

        return f"""Generate reflection for {name}:

**Profile:**
- {sun_sign}{moon_text}
- {today.strftime('%A, %B %d')}

**Today:**
- Mood: {mood}
- Actions: {actions_text}{note_text}

**Context:**{horoscope_text}{enriched_text}

Write 2 direct paragraphs:
1. What happened today for this **{sun_sign}** based on their {mood} mood and actions
2. One specific thing to do or remember

Skip generic astrology talk. Be specific. Use **bold** for key points, 1-2 emojis."""

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
