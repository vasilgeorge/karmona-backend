"""
Test script for Ephemeris Service
Run with: python test_ephemeris.py
"""

from datetime import date
from app.services.ephemeris_service import EphemerisService, get_todays_positions


def test_basic_calculation():
    """Test basic planetary position calculation."""
    print("=" * 70)
    print("TEST 1: Basic Planetary Position Calculation")
    print("=" * 70)

    positions = get_todays_positions()

    if "error" in positions:
        print(f"❌ Error: {positions['error']}")
        print("\n💡 To fix, run: pip install pyswisseph")
        return False

    print(f"\n✅ Successfully calculated positions for {positions['date']}")
    print(f"   Julian Day: {positions['julian_day']}")
    print(f"   Total planets calculated: {len(positions['positions'])}")

    return True


def test_formatted_output():
    """Test LLM-formatted output."""
    print("\n" + "=" * 70)
    print("TEST 2: LLM-Formatted Output")
    print("=" * 70)

    service = EphemerisService()
    positions = service.calculate_positions()

    if "error" in positions:
        return False

    formatted = service.format_for_llm(positions)
    print(f"\n{formatted}")

    return True


def test_retrograde_detection():
    """Test retrograde planet detection."""
    print("\n" + "=" * 70)
    print("TEST 3: Retrograde Planet Detection")
    print("=" * 70)

    service = EphemerisService()
    positions = service.calculate_positions()

    if "error" in positions:
        return False

    retrograde = service.get_retrograde_planets(positions)

    if retrograde:
        print(f"\n✅ Detected retrograde planets: {', '.join(retrograde)}")
    else:
        print("\n✅ No planets currently retrograde")

    return True


def test_specific_date():
    """Test calculation for a specific historical date."""
    print("\n" + "=" * 70)
    print("TEST 4: Historical Date Calculation")
    print("=" * 70)

    service = EphemerisService()

    # Test with a known date (Jan 1, 2000)
    test_date = date(2000, 1, 1)
    positions = service.calculate_positions(test_date)

    if "error" in positions:
        return False

    print(f"\n✅ Successfully calculated for {test_date}")
    print(f"\nSample positions:")
    print(f"   Sun: {positions['positions']['sun']['formatted']}")
    print(f"   Moon: {positions['positions']['moon']['formatted']}")
    print(f"   Mercury: {positions['positions']['mercury']['formatted']}")

    return True


def test_s3_upload():
    """Test S3 upload (requires AWS credentials)."""
    print("\n" + "=" * 70)
    print("TEST 5: S3 Upload (Optional)")
    print("=" * 70)

    service = EphemerisService()
    positions = service.calculate_positions()

    if "error" in positions:
        return False

    try:
        success = service.upload_to_s3(positions)
        if success:
            print("\n✅ Successfully uploaded to S3")
        else:
            print("\n⚠️  S3 upload failed (check AWS credentials)")
        return success
    except Exception as e:
        print(f"\n⚠️  S3 upload skipped: {e}")
        return False


if __name__ == "__main__":
    print("\n🌌 EPHEMERIS SERVICE TEST SUITE")
    print("=" * 70)

    tests = [
        test_basic_calculation,
        test_formatted_output,
        test_retrograde_detection,
        test_specific_date,
        test_s3_upload,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 70)

    if passed < 4:  # Allow S3 test to fail
        print("\n⚠️  Some tests failed. Check pyswisseph installation:")
        print("   pip install pyswisseph")
    else:
        print("\n✅ All core tests passed!")
        print("\nNext steps:")
        print("1. Integrate into daily scrape job")
        print("2. Update LLM prompts to use planetary data")
