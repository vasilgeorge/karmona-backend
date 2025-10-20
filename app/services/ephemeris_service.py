"""
Swiss Ephemeris Service
Calculates precise planetary positions for any date/time.
No scraping needed - pure astronomical calculations.
"""

from datetime import date, datetime
from typing import Dict, Any, List
import json
import boto3

from app.core.config import settings


# Zodiac sign boundaries (degrees)
ZODIAC_SIGNS = [
    ("Aries", 0), ("Taurus", 30), ("Gemini", 60), ("Cancer", 90),
    ("Leo", 120), ("Virgo", 150), ("Libra", 180), ("Scorpio", 210),
    ("Sagittarius", 240), ("Capricorn", 270), ("Aquarius", 300), ("Pisces", 330)
]


class EphemerisService:
    """
    Calculate planetary positions using Swiss Ephemeris.

    Installation required:
        pip install pyswisseph
    """

    def __init__(self):
        """Initialize ephemeris service."""
        try:
            import swisseph as swe
            self.swe = swe
            self.swe_available = True
        except ImportError:
            print("⚠️ pyswisseph not installed. Run: pip install pyswisseph")
            self.swe_available = False

        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def _degrees_to_sign(self, degrees: float) -> Dict[str, Any]:
        """
        Convert ecliptic longitude to zodiac sign with degree and minute.

        Args:
            degrees: Ecliptic longitude (0-360)

        Returns:
            Dictionary with sign, degrees within sign, and formatted string
        """
        # Normalize to 0-360
        degrees = degrees % 360

        # Find zodiac sign
        for i, (sign, start_deg) in enumerate(ZODIAC_SIGNS):
            next_start = ZODIAC_SIGNS[(i + 1) % 12][1] if i < 11 else 360
            if start_deg <= degrees < next_start:
                degrees_in_sign = degrees - start_deg
                deg_int = int(degrees_in_sign)
                minutes = int((degrees_in_sign - deg_int) * 60)

                return {
                    "sign": sign,
                    "degrees": round(degrees_in_sign, 2),
                    "formatted": f"{deg_int}°{minutes}' {sign}"
                }

        # Fallback (should never reach here)
        return {"sign": "Pisces", "degrees": 0, "formatted": "0°0' Pisces"}

    def calculate_positions(self, target_date: date | None = None) -> Dict[str, Any]:
        """
        Calculate all planetary positions for a given date.

        Args:
            target_date: Date to calculate for (defaults to today)

        Returns:
            Dictionary with planetary positions and metadata
        """
        if not self.swe_available:
            return {"error": "Swiss Ephemeris not available"}

        if target_date is None:
            target_date = date.today()

        # Convert to Julian Day (noon UTC)
        jd = self.swe.julday(target_date.year, target_date.month, target_date.day, 12.0)

        # Define planets to calculate
        planets = {
            'sun': self.swe.SUN,
            'moon': self.swe.MOON,
            'mercury': self.swe.MERCURY,
            'venus': self.swe.VENUS,
            'mars': self.swe.MARS,
            'jupiter': self.swe.JUPITER,
            'saturn': self.swe.SATURN,
            'uranus': self.swe.URANUS,
            'neptune': self.swe.NEPTUNE,
            'pluto': self.swe.PLUTO,
            'north_node': self.swe.TRUE_NODE,
            'chiron': self.swe.CHIRON,
        }

        positions = {}

        # Calculate each planet
        for planet_name, planet_id in planets.items():
            try:
                # Calculate position using Swiss Ephemeris
                # FLG_SWIEPH (2) = use built-in ephemeris (Moshier)
                # FLG_SPEED (256) = calculate speed for retrograde detection
                result = self.swe.calc_ut(jd, planet_id, self.swe.FLG_SWIEPH | self.swe.FLG_SPEED)

                # Result is (tuple_of_6_values, return_code)
                position_data = result[0]

                longitude = position_data[0]  # Ecliptic longitude
                speed = position_data[3]      # Daily motion (negative = retrograde)

                # Convert to sign
                sign_info = self._degrees_to_sign(longitude)

                positions[planet_name] = {
                    "longitude": round(longitude, 4),
                    "sign": sign_info["sign"],
                    "degrees_in_sign": sign_info["degrees"],
                    "formatted": sign_info["formatted"],
                    "retrograde": speed < 0,
                    "daily_motion": round(speed, 4),
                }

            except Exception as e:
                print(f"Error calculating {planet_name}: {e}")
                positions[planet_name] = {"error": str(e)}

        return {
            "date": target_date.isoformat(),
            "julian_day": jd,
            "positions": positions,
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def get_retrograde_planets(self, positions: Dict[str, Any]) -> List[str]:
        """
        Extract list of retrograde planets from positions.

        Args:
            positions: Output from calculate_positions()

        Returns:
            List of planet names currently retrograde
        """
        retrograde = []
        planet_data = positions.get("positions", {})

        for planet, data in planet_data.items():
            if isinstance(data, dict) and data.get("retrograde"):
                retrograde.append(planet.capitalize())

        return retrograde

    def format_for_llm(self, positions: Dict[str, Any]) -> str:
        """
        Format planetary positions as human-readable text for LLM context.

        Args:
            positions: Output from calculate_positions()

        Returns:
            Formatted string describing planetary positions
        """
        if "error" in positions:
            return "Planetary position data unavailable."

        date_str = positions["date"]
        planet_data = positions.get("positions", {})

        lines = [f"**Planetary Positions for {date_str}:**\n"]

        # Major planets
        major = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
        lines.append("**Inner & Outer Planets:**")
        for planet in major:
            if planet in planet_data and "formatted" in planet_data[planet]:
                data = planet_data[planet]
                retro = " (Retrograde)" if data.get("retrograde") else ""
                lines.append(f"- {planet.capitalize()}: {data['formatted']}{retro}")

        # Outer planets
        lines.append("\n**Generational Planets:**")
        outer = ["uranus", "neptune", "pluto"]
        for planet in outer:
            if planet in planet_data and "formatted" in planet_data[planet]:
                data = planet_data[planet]
                retro = " (Retrograde)" if data.get("retrograde") else ""
                lines.append(f"- {planet.capitalize()}: {data['formatted']}{retro}")

        # Special points
        lines.append("\n**Lunar Nodes & Asteroids:**")
        special = ["north_node", "chiron"]
        for point in special:
            if point in planet_data and "formatted" in planet_data[point]:
                data = planet_data[point]
                lines.append(f"- {point.replace('_', ' ').title()}: {data['formatted']}")

        # Retrograde summary
        retrograde = self.get_retrograde_planets(positions)
        if retrograde:
            lines.append(f"\n**Currently Retrograde:** {', '.join(retrograde)}")
        else:
            lines.append("\n**Currently Retrograde:** None")

        return "\n".join(lines)

    def upload_to_s3(self, positions: Dict[str, Any]) -> bool:
        """
        Upload calculated positions to S3 for knowledge base.

        Args:
            positions: Output from calculate_positions()

        Returns:
            True if successful
        """
        try:
            target_date = positions["date"]

            # Create filename
            filename = f"ephemeris/{target_date}/planetary_positions.json"

            # Format for knowledge base
            kb_document = {
                "id": f"ephemeris-{target_date}",
                "date": target_date,
                "source": "swiss_ephemeris",
                "content": self.format_for_llm(positions),
                "data": positions,  # Include raw data
                "metadata": {
                    "tags": ["ephemeris", "planetary-positions", "daily"],
                    "calculated_at": positions["calculated_at"],
                }
            }

            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.s3_astrology_bucket,
                Key=filename,
                Body=json.dumps(kb_document, indent=2),
                ContentType='application/json',
            )

            print(f"✅ Uploaded ephemeris data to S3: {filename}")
            return True

        except Exception as e:
            print(f"❌ Failed to upload ephemeris data: {e}")
            return False

    def run_daily_calculation(self, target_date: date | None = None) -> Dict[str, Any]:
        """
        Main method: Calculate positions and upload to S3.

        Args:
            target_date: Date to calculate (defaults to today)

        Returns:
            Calculation results
        """
        if target_date is None:
            target_date = date.today()

        print(f"🌌 Calculating planetary positions for {target_date.isoformat()}...")

        # Calculate positions
        positions = self.calculate_positions(target_date)

        if "error" in positions:
            print(f"❌ Calculation failed: {positions['error']}")
            return positions

        # Print summary
        print(f"\n{self.format_for_llm(positions)}")

        # Upload to S3
        uploaded = self.upload_to_s3(positions)

        if uploaded:
            print(f"✅ Ephemeris calculation complete!")

        return {
            "success": uploaded,
            "date": target_date.isoformat(),
            "positions": positions,
        }


# Convenience function for quick use
def get_todays_positions() -> Dict[str, Any]:
    """Get today's planetary positions (convenience function)."""
    service = EphemerisService()
    return service.calculate_positions()
