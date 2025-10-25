"""
Daily Astrology Scraper
Scrapes astrology sites and uploads to S3 for Knowledge Base
"""

import json
import asyncio
from datetime import date, datetime
from typing import List, Dict, Any
import boto3

from app.core.config import settings
from app.services.browser_scraper import BrowserScraper
from app.services.scraping_sources import get_enabled_sources, count_total_scrapes
from app.services.ephemeris_service import EphemerisService
from app.services.nasa_apod_service import NASAAPODService
from app.services.supabase_vector_service import SupabaseVectorService


class DailyScraper:
    """
    Scrapes astrology and spiritual sites daily.
    Uploads formatted documents to S3 for Knowledge Base ingestion.
    """
    
    def __init__(self):
        """Initialize daily scraper."""
        self.browser_scraper = BrowserScraper()
        self.ephemeris_service = EphemerisService()
        self.nasa_apod_service = NASAAPODService()
        self.vector_service = SupabaseVectorService()
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    
    def scrape_source(
        self,
        source_name: str,
        url: str,
        prompt: str,
        context: str = "general",
    ) -> Dict[str, Any] | None:
        """
        Scrape a single URL from a configured source.
        
        Args:
            source_name: Name of the source (e.g., "astrostyle")
            url: URL to scrape
            prompt: Extraction prompt (may include {sign} placeholder)
            context: Additional context (e.g., sign name)
            
        Returns:
            Formatted document or None if failed
        """
        try:
            # Format prompt with context (e.g., replace {sign})
            formatted_prompt = prompt.format(sign=context)
            
            # Scrape and extract
            result = self.browser_scraper.fetch_and_extract(
                url=url,
                extraction_prompt=formatted_prompt,
                wait_seconds=4,  # Give pages time to load
            )
            
            if result['success'] and result['data']:
                # Determine tags based on source type
                tags = []
                if context != "general":
                    tags.append(f"sign-{context.lower()}")
                tags.append(f"source-{source_name}")
                
                return {
                    "source": source_name,
                    "url": url,
                    "content": result['data'],
                    "context": context,
                    "tags": tags,
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def _upload_to_s3_and_supabase(self, document: Dict[str, Any], today: date, index: int) -> bool:
        """
        Upload document to S3 (for backup) AND Supabase pgvector (for retrieval).

        Args:
            document: Scraped document with content and metadata
            today: Current date
            index: Unique index for this document

        Returns:
            True if upload successful
        """
        try:
            # Create filename with date and context (for sign-specific)
            source = document['source']
            context = document.get('context', 'general')

            if context != "general":
                # Sign-specific: source_sign_date.json
                filename = f"daily/{today.isoformat()}/{source}_{context}.json"
                doc_id = f"{source}-{context}-{today.isoformat()}"
            else:
                # General: source_date.json
                filename = f"daily/{today.isoformat()}/{source}.json"
                doc_id = f"{source}-{today.isoformat()}"

            # Format document metadata
            metadata = {
                "date": today.isoformat(),
                "source": document['source'],
                "url": document['url'],
                "tags": document.get('tags', []),
                "scraped_at": datetime.utcnow().isoformat(),
                "context": context,
            }

            # 1. Upload to S3 (for backup/compliance)
            kb_document = {
                "id": doc_id,
                "content": document['content'],
                "metadata": metadata,
            }

            self.s3_client.put_object(
                Bucket=settings.s3_astrology_bucket,
                Key=filename,
                Body=json.dumps(kb_document, indent=2),
                ContentType='application/json',
            )
            print(f"✅ Uploaded {filename} to S3")

            # 2. Store in Supabase pgvector (for fast retrieval)
            # Run async operation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.vector_service.store_document(
                        document_id=doc_id,
                        content=document['content'],
                        metadata=metadata,
                    )
                )
                print(f"✅ Stored {doc_id} in Supabase pgvector")
            finally:
                loop.close()

            return True

        except Exception as e:
            print(f"❌ Failed to upload {source}: {e}")
            return False
    
    def _sync_knowledge_base(self) -> bool:
        """
        DEPRECATED: AWS Knowledge Base sync is no longer used.
        We now use Supabase pgvector instead of AWS OpenSearch.
        Keeping this method for backwards compatibility but it does nothing.
        """
        print("ℹ️  KB sync skipped (using Supabase pgvector instead of AWS KB)")
        return True
    
    def run_daily_scrape(self) -> Dict[str, Any]:
        """
        Main method: Run full daily scraping pipeline.
        
        Returns:
            Summary of scraping results
        """
        today = date.today()
        sources = get_enabled_sources()
        total_scrapes = count_total_scrapes()
        
        print(f"🌅 Starting daily scrape for {today.isoformat()}")
        print(f"📊 Total sources: {len(sources)} | Total URLs: {total_scrapes}")
        print("=" * 60)
        
        results = {
            "date": today.isoformat(),
            "scraped": [],
            "failed": [],
            "uploaded": 0,
            "total": total_scrapes + 1,  # +1 for ephemeris (NASA APOD disabled)
        }
        
        document_index = 0

        # STEP 1: Calculate planetary positions (no scraping needed)
        print(f"\n{'='*60}")
        print("🌌 STEP 1: Calculating Planetary Positions (Ephemeris)")
        print(f"{'='*60}")

        try:
            ephemeris_result = self.ephemeris_service.run_daily_calculation(today)
            if ephemeris_result.get('success'):
                results['scraped'].append('ephemeris_planetary_positions')
                results['uploaded'] += 1
                print("✅ Ephemeris calculation complete and uploaded")
            else:
                results['failed'].append('ephemeris_planetary_positions')
                print("❌ Ephemeris calculation failed")
        except Exception as e:
            print(f"❌ Ephemeris error: {e}")
            results['failed'].append('ephemeris_planetary_positions')

        # STEP 2: Fetch NASA APOD (API call) - DISABLED due to timeout issues
        # print(f"\n{'='*60}")
        # print("🚀 STEP 2: Fetching NASA Astronomy Picture of the Day")
        # print(f"{'='*60}")
        #
        # try:
        #     apod_result = self.nasa_apod_service.run_daily_fetch(today)
        #     if apod_result.get('success'):
        #         results['scraped'].append('nasa_apod')
        #         results['uploaded'] += 1
        #         print("✅ NASA APOD fetched and uploaded")
        #     else:
        #         results['failed'].append('nasa_apod')
        #         print("❌ NASA APOD fetch failed")
        # except Exception as e:
        #     print(f"❌ NASA APOD error: {e}")
        #     results['failed'].append('nasa_apod')

        # STEP 2: Process each configured source (web scraping)
        for source_config in sources:
            print(f"\n{'='*60}")
            print(f"📰 Source: {source_config.name} ({source_config.source_type})")
            print(f"{'='*60}")
            
            # Get all URLs for this source (1 or 12 depending on type)
            urls_to_scrape = source_config.get_urls()
            print(f"   URLs to scrape: {len(urls_to_scrape)}")
            
            for url_info in urls_to_scrape:
                url = url_info['url']
                context = url_info['context']
                
                print(f"\n   → {context}: {url}")
                
                try:
                    # Scrape this URL
                    document = self.scrape_source(
                        source_name=source_config.name,
                        url=url,
                        prompt=source_config.extraction_prompt,
                        context=context,
                    )
                    
                    if document:
                        # Print extracted content for inspection
                        print(f"\n      📝 Extracted content:")
                        print(f"      {'-' * 50}")
                        content_preview = document['content'][:300] + "..." if len(document['content']) > 300 else document['content']
                        print(f"      {content_preview}")
                        print(f"      {'-' * 50}")
                        print(f"      Full length: {len(document['content'])} chars")

                        # Upload to S3 AND Supabase
                        if self._upload_to_s3_and_supabase(document, today, document_index):
                            results['scraped'].append(f"{source_config.name}_{context}")
                            results['uploaded'] += 1
                            document_index += 1
                        else:
                            results['failed'].append(f"{source_config.name}_{context}")
                    else:
                        results['failed'].append(f"{source_config.name}_{context}")
                        
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    results['failed'].append(f"{source_config.name}_{context}")
        
        # Sync Knowledge Base with new data
        if results['uploaded'] > 0:
            print(f"\n🔄 Syncing Knowledge Base...")
            self._sync_knowledge_base()
        
        print("\n" + "=" * 60)
        print(f"✅ Daily scrape complete!")
        print(f"   Total attempted: {results['total']}")
        print(f"   Successfully scraped: {len(results['scraped'])}")
        print(f"   Failed: {len(results['failed'])}")
        print(f"   Uploaded to S3: {results['uploaded']}")
        print(f"   Success rate: {int((results['uploaded'] / results['total']) * 100)}%")
        
        return results
