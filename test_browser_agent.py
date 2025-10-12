"""
Test the browser agent client with a simple astrology data fetch
"""
import asyncio
from app.services.browser_agent_client import BrowserAgentClient

async def test_simple_fetch():
    """Test basic browser agent functionality"""
    print("🌐 Testing Browser Agent Client...")
    print("=" * 60)
    
    client = BrowserAgentClient(region="us-east-2")
    
    # Simple test: Fetch today's horoscope
    print("\n📅 Test 1: Fetching today's Capricorn horoscope from Astro.com...")
    
    result = await client.fetch_from_url(
        url="https://www.astro.com/horoscope",
        extraction_prompt="""
        Find and extract today's horoscope for Capricorn.
        Return just the horoscope text, 1-2 sentences maximum.
        """
    )
    
    print(f"\n✅ Result:")
    print(f"   Success: {result['success']}")
    print(f"   Data: {result['data']}")
    print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("🎉 Browser Agent Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_simple_fetch())
