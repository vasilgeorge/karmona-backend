"""
Test each data source individually to see what works
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
    print("🌌 TEST 1: Swiss Ephemeris (Planetary Positions)")
    print("="*70)
    try:
        service = EphemerisService()
        result = service.calculate_positions(date.today())
        if "error" not in result:
            print("✅ SUCCESS - Ephemeris calculation works")
            print(f"   Sample: Sun at {result['positions']['sun']['formatted']}")
            return True
        else:
            print(f"❌ FAILED - {result['error']}")
            return False
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False

def test_source(source_name, url, prompt, context="general"):
    """Test a single scraping source"""
    print("\n" + "="*70)
    print(f"📰 TEST: {source_name}")
    print(f"   URL: {url}")
    print("="*70)
    try:
        scraper = BrowserScraper()
        result = scraper.fetch_and_extract(
            url=url,
            extraction_prompt=prompt,
            wait_seconds=3
        )
        
        if result['success']:
            print(f"✅ SUCCESS - {source_name}")
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
    """Test all data sources"""
    results = {}
    
    # Test 1: Ephemeris
    results['ephemeris'] = test_ephemeris()
    
    # Test 2: Browser-scraped sources (one example from each type)
    test_sources = [
        # One horoscope from each provider
        ("Astrostyle Aries", "https://astrostyle.com/horoscopes/daily/aries/", 
         SCRAPING_SOURCES[0].extraction_prompt.replace("{sign}", "aries")),
        
        ("Cafe Astrology Aries", "https://cafeastrology.com/ariesdailyhoroscope.html",
         SCRAPING_SOURCES[1].extraction_prompt.replace("{sign}", "aries")),
        
        # Cosmic overview sources
        ("Astro-Seek", "https://www.astro-seek.com/",
         SCRAPING_SOURCES[2].extraction_prompt),
        
        ("Tiny Buddha", "https://tinybuddha.com/",
         SCRAPING_SOURCES[3].extraction_prompt),
        
        ("Moon Phase", "https://www.moongiant.com/phase/today/",
         SCRAPING_SOURCES[4].extraction_prompt),
        
        ("Retrogrades", "https://cafeastrology.com/calendars/todayinastrologycalendar.html",
         SCRAPING_SOURCES[5].extraction_prompt),
        
        ("Eclipses", "https://www.timeanddate.com/eclipse/list.html",
         SCRAPING_SOURCES[6].extraction_prompt),
    ]
    
    for name, url, prompt in test_sources:
        results[name] = test_source(name, url, prompt)
    
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
