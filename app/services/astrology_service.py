"""
Astrology calculation service using pyswisseph.
"""

from datetime import date, datetime
from typing import Any

import swisseph as swe
import httpx

from app.core.config import settings
from app.models.schemas import AstrologyData


# Zodiac sign boundaries (in degrees)
ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


class AstrologyService:
    """Service for astrology calculations and horoscopes."""

    def __init__(self) -> None:
        """Initialize astrology service."""
        # Swiss Ephemeris uses Julian Day numbers
        pass

    def calculate_sun_sign(self, birthdate: date) -> str:
        """Calculate sun sign from birthdate."""
        # Simple sun sign calculation based on date ranges
        month, day = birthdate.month, birthdate.day

        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "Capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Aquarius"
        else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
            return "Pisces"

    def calculate_moon_sign(
        self, birthdate: date, birth_time: str | None = None, birth_place: str | None = None
    ) -> str | None:
        """
        Calculate moon sign using Swiss Ephemeris.
        Requires birth time and location for accurate calculation.
        """
        if not birth_time:
            return None

        try:
            # Parse birth time
            hour, minute = map(int, birth_time.split(":"))

            # Convert to Julian Day
            # Note: This is a simplified version. For production, you'd need:
            # 1. Geocoding birth_place to get latitude/longitude
            # 2. Timezone conversion
            # 3. More precise Swiss Ephemeris calculations

            birth_datetime = datetime(
                birthdate.year, birthdate.month, birthdate.day, hour, minute
            )
            julian_day = swe.julday(
                birth_datetime.year,
                birth_datetime.month,
                birth_datetime.day,
                birth_datetime.hour + birth_datetime.minute / 60.0,
            )

            # Calculate moon position (planet ID 1 = Moon)
            moon_position = swe.calc_ut(julian_day, swe.MOON)[0][0]

            # Convert position to zodiac sign
            sign_index = int(moon_position / 30)
            return ZODIAC_SIGNS[sign_index]

        except Exception as e:
            print(f"Error calculating moon sign: {e}")
            return None

    async def get_daily_horoscope(self, sign: str) -> str | None:
        """
        Fetch today's horoscope from Aztro API.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.aztro_api_url}/?sign={sign.lower()}&day=today"
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("description", "")
        except Exception as e:
            print(f"Error fetching horoscope: {e}")

        return None

    async def get_astrology_data(
        self, birthdate: date, birth_time: str | None = None, birth_place: str | None = None
    ) -> AstrologyData:
        """
        Get complete astrology data for a user.
        """
        sun_sign = self.calculate_sun_sign(birthdate)
        moon_sign = self.calculate_moon_sign(birthdate, birth_time, birth_place)

        # Get today's horoscope for context
        horoscope = await self.get_daily_horoscope(sun_sign)

        return AstrologyData(
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            planetary_summary=horoscope,
        )

    def get_zodiac_element(self, sign: str) -> str:
        """Get the element (Fire, Earth, Air, Water) for a zodiac sign."""
        elements = {
            "Aries": "Fire",
            "Taurus": "Earth",
            "Gemini": "Air",
            "Cancer": "Water",
            "Leo": "Fire",
            "Virgo": "Earth",
            "Libra": "Air",
            "Scorpio": "Water",
            "Sagittarius": "Fire",
            "Capricorn": "Earth",
            "Aquarius": "Air",
            "Pisces": "Water",
        }
        return elements.get(sign, "Unknown")

