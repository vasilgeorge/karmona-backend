"""
Abstract Base Class for Vector Retrieval
Allows swapping between AWS Knowledge Base and Supabase pgvector
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import MoodType, ActionType


class VectorRetrievalService(ABC):
    """
    Abstract base class for vector retrieval services.
    Implementations can use AWS KB, Supabase pgvector, or other vector stores.
    """

    @abstractmethod
    async def retrieve_context(
        self,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: List[ActionType],
        zodiac_element: str,
        max_results: int = 5,
    ) -> str:
        """
        Retrieve relevant astrology/spiritual context based on user profile.

        Args:
            sun_sign: User's sun sign
            moon_sign: User's moon sign (optional)
            mood: Current mood
            actions: Today's actions
            zodiac_element: Fire/Earth/Air/Water
            max_results: Number of chunks to retrieve

        Returns:
            Formatted string with enriched context for Claude
        """
        pass

    def _build_search_query(
        self,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: List[ActionType],
        zodiac_element: str,
    ) -> str:
        """
        Build semantic search query based on user context.
        Shared across all implementations.
        """
        query_parts = [
            f"{sun_sign} zodiac sign",
        ]

        if moon_sign:
            query_parts.append(f"{moon_sign} moon sign")

        query_parts.append(f"{zodiac_element} element energy")

        # Add mood context
        mood_keywords = {
            "great": "joyful positive uplifting",
            "good": "balanced harmonious",
            "neutral": "centered grounded",
            "sad": "emotional healing transformation",
        }
        query_parts.append(mood_keywords.get(mood, mood))

        # Add action themes
        action_themes = {
            "helped": "service compassion",
            "loved": "love connection",
            "meditated": "meditation spiritual practice",
            "worked": "productivity ambition",
            "created": "creativity manifestation",
            "learned": "wisdom knowledge",
            "exercised": "vitality physical energy",
            "rested": "restoration self-care",
            "argued": "conflict challenge",
            "lied": "shadow work truth",
        }

        for action in actions[:3]:  # Top 3 actions
            theme = action_themes.get(action, action)
            query_parts.append(theme)

        # Combine into rich search query
        query = " ".join(query_parts)
        return query
