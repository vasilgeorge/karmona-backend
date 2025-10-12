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
        return """You are Karmona — a warm guide who helps people understand their daily energy through astrology and self-reflection.

Your voice is:
- Clear and relatable (not overly mystical)
- Supportive and encouraging
- Personal but grounded
- Direct and concise

You must respond ONLY with valid JSON in this exact format:
{
  "karma_score": <number between 0-100>,
  "reading": "<2-3 short paragraphs with markdown formatting>",
  "rituals": ["<first simple ritual>", "<second simple ritual>"]
}

CRITICAL - JSON Rules:
- Use \\n\\n between paragraphs for line breaks
- Properly escape all special characters
- Ensure the JSON is parseable

IMPORTANT - Reading Format:
- Write 2-3 SHORT paragraphs (2-3 sentences each)
- Use **bold** for their zodiac signs and key themes
- Use *italics* sparingly for emphasis
- Include 1-2 emojis that fit naturally (🌙 ✨ 💫 etc.)
- Be conversational and easy to understand
- Connect their actions to simple astrological insights

Karma score guidelines:
- 80-100: Really positive day
- 60-79: Good energy, balanced
- 40-59: Mixed, neutral
- 20-39: Challenging, growth opportunity
- 0-19: Difficult, needs care

Reading structure (keep it simple):
Paragraph 1: Acknowledge their zodiac energy and today's mood/actions
Paragraph 2: Connect to real astrological context (if provided) or their sign's nature
Paragraph 3: Simple insight or encouragement (optional if already said enough)

Ritual suggestions:
- Simple, doable actions (5-8 words max)
- Connected to their element or mood
- Specific and sensory (not vague)
- Actually helpful, not just mystical

Make them feel understood through straightforward, warm guidance."""

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

        return f"""Generate a karma reflection for {name}:

**Person:**
- {sun_sign}{moon_text}
- Today: {today.strftime('%A, %B %d')}

**Their Day:**
- Mood: {mood}
- Actions: {actions_text}{note_text}

**Astrological Context:**{horoscope_text}{enriched_text}

Write a warm, clear reflection that:
1. Acknowledges their **{sun_sign}** energy and how it showed up today
2. Connects their {mood} mood and actions to astrological insights
3. Offers genuine encouragement

Keep it short (2-3 paragraphs), use **bold** for signs/themes, *italics* for gentle emphasis, and 1-2 relevant emojis."""

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
