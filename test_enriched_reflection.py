"""Test reflection generation with KB-enriched data"""
import asyncio
from datetime import date
from app.services.bedrock_service import BedrockService
from app.services.astrology_service import AstrologyService
from app.services.kb_retrieval_service import KBRetrievalService

async def test_enriched_reflection():
    print("🌙 Testing Reflection with KB Enrichment")
    print("=" * 60)
    
    # Initialize services
    bedrock = BedrockService()
    astrology = AstrologyService()
    kb_retrieval = KBRetrievalService()
    
    # Sample user data
    sun_sign = "Capricorn"
    moon_sign = "Virgo"
    mood = "good"
    actions = ["helped", "meditated"]
    
    # Get zodiac element
    element = astrology.get_zodiac_element(sun_sign)
    print(f"User: {sun_sign} (Moon in {moon_sign}) - {element} element")
    print(f"Mood: {mood}")
    print(f"Actions: {', '.join(actions)}")
    print()
    
    # Get horoscope
    horoscope = await astrology.get_daily_horoscope(sun_sign)
    
    # Get KB enriched context
    print("🔍 Fetching enriched context from KB...")
    enriched_context = await kb_retrieval.retrieve_context(
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        mood=mood,
        actions=actions,
        zodiac_element=element,
    )
    
    print(f"\n📦 Enriched context received: {len(enriched_context)} chars")
    print(f"Preview: {enriched_context[:200]}..." if enriched_context else "None")
    
    # Generate reflection
    print("\n🤖 Generating reflection with Claude...")
    result = await bedrock.generate_reflection(
        name="Test User",
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        mood=mood,
        actions=actions,
        note="Had a really meaningful day helping others and taking time for myself.",
        horoscope=horoscope,
        enriched_context=enriched_context,
        today=date.today(),
    )
    
    print("\n" + "=" * 60)
    print("✨ GENERATED REFLECTION:")
    print("=" * 60)
    print(f"Karma Score: {result.karma_score}")
    print(f"\nReading:")
    print(result.reading)
    print(f"\nRituals:")
    for ritual in result.rituals:
        print(f"  • {ritual}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_enriched_reflection())
