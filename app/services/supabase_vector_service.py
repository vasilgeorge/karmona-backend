"""
Supabase pgvector Implementation for Vector Retrieval
Replaces AWS OpenSearch with cost-effective Supabase solution
"""

import json
from typing import List, Dict, Any
import boto3
from supabase import create_client, Client

from app.core.config import settings
from app.models.schemas import MoodType, ActionType
from app.services.vector_retrieval_base import VectorRetrievalService


class SupabaseVectorService(VectorRetrievalService):
    """
    Vector retrieval using Supabase pgvector extension.
    Much cheaper than AWS OpenSearch (~$0-25/month vs ~$175/month).
    """

    def __init__(self):
        """Initialize Supabase client and Bedrock for embeddings."""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )

        # Bedrock client for generating embeddings
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Amazon Titan Embeddings.

        Args:
            text: Text to embed

        Returns:
            1536-dimensional embedding vector
        """
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=json.dumps({
                    "inputText": text,
                    "dimensions": 1024,  # Titan v2 supports 256-1024 dimensions
                    "normalize": True
                })
            )

            result = json.loads(response['body'].read())
            return result['embedding']

        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise

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
        Retrieve relevant astrology context from Supabase pgvector.

        Uses cosine similarity search on embeddings stored in Supabase.
        """
        try:
            # Build search query
            query = self._build_search_query(
                sun_sign, moon_sign, mood, actions, zodiac_element
            )

            print(f"🔍 Searching Supabase with query: {query}")

            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query)

            # Search using pgvector cosine similarity
            # Note: Supabase uses match_documents RPC function for vector search
            response = self.supabase.rpc(
                'match_astrology_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.3,
                    'match_count': max_results
                }
            ).execute()

            results = response.data

            if not results:
                print("⚠️  No results from Supabase, returning empty context")
                return ""

            print(f"✅ Retrieved {len(results)} chunks from Supabase")

            # Format chunks for Claude
            context_chunks = []
            for i, result in enumerate(results, 1):
                content = result['content']
                similarity = result.get('similarity', 0)

                print(f"   Chunk {i} similarity: {similarity:.3f}")

                # Sanitize content
                clean_content = (
                    content
                    .replace('\n', ' ')
                    .replace('\r', ' ')
                    .replace('\t', ' ')
                    .replace('  ', ' ')
                    .strip()
                )

                context_chunks.append(f"Insight {i}: {clean_content}")

            if not context_chunks:
                print("⚠️  All chunks filtered out")
                return ""

            # Format as enriched context
            enriched_context = "\n\n".join(context_chunks)

            return f"""ENRICHED ASTROLOGICAL CONTEXT (from real-time sources):

{enriched_context}

Use these insights to personalize the reflection."""

        except Exception as e:
            print(f"❌ Supabase retrieval error: {e}")
            # Return empty string on error (reflection will still work)
            return ""

    async def store_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        Store a document with its embedding in Supabase.

        Args:
            document_id: Unique identifier
            content: Document text content
            metadata: Additional metadata (source, date, tags, etc.)

        Returns:
            True if successful
        """
        try:
            # Generate embedding for content
            embedding = await self._generate_embedding(content)

            # Insert into Supabase
            self.supabase.table('astrology_documents').upsert({
                'id': document_id,
                'content': content,
                'metadata': metadata,
                'embedding': embedding,
                'created_at': metadata.get('scraped_at'),
            }).execute()

            print(f"✅ Stored document {document_id} in Supabase")
            return True

        except Exception as e:
            print(f"❌ Error storing document: {e}")
            return False
