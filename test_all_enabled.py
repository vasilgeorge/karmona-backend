"""
Test all enabled data sources (one example per source)
"""

import sys
sys.path.insert(0, '/Users/georgiosvasilakis/src/karmona-backend')

from datetime import date
from app.services.ephemeris_service import EphemerisService
from app.services.browser_scraper import BrowserScraper

def test_source(name, url, prompt):
    """Test a single source"""
    print(f"\n{'='*60}")
    print(f"📰 {name}")
    print(f"{'='*60}")
    try:
        scraper = BrowserScraper()
        result = scraper.fetch_and_extract(url=url, extraction_prompt=prompt, wait_seconds=3)

        if result['success']:
            print(f"✅ SUCCESS - {len(result['data'])} chars")
            return True
        else:
            print(f"❌ FAILED - {result['error']}")
            return False
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

def main():
    results = {}

    # Ephemeris
    print(f"\n{'='*60}")
    print("🌌 Ephemeris")
    print(f"{'='*60}")
    try:
        service = EphemerisService()
        result = service.calculate_positions(date.today())
        if "error" not in result:
            print("✅ SUCCESS")
            results['Ephemeris'] = True
        else:
            print(f"❌ FAILED - {result['error']}")
            results['Ephemeris'] = False
    except Exception as e:
        print(f"❌ FAILED - {e}")
        results['Ephemeris'] = False

    # Astrostyle Aries
    results['Astrostyle'] = test_source(
        "Astrostyle Aries",
        "https://astrostyle.com/horoscopes/daily/aries/",
        "Extract TODAY'S COMPLETE daily horoscope for Aries. Include all text, planetary influences, and guidance."
    )

    # Cafe Astrology Aries
    results['Cafe Astrology'] = test_source(
        "Cafe Astrology Aries",
        "https://cafeastrology.com/ariesdailyhoroscope.html",
        "Extract today's horoscope for Aries. Copy the complete text word-for-word."
    )

    # Astro-Seek
    results['Astro-Seek'] = test_source(
        "Astro-Seek",
        "https://www.astro-seek.com/",
        "Extract today's major planetary transits and moon position."
    )

    # Tiny Buddha
    results['Tiny Buddha'] = test_source(
        "Tiny Buddha",
        "https://tinybuddha.com/",
        "Extract featured inspirational teaching and mindfulness guidance."
    )

    # Moon Phase
    results['Moon Phase'] = test_source(
        "MoonGiant",
        "https://www.moongiant.com/phase/today/",
        "Extract TODAY's moon phase name, illumination, moon sign, and position."
    )

    # Retrogrades
    results['Retrogrades'] = test_source(
        "Retrogrades",
        "https://cafeastrology.com/calendars/todayinastrologycalendar.html",
        "Extract planets currently in RETROGRADE motion. List all with their signs and degrees."
    )

    # Eclipses
    results['Eclipses'] = test_source(
        "Eclipses",
        "https://www.timeanddate.com/eclipse/list.html",
        "Extract upcoming eclipse information for the next 12 months."
    )

    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    print(f"\nPassed: {passed}/{total} ({int(passed/total*100)}%)")

if __name__ == "__main__":
    main()
