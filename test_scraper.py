"""Test the simple browser scraper with NY Post"""
from app.services.browser_scraper import BrowserScraper

def test_nypost():
    print("Testing NY Post Astrology Scraper")
    print("=" * 60)
    
    scraper = BrowserScraper(region="us-east-2")
    
    result = scraper.fetch_and_extract(
        url="https://nypost.com/astrology/",
        extraction_prompt="What is the main headline about astrology on this page? Return just the headline text."
    )
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Data: {result['data']}")
    print("=" * 60)

if __name__ == "__main__":
    test_nypost()
