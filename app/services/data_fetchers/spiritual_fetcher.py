"""
Spiritual Data Fetcher
Scrapes wisdom from spiritual and philosophical sources
"""

from datetime import date
from typing import Dict, Any
import asyncio

from app.services.browser_agent_client import BrowserAgentClient


class SpiritualDataFetcher:
    """
    Fetches spiritual wisdom and teachings from various sources.
    
    Sources:
    - Daily spiritual quotes/teachings
    - Sacred wisdom aligned with astrological themes
    - Mindfulness and intention-setting guidance
    """
    
    def __init__(self):
        """Initialize spiritual data fetcher."""
        self.browser_client = BrowserAgentClient()
    
    async def fetch_daily_wisdom(self, theme: str | None = None) -> Dict[str, Any]:
        """
        Fetch daily spiritual wisdom.
        
        Args:
            theme: Optional theme to focus on (e.g., "earth", "balance", "growth")
            
        Returns:
            Dictionary with spiritual wisdom
        """
        # Tiny Buddha has good daily wisdom
        url = "https://tinybuddha.com/"
        
        theme_text = f" related to {theme}" if theme else ""
        
        prompt = f"""
        Visit this spiritual wisdom website and extract:
        
        1. The most recent or featured spiritual teaching/quote
        2. Any daily wisdom or reflection prompt{theme_text}
        3. Practical mindfulness suggestions
        
        Summarize in 1-2 sentences that feel warm and grounding.
        Focus on actionable spiritual insights, not just quotes.
        """
        
        result = await self.browser_client.fetch_from_url(url, prompt)
        
        return {
            "source": "tinybuddha.com",
            "wisdom": result.get("data", "Spiritual wisdom unavailable"),
            "success": result.get("success", False),
        }
    
    async def fetch_intention_guidance(self, zodiac_element: str) -> Dict[str, Any]:
        """
        Fetch intention-setting guidance aligned with zodiac element.
        
        Args:
            zodiac_element: "Fire", "Earth", "Air", or "Water"
            
        Returns:
            Element-specific spiritual guidance
        """
        # Map elements to spiritual themes
        element_themes = {
            "Fire": "passion, action, transformation",
            "Earth": "grounding, manifestation, stability",
            "Air": "clarity, communication, freedom",
            "Water": "emotion, intuition, flow",
        }
        
        theme = element_themes.get(zodiac_element, "balance")
        
        url = "https://www.mindbodygreen.com/articles"
        
        prompt = f"""
        Visit this wellness/spirituality website and extract:
        
        Find recent articles or guidance about {theme}.
        Extract 1-2 key insights about setting intentions or spiritual practices
        related to {zodiac_element} element energy.
        
        Summarize in 1-2 sentences, focusing on embodied practices.
        """
        
        result = await self.browser_client.fetch_from_url(url, prompt)
        
        return {
            "source": "mindbodygreen.com",
            "element": zodiac_element,
            "guidance": result.get("data", "Intention guidance unavailable"),
            "success": result.get("success", False),
        }
    
    async def fetch_enriched_spiritual_context(
        self,
        zodiac_element: str,
    ) -> str:
        """
        Fetch comprehensive spiritual context from multiple sources.
        
        Args:
            zodiac_element: User's zodiac element (Fire/Earth/Air/Water)
            
        Returns:
            Formatted string with enriched spiritual context for LLM
        """
        # Fetch from multiple sources in parallel
        tasks = [
            self.fetch_daily_wisdom(theme=zodiac_element.lower()),
            self.fetch_intention_guidance(zodiac_element),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results for LLM
        context_parts = []
        
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                if "wisdom" in result:
                    context_parts.append(f"Spiritual Wisdom: {result['wisdom']}")
                if "guidance" in result:
                    context_parts.append(f"Elemental Guidance ({result['element']}): {result['guidance']}")
        
        if not context_parts:
            return "Spiritual context temporarily unavailable."
        
        return "\n\n".join(context_parts)

