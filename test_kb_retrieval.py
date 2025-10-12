"""Test KB retrieval service"""
import asyncio
from app.services.kb_retrieval_service import KBRetrievalService

async def test_retrieval():
    print("🔍 Testing Knowledge Base Retrieval")
    print("=" * 60)
    
    retrieval = KBRetrievalService()
    
    # Test with sample user data
    context = await retrieval.retrieve_context(
        sun_sign="Capricorn",
        moon_sign="Virgo",
        mood="good",
        actions=["helped", "meditated"],
        zodiac_element="Earth",
        max_results=5,
    )
    
    print("\n" + "=" * 60)
    print("📊 RETRIEVED CONTEXT:")
    print("=" * 60)
    print(context)
    print("=" * 60)
    print(f"\nContext length: {len(context)} chars")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
