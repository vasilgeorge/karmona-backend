"""
Configuration for astrology data sources.
Defines what sites to scrape and how.
"""

from typing import List, Dict, Any

# All zodiac signs in lowercase
ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]


class ScrapingSource:
    """Configuration for a scraping source."""
    
    def __init__(
        self,
        name: str,
        source_type: str,
        url_pattern: str | None = None,
        url: str | None = None,
        extraction_prompt: str = "",
        frequency: str = "daily",
        enabled: bool = True,
    ):
        self.name = name
        self.source_type = source_type  # sign_specific | cosmic_overview | article_based
        self.url_pattern = url_pattern  # For sign-specific: has {sign} placeholder
        self.url = url  # For single-URL sources
        self.extraction_prompt = extraction_prompt
        self.frequency = frequency
        self.enabled = enabled
    
    def get_urls(self) -> List[Dict[str, str]]:
        """Get list of URLs to scrape based on source type."""
        if self.source_type == "sign_specific" and self.url_pattern:
            # Generate URL for each zodiac sign
            return [
                {
                    "url": self.url_pattern.format(sign=sign),
                    "context": sign.capitalize(),
                }
                for sign in ZODIAC_SIGNS
            ]
        elif self.source_type in ["cosmic_overview", "article_based"] and self.url:
            # Single URL
            return [{"url": self.url, "context": "general"}]
        else:
            return []


# Configure all scraping sources
SCRAPING_SOURCES = [
    # Sign-specific horoscopes (12 URLs each)
    ScrapingSource(
        name="astrostyle",
        source_type="sign_specific",
        url_pattern="https://astrostyle.com/horoscopes/daily/{sign}/",
        extraction_prompt="""
        Extract TODAY'S COMPLETE daily horoscope for {sign}.

        Include ALL of the following:
        1. Main horoscope text - extract the FULL text, not a summary
        2. All planetary influences, transits, and aspects mentioned
        3. All practical advice, actions, or guidance provided
        4. Lucky numbers, colors, or other attributes if mentioned
        5. Love, career, or other specific area forecasts if provided
        6. Any timing information (morning/afternoon/evening guidance)

        Do NOT summarize or shorten the content. Extract the complete horoscope as written.
        Only exclude navigation menus, ads, and unrelated site content.
        """,
        enabled=True,
    ),
    
    # Cafe Astrology - Daily Horoscopes (sign-specific)
    ScrapingSource(
        name="cafeastrology_horoscopes",
        source_type="sign_specific",
        url_pattern="https://cafeastrology.com/{sign}dailyhoroscope.html",
        extraction_prompt="""
        Extract TODAY'S COMPLETE daily horoscope for {sign} in its ORIGINAL form.

        **CRITICAL: Quote the horoscope text word-for-word. Do NOT paraphrase or summarize.**

        Format your response exactly like this:

        **Daily Horoscope:**
        [Quote the complete horoscope paragraph(s) exactly as written]

        **Planetary Influences:**
        [List all planetary alignments, transits, and aspects mentioned]

        **Specific Advice:**
        [List all specific actions, guidance, and recommendations]

        **Ratings (if provided):**
        [Include any ratings for Love, Creativity, Business, etc.]

        **Timing Notes:**
        [Any morning/afternoon/evening specific guidance]

        **Additional Forecasts:**
        [Any love/career/money/health forecasts if provided]

        Remember: Extract word-for-word. Preserve all detail. Do not condense.
        Only exclude navigation menus, ads, and unrelated site content.
        """,
        enabled=True,
    ),

    # Cosmic overview sources (1 URL each)
    ScrapingSource(
        name="cafeastrology_cosmic_overview",
        source_type="cosmic_overview",
        url="https://www.cafeastrology.com/",
        extraction_prompt="""
        Extract TODAY's cosmic information:
        1. Current moon phase and moon sign
        2. Planetary aspects happening today
        3. Any planets in retrograde
        4. Overall cosmic energy or theme for the day

        Be specific about today's astrological events.
        """,
        enabled=False,  # Disabled for now, we'll enable after testing horoscopes
    ),
    
    ScrapingSource(
        name="astro_seek",
        source_type="cosmic_overview",
        url="https://www.astro-seek.com/",
        extraction_prompt="""
        Extract current planetary positions and aspects:
        1. Today's major planetary transits
        2. Moon position and phase
        3. Any significant astrological events today
        
        Focus on actionable astrological insights.
        """,
        enabled=True,
    ),
    
    # Spiritual wisdom
    ScrapingSource(
        name="tinybuddha",
        source_type="cosmic_overview",
        url="https://tinybuddha.com/",
        extraction_prompt="""
        Extract recent spiritual wisdom and mindfulness guidance:
        1. Featured inspirational teaching or quote
        2. Practical mindfulness suggestions
        3. Guidance on self-reflection or intention-setting
        
        Summarize in 2-3 sentences with warm, grounding energy.
        """,
        enabled=True,
    ),
]


def get_enabled_sources() -> List[ScrapingSource]:
    """Get list of enabled scraping sources."""
    return [source for source in SCRAPING_SOURCES if source.enabled]


def count_total_scrapes() -> int:
    """Calculate total number of scrapes per run."""
    total = 0
    for source in get_enabled_sources():
        urls = source.get_urls()
        total += len(urls)
    return total

