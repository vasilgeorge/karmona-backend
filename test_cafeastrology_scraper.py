"""
Test Cafe Astrology horoscope scraper
Tests a single sign to verify we're getting good data
"""

import sys
sys.path.insert(0, '/Users/georgiosvasilakis/src/karmona-backend')

from app.services.browser_scraper import BrowserScraper
from datetime import date


def test_single_sign(sign: str = "aries"):
    """Test scraping a single sign's horoscope."""
    print("=" * 70)
    print(f"🔮 Testing Cafe Astrology Horoscope Scraper")
    print("=" * 70)
    print(f"Sign: {sign.capitalize()}")
    print(f"Date: {date.today().isoformat()}")
    print("=" * 70)
    print()

    # URL format from Cafe Astrology
    url = f"https://cafeastrology.com/{sign}dailyhoroscope.html"
    print(f"URL: {url}")
    print()

    # Extraction prompt
    extraction_prompt = f"""
    Extract TODAY'S daily horoscope for {sign}.

    Focus on:
    1. Today's main theme or guidance
    2. Any planetary influences or transits mentioned
    3. Practical advice or areas of focus
    4. Emotional or energetic insights

    Return ONLY the horoscope text for today.
    Be concise but capture the key insights (3-5 sentences).
    Do not include headers, dates, or navigation text.
    """

    # Initialize scraper
    print("🌐 Initializing browser scraper...")
    scraper = BrowserScraper()

    # Scrape
    print("🔍 Scraping page (this may take 10-15 seconds)...")
    result = scraper.fetch_and_extract(
        url=url,
        extraction_prompt=extraction_prompt,
        wait_seconds=4,
    )

    # Display results
    print()
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)

    if result['success']:
        print("✅ SUCCESS")
        print()
        print("Extracted Content:")
        print("-" * 70)
        print(result['data'])
        print("-" * 70)
        print()
        print(f"Content Length: {len(result['data'])} characters")

        # Quality checks
        print()
        print("Quality Checks:")
        print("-" * 70)

        content = result['data'].lower()

        # Check 1: Has meaningful content
        if len(result['data']) < 50:
            print("⚠️  WARNING: Content seems too short (< 50 chars)")
        else:
            print(f"✅ Content length OK ({len(result['data'])} chars)")

        # Check 2: Contains astrological terms
        astro_terms = ['planet', 'moon', 'sun', 'mercury', 'venus', 'mars',
                       'jupiter', 'saturn', 'energy', 'transit', 'aspect']
        found_terms = [term for term in astro_terms if term in content]
        if found_terms:
            print(f"✅ Contains astro terms: {', '.join(found_terms)}")
        else:
            print("⚠️  WARNING: No astrological terms detected")

        # Check 3: Mentions the sign
        if sign in content:
            print(f"✅ Mentions {sign.capitalize()}")
        else:
            print(f"⚠️  WARNING: Doesn't mention {sign.capitalize()}")

        # Check 4: Future-oriented (advice/guidance)
        guidance_words = ['will', 'should', 'can', 'may', 'might', 'today',
                         'focus', 'consider', 'opportunity', 'energy']
        found_guidance = [word for word in guidance_words if word in content]
        if found_guidance:
            print(f"✅ Contains guidance: {', '.join(found_guidance[:5])}")
        else:
            print("⚠️  WARNING: No guidance words detected")

        print()
        print("=" * 70)
        print("✅ Test Complete - Data looks good!" if len(result['data']) > 50 else
              "⚠️  Test Complete - Review data quality")
        print("=" * 70)

        return True

    else:
        print("❌ FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False


def test_multiple_signs():
    """Test scraping multiple signs."""
    print("\n" + "=" * 70)
    print("🔮 Testing Multiple Signs")
    print("=" * 70)
    print()

    test_signs = ["aries", "taurus", "gemini"]
    results = {}

    for sign in test_signs:
        print(f"\n📋 Testing {sign.capitalize()}...")
        success = test_single_sign(sign)
        results[sign] = success

        if success:
            print("✅")
        else:
            print("❌")

        print()
        input("Press Enter to continue to next sign...")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    successful = sum(1 for v in results.values() if v)
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {len(results) - successful}/{len(results)}")

    for sign, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {sign.capitalize()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Cafe Astrology scraper")
    parser.add_argument("--sign", default="aries", help="Zodiac sign to test")
    parser.add_argument("--multiple", action="store_true",
                       help="Test multiple signs")

    args = parser.parse_args()

    if args.multiple:
        test_multiple_signs()
    else:
        test_single_sign(args.sign)
