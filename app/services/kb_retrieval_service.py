"""
Knowledge Base Retrieval Service
Semantic search over astrology knowledge base
"""

from typing import List, Dict, Any
import boto3

from app.core.config import settings
from app.models.schemas import MoodType, ActionType


class KBRetrievalService:
    """
    Retrieves relevant astrology/spiritual context from Knowledge Base.
    Uses semantic search to find most relevant chunks.
    """
    
    def __init__(self):
        """Initialize KB retrieval service."""
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    
    def _build_search_query(
        self,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: List[ActionType],
        zodiac_element: str,
    ) -> str:
        """
        Build semantic search query based on user context.
        
        This query will find relevant astrology insights from the KB.
        """
        # Build rich query incorporating all user context
        query_parts = [
            f"{sun_sign} zodiac sign",
        ]
        
        if moon_sign:
            query_parts.append(f"{moon_sign} moon sign")
        
        query_parts.append(f"{zodiac_element} element energy")
        
        # Add mood context
        mood_keywords = {
            "great": "joyful positive uplifting",
            "good": "balanced harmonious",
            "neutral": "centered grounded",
            "sad": "emotional healing transformation",
        }
        query_parts.append(mood_keywords.get(mood, mood))
        
        # Add action themes
        action_themes = {
            "helped": "service compassion",
            "loved": "love connection",
            "meditated": "meditation spiritual practice",
            "worked": "productivity ambition",
            "created": "creativity manifestation",
            "learned": "wisdom knowledge",
            "exercised": "vitality physical energy",
            "rested": "restoration self-care",
            "argued": "conflict challenge",
            "lied": "shadow work truth",
        }
        
        for action in actions[:3]:  # Top 3 actions
            theme = action_themes.get(action, action)
            query_parts.append(theme)
        
        # Combine into rich search query
        query = " ".join(query_parts)
        return query
    
    async def retrieve_context(
        self,
        sun_sign: str,
        moon_sign: str | None,
        mood: MoodType,
        actions: List[ActionType],
        zodiac_element: str,
        max_results: int = 5,
    ) -> str:
        """
        Retrieve relevant astrology/spiritual context from Knowledge Base.
        
        Args:
            sun_sign: User's sun sign
            moon_sign: User's moon sign (optional)
            mood: Current mood
            actions: Today's actions
            zodiac_element: Fire/Earth/Air/Water
            max_results: Number of chunks to retrieve
            
        Returns:
            Formatted string with enriched context for Claude
        """
        try:
            # Build semantic search query
            query = self._build_search_query(
                sun_sign, moon_sign, mood, actions, zodiac_element
            )
            
            print(f"🔍 Searching KB with query: {query}")
            
            # Retrieve from Knowledge Base
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=settings.bedrock_knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results,
                    }
                }
            )
            
            # Extract and format results
            retrieved_results = response.get('retrievalResults', [])
            
            if not retrieved_results:
                print("⚠️  No results from KB, returning empty context")
                return ""
            
            print(f"✅ Retrieved {len(retrieved_results)} chunks from KB")
            
            # Format chunks for Claude
            context_chunks = []
            for i, result in enumerate(retrieved_results, 1):
                raw_content = result['content']['text']
                score = result.get('score', 0)
                
                print(f"   Chunk {i} score: {score:.3f}")
                
                # Include all results with score > 0.3 (lowered threshold)
                if score > 0.3:
                    # Parse the JSON to extract just the "content" field
                    try:
                        import json
                        doc = json.loads(raw_content)
                        clean_content = doc.get('content', raw_content)
                        context_chunks.append(f"Insight {i}: {clean_content}")
                    except:
                        # If not JSON, use as-is
                        context_chunks.append(f"Insight {i}: {raw_content}")
            
            if not context_chunks:
                print("⚠️  All chunks filtered out (scores too low)")
                return ""
            
            # Format as enriched context
            enriched_context = "\n\n".join(context_chunks)
            
            return f"""ENRICHED ASTROLOGICAL CONTEXT (from real-time sources):

{enriched_context}

Use these insights to personalize the reflection."""
            
        except Exception as e:
            print(f"❌ KB retrieval error: {e}")
            # Return empty string on error (reflection will still work without it)
            return ""
