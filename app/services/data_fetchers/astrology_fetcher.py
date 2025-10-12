"""
Astrology Data Fetcher
Scrapes real-time astrological data from multiple sources
"""

from datetime import date
from typing import Dict, Any

from app.services.browser_agent_client import BrowserAgentClient


class AstrologyDataFetcher:
    """
    Fetches real-time astrology data from trusted sources.
    
    Sources:
    - Astro.com (planetary transits)
    - Cafe Astrology (daily aspects)
    - The Pattern (cosmic insights)
    """
    
    def __init__(self):
        """Initialize astrology data fetcher."""
        self.browser_client = BrowserAgentClient()
        
    async def fetch_planetary_transits(self, sun_sign: str, today: date) -> Dict[str, Any]:
        """
        Fetch today's planetary transits affecting the given sun sign.
        
        Args:
            sun_sign: User's sun sign (e.g., "Capricorn")
            today: Current date
            
        Returns:
            Dictionary with planetary transit information
        """
        url = f"https://www.astro.com/horoscope/daily_horoscope.aspx?sign={sun_sign.lower()}"
        
        prompt = f"""
        Navigate to this astrology website and extract TODAY's planetary information for {sun_sign}:
        
        Please extract:
        1. Major planetary transits happening today
        2. Which planets are affecting {sun_sign} specifically
        3. The overall cosmic energy or theme for today
        4. Any significant aspects (conjunctions, squares, trines)
        
        Summarize in 2-3 sentences focusing on actionable insights.
        """
        
        result = await self.browser_client.fetch_from_url(url, prompt)
        
        return {
            "source": "astro.com",
            "sign": sun_sign,
            "date": today.isoformat(),
            "transits": result.get("data", "Planetary transits unavailable"),
            "success": result.get("success", False),
        }
    
    async def fetch_daily_cosmic_events(self, today: date) -> Dict[str, Any]:
        """
        Fetch significant cosmic events happening today.
        
        Args:
            today: Current date
            
        Returns:
            Dictionary with cosmic events (moon phase, retrogrades, etc.)
        """
        url = "https://www.cafeastrology.com/dailyaspects.html"
        
        prompt = f"""
        Visit this astrology website and extract TODAY'S cosmic events ({today.strftime('%B %d, %Y')}):
        
        Extract:
        1. Current moon phase and sign
        2. Any planets in retrograde
        3. Major aspects happening today
        4. Overall cosmic weather summary
        
        Summarize in 2-3 sentences with mystical but accessible language.
        """
        
        result = await self.browser_client.fetch_from_url(url, prompt)
        
        return {
            "source": "cafeastrology.com",
            "date": today.isoformat(),
            "cosmic_events": result.get("data", "Cosmic events unavailable"),
            "success": result.get("success", False),
        }
    
    async def fetch_enriched_astrology_context(
        self,
        sun_sign: str,
        moon_sign: str | None,
        today: date,
    ) -> str:
        """
        Fetch comprehensive astrology context from multiple sources.
        
        This is the main method to call - it aggregates data from multiple sources.
        
        Returns:
            Formatted string with enriched astrology context for LLM
        """
        # Fetch from multiple sources in parallel
        tasks = [
            self.fetch_planetary_transits(sun_sign, today),
            self.fetch_daily_cosmic_events(today),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results for LLM
        context_parts = []
        
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                if "transits" in result:
                    context_parts.append(f"Planetary Transits: {result['transits']}")
                if "cosmic_events" in result:
                    context_parts.append(f"Cosmic Events: {result['cosmic_events']}")
        
        if not context_parts:
            return "Real-time astrology data temporarily unavailable."
        
        return "\n\n".join(context_parts)

