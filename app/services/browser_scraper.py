"""
Simple browser scraper using Bedrock AgentCore + Playwright
Fast and direct web scraping with LLM parsing
"""

import time
from typing import Dict, Any

from playwright.sync_api import sync_playwright, BrowserType
from langchain_aws import ChatBedrock

from app.core.config import settings
from app.services.karmona_browser_session import karmona_browser_session


class BrowserScraper:
    """
    Simple browser scraper using AgentCore browser + Playwright.
    
    This is faster than autonomous agents:
    - Direct page navigation with Playwright
    - Extract text content
    - Use Claude to parse and extract data
    """
    
    def __init__(self, region: str | None = None):
        """Initialize browser scraper."""
        self.region = region or settings.aws_region
        
    def _create_llm(self) -> ChatBedrock:
        """Create ChatBedrock for parsing page content with explicit credentials."""
        import boto3
        
        # Create boto3 client with Karmona credentials
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=self.region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        
        # Use Nova Micro for extraction (much cheaper than Claude)
        return ChatBedrock(
            model_id="us.amazon.nova-micro-v1:0",  # ~100x cheaper than Claude!
            client=bedrock_client,
            model_kwargs={
                "max_tokens": 4096,  # Maximum for Nova Micro - allow full extraction
                "temperature": 0.1,   # Lower temperature for more literal extraction
            },
        )
    
    def fetch_and_extract(
        self,
        url: str,
        extraction_prompt: str,
        wait_seconds: int = 3,
    ) -> Dict[str, Any]:
        """
        Fetch a URL and extract data using LLM.
        
        Args:
            url: Website URL to scrape
            extraction_prompt: What to extract (natural language)
            wait_seconds: Seconds to wait for page load
            
        Returns:
            Dictionary with extracted data
            
        Example:
            result = scraper.fetch_and_extract(
                url="https://nypost.com/astrology/",
                extraction_prompt="Extract the main headline about today's astrology"
            )
        """
        try:
            with sync_playwright() as playwright:
                # Use custom browser_session with explicit Karmona credentials
                with karmona_browser_session(
                    region=self.region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                ) as client:
                    # Get CDP websocket URL and headers
                    ws_url, headers = client.generate_ws_headers()
                    
                    # Connect Playwright to AgentCore browser
                    chromium: BrowserType = playwright.chromium
                    browser = chromium.connect_over_cdp(ws_url, headers=headers)
                    
                    try:
                        # Get or create context and page
                        context = browser.contexts[0] if browser.contexts else browser.new_context(
                            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                        )
                        page = context.pages[0] if context.pages else context.new_page()
                        
                        # Navigate to URL (with generous timeout for slow sites)
                        print(f"🌐 Navigating to: {url}")
                        page.goto(url, timeout=40000, wait_until="domcontentloaded")  # 40s timeout, faster load
                        print(f"✅ Navigation complete")
                        time.sleep(wait_seconds)

                        # Extract page content (use content() instead of inner_text to avoid timeout)
                        html_content = page.content()
                        print(f"📄 HTML content extracted ({len(html_content)} chars)")

                        # Extract text from HTML using simple parsing
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        content = soup.get_text(separator='\n', strip=True)
                        print(f"📝 Text content extracted ({len(content)} chars)")
                        
                        # Use Nova Micro to extract specific data
                        llm = self._create_llm()

                        # Send more content to LLM (first 15000 chars for better extraction)
                        full_prompt = f"""{extraction_prompt}

Here's the page content:

{content[:15000]}"""

                        print(f"🤖 Asking LLM to extract data...")
                        result = llm.invoke(full_prompt).content
                        
                        return {
                            "success": True,
                            "data": result,
                            "url": url,
                            "error": None,
                        }
                    
                    finally:
                        if not page.is_closed():
                            page.close()
                        browser.close()
                        
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return {
                "success": False,
                "data": None,
                "url": url,
                "error": str(e),
            }

