"""
Browser Agent Client using AWS Bedrock AgentCore + Browser-Use
Enables AI-powered web scraping and data extraction
"""

from typing import Any, Dict
from contextlib import asynccontextmanager
import asyncio

from bedrock_agentcore.tools.browser_client import BrowserClient
from browser_use import Agent
from browser_use.browser.session import BrowserSession
from browser_use.browser import BrowserProfile
from langchain_aws import ChatBedrockConverse

from app.core.config import settings


class BrowserAgentClient:
    """
    Client for AI-powered browser automation using Bedrock AgentCore.
    
    Uses Browser-Use SDK with Bedrock models to navigate websites
    and extract data based on natural language instructions.
    """
    
    def __init__(self, region: str | None = None):
        """Initialize browser agent client."""
        self.region = region or settings.aws_region
        self.browser_client: BrowserClient | None = None
        
    def _create_llm(self) -> ChatBedrockConverse:
        """Create Bedrock LLM for browser agent."""
        return ChatBedrockConverse(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Use inference profile
            region_name=self.region,
        )
    
    @asynccontextmanager
    async def browser_session(self):
        """
        Context manager for browser session.
        
        Usage:
            async with client.browser_session() as session:
                result = await client.execute_task(session, "Extract...")
        """
        self.browser_client = BrowserClient(self.region)
        self.browser_client.start()
        
        try:
            # Get WebSocket URL and headers for browser connection
            ws_url, headers = self.browser_client.generate_ws_headers()
            
            # Create browser profile with headers
            browser_profile = BrowserProfile(
                headers=headers,
                timeout=150000,  # 150 seconds timeout
            )
            
            # Create browser session connected to AgentCore browser
            session = BrowserSession(
                cdp_url=ws_url,
                browser_profile=browser_profile,
                keep_alive=True,  # Keep browser alive between tasks
            )
            
            # Initialize the session
            await session.start()
            
            yield session
            
        finally:
            # Cleanup
            if self.browser_client:
                self.browser_client.stop()
    
    async def execute_task(
        self,
        browser_session: BrowserSession,
        task: str,
        starting_url: str | None = None,
    ) -> Dict[str, Any]:
        """
        Execute a browser automation task using natural language.
        
        Args:
            browser_session: Active browser session
            task: Natural language instruction (e.g., "Extract today's horoscope for Capricorn")
            starting_url: Optional starting URL
            
        Returns:
            Dictionary with extracted data and metadata
        """
        try:
            # Create LLM for agent
            llm = self._create_llm()
            
            # Include starting URL in task if provided
            full_task = task
            if starting_url:
                full_task = f"Go to {starting_url} and then: {task}"
            
            # Create browser agent with task
            agent = Agent(
                task=full_task,
                llm=llm,
                browser_session=browser_session,
            )
            
            # Execute task
            result = await agent.run()
            
            return {
                "success": True,
                "data": result.final_result() if hasattr(result, 'final_result') else str(result),
                "error": None,
            }
            
        except Exception as e:
            print(f"Browser agent error: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
            }
    
    async def fetch_from_url(
        self,
        url: str,
        extraction_prompt: str,
    ) -> Dict[str, Any]:
        """
        High-level method: Fetch and extract data from a URL.
        
        Args:
            url: Website to visit
            extraction_prompt: What to extract (natural language)
            
        Returns:
            Extracted data
            
        Example:
            result = await client.fetch_from_url(
                url="https://astro.com",
                extraction_prompt="Extract today's planetary transits and their meanings"
            )
        """
        async with self.browser_session() as session:
            return await self.execute_task(
                browser_session=session,
                task=extraction_prompt,
                starting_url=url,
            )
