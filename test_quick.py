"""
Quick test of key data sources
"""

import sys
sys.path.insert(0, '/Users/georgiosvasilakis/src/karmona-backend')

from datetime import date
from app.services.ephemeris_service import EphemerisService
from app.services.browser_scraper import BrowserScraper
from app.services.scraping_sources import SCRAPING_SOURCES

def test_ephemeris():
    """Test Swiss Ephemeris calculation"""
    print("\n" + "="*70)
    print("🌌 TEST: Swiss Ephemeris")
    print("="*70)
    try:
        service = EphemerisService()
        result = service.calculate_positions(date.today())
        if "error" not in result:
            print("✅ SUCCESS - Ephemeris works")
            print(f"   Sample: Sun at {result['positions']['sun']['formatted']}")
            return True
        else:
            print(f"❌ FAILED - {result['error']}")
            return False
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

def test_astrostyle():
    """Test Astrostyle (was timing out before fix)"""
    print("\n" + "="*70)
    print("📰 TEST: Astrostyle Aries")
    print("="*70)
    try:
        scraper = BrowserScraper()
        result = scraper.fetch_and_extract(
            url="https://astrostyle.com/horoscopes/daily/aries/",
            extraction_prompt=SCRAPING_SOURCES[0].extraction_prompt.replace("{sign}", "Aries"),
            wait_seconds=3
        )

        if result['success']:
            print(f"✅ SUCCESS - Astrostyle")
            print(f"   Content length: {len(result['data'])} chars")
            print(f"   Preview: {result['data'][:150]}...")
            return True
        else:
            print(f"❌ FAILED - {result['error']}")
            return False
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

def test_cafeastrology():
    """Test Cafe Astrology"""
    print("\n" + "="*70)
    print("📰 TEST: Cafe Astrology Aries")
    print("="*70)
    try:
        scraper = BrowserScraper()
        result = scraper.fetch_and_extract(
            url="https://cafeastrology.com/ariesdailyhoroscope.html",
            extraction_prompt=SCRAPING_SOURCES[1].extraction_prompt.replace("{sign}", "Aries"),
            wait_seconds=3
        )

        if result['success']:
            print(f"✅ SUCCESS - Cafe Astrology")
            print(f"   Content length: {len(result['data'])} chars")
            print(f"   Preview: {result['data'][:150]}...")
            return True
        else:
            print(f"❌ FAILED - {result['error']}")
            return False
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

def main():
    """Test key sources"""
    results = {
        'Ephemeris': test_ephemeris(),
        'Astrostyle': test_astrostyle(),
        'Cafe Astrology': test_cafeastrology(),
    }

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    print(f"\nPassed: {passed}/{total} ({int(passed/total*100)}%)")
    print("="*70)

if __name__ == "__main__":
    main()
