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
        You are extracting today's horoscope for {sign} from a web page.

        FIND the section that says "Today's {sign} Horoscope" or "{sign} Daily Horoscope" followed by today's date.

        Extract EVERYTHING in that horoscope section, word-for-word:
        1. The complete horoscope text (usually 2-3 paragraphs) - copy it EXACTLY
        2. Any ratings like "Creativity: Excellent ~ Love: Good ~ Business: Good"
        3. Any planetary alignments or aspects mentioned (Mercury-Mars, Sun-Saturn, etc.)

        IGNORE: Navigation menus, links to other horoscopes, "choose another sign" sections, general astrology info

        COPY the horoscope paragraphs verbatim. Do not summarize or paraphrase.
        Include the complete text as it appears on the page.
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

    # Moon phase data
    ScrapingSource(
        name="moongiant_phase",
        source_type="cosmic_overview",
        url="https://www.moongiant.com/phase/today/",
        extraction_prompt="""
        Extract TODAY's complete moon phase information:

        1. Moon Phase Name (e.g., Waning Crescent, Full Moon, New Moon, etc.)
        2. Illumination percentage
        3. Moon Age (days into current lunar cycle)
        4. Current Moon Sign (which zodiac sign the moon is in)
        5. Moon's position in degrees within that sign
        6. Moonrise time (if available)
        7. Moonset time (if available)

        Include ALL details exactly as shown. This is important astrological data.
        """,
        enabled=True,
    ),

    # Retrograde planets
    ScrapingSource(
        name="cafeastrology_retrogrades",
        source_type="cosmic_overview",
        url="https://cafeastrology.com/calendars/todayinastrologycalendar.html",
        extraction_prompt="""
        Extract information about planets currently in RETROGRADE motion.

        Look for planetary positions marked with "R" (indicating retrograde).

        For each retrograde planet, extract:
        1. Planet name
        2. Current zodiac sign
        3. Exact degree position
        4. That it's retrograde (marked with R)

        Example format: "Saturn is retrograde at 26° Pisces"

        List ALL planets that are currently retrograde.
        If no planets are retrograde, state "No planets are currently retrograde."
        """,
        enabled=True,
    ),

    # Eclipse calendar
    ScrapingSource(
        name="timeanddate_eclipses",
        source_type="cosmic_overview",
        url="https://www.timeanddate.com/eclipse/list.html",
        extraction_prompt="""
        Extract upcoming eclipse information for the next 12 months:

        For each eclipse, extract:
        1. Eclipse type (Solar or Lunar, Total/Partial/Annular)
        2. Date
        3. Brief description if available

        Focus on eclipses happening in 2025 and early 2026.
        This data changes infrequently so it's okay to get broader timeframe.
        """,
        enabled=True,
    ),

    # Weekly horoscopes (run daily - gives users weekly perspective)
    ScrapingSource(
        name="astrology_com_weekly",
        source_type="sign_specific",
        url_pattern="https://www.astrology.com/horoscope/weekly/{sign}.html",
        extraction_prompt="""
        Extract this WEEK's complete horoscope forecast for {sign}.

        Include ALL of the following:
        1. The full weekly forecast text - extract EVERYTHING, don't summarize
        2. Week date range if shown
        3. Key themes and focus areas for the week
        4. Any specific day-by-day guidance if provided
        5. Important planetary transits or aspects mentioned for this week
        6. Timing advice (best days for specific activities)

        Extract the complete text exactly as written. Do not shorten or paraphrase.
        """,
        enabled=True,  # Now enabled - provides weekly perspective
        frequency="daily",  # Run daily so users always have current week's forecast
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

