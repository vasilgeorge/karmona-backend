"""
Daily Astrology Scraper
Scrapes astrology sites and uploads to S3 for Knowledge Base
"""

import json
from datetime import date, datetime
from typing import List, Dict, Any
import boto3

from app.core.config import settings
from app.services.browser_scraper import BrowserScraper


class DailyScraper:
    """
    Scrapes astrology and spiritual sites daily.
    Uploads formatted documents to S3 for Knowledge Base ingestion.
    """
    
    def __init__(self):
        """Initialize daily scraper."""
        self.browser_scraper = BrowserScraper()
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    
    def scrape_nypost_astrology(self) -> Dict[str, Any]:
        """Scrape NY Post astrology section."""
        result = self.browser_scraper.fetch_and_extract(
            url="https://nypost.com/astrology/",
            extraction_prompt="""
            Extract today's main astrology insights and cosmic events from this page.
            Include:
            1. Featured headline and its key insights
            2. Any mentions of planetary transits or cosmic events
            3. Guidance for specific zodiac signs if mentioned
            
            Format as a detailed summary covering all important astrological information.
            """
        )
        
        if result['success']:
            return {
                "source": "nypost",
                "url": "https://nypost.com/astrology/",
                "content": result['data'],
                "tags": ["cosmic-events", "daily-astrology"],
            }
        return None
    
    def scrape_cafe_astrology(self) -> Dict[str, Any]:
        """Scrape Cafe Astrology daily aspects."""
        result = self.browser_scraper.fetch_and_extract(
            url="https://www.cafeastrology.com/",
            extraction_prompt="""
            Extract today's astrological information:
            1. Current moon phase and moon sign
            2. Planetary aspects happening today
            3. Any retrograde planets
            4. Daily cosmic energy summary
            
            Be specific and include all relevant astrological details.
            """
        )
        
        if result['success']:
            return {
                "source": "cafeastrology",
                "url": "https://www.cafeastrology.com/",
                "content": result['data'],
                "tags": ["moon-phase", "aspects", "transits"],
            }
        return None
    
    def scrape_spiritual_wisdom(self) -> Dict[str, Any]:
        """Scrape spiritual wisdom sites."""
        result = self.browser_scraper.fetch_and_extract(
            url="https://tinybuddha.com/",
            extraction_prompt="""
            Extract today's or recent spiritual wisdom and teachings.
            Look for:
            1. Daily inspirational quotes or teachings
            2. Mindfulness practices
            3. Guidance on intention-setting or self-reflection
            
            Summarize the key spiritual insights in an accessible way.
            """
        )
        
        if result['success']:
            return {
                "source": "tinybuddha",
                "url": "https://tinybuddha.com/",
                "content": result['data'],
                "tags": ["spiritual-wisdom", "mindfulness"],
            }
        return None
    
    def _upload_to_s3(self, document: Dict[str, Any], today: date) -> bool:
        """
        Upload document to S3 in Knowledge Base-friendly format.
        
        Args:
            document: Scraped document with content and metadata
            today: Current date
            
        Returns:
            True if upload successful
        """
        try:
            # Create filename with date
            source = document['source']
            filename = f"daily/{today.isoformat()}/{source}.json"
            
            # Format document for Knowledge Base
            kb_document = {
                "id": f"{source}-{today.isoformat()}",
                "date": today.isoformat(),
                "source": document['source'],
                "url": document['url'],
                "content": document['content'],
                "metadata": {
                    "tags": document.get('tags', []),
                    "scraped_at": datetime.utcnow().isoformat(),
                }
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.s3_astrology_bucket,
                Key=filename,
                Body=json.dumps(kb_document, indent=2),
                ContentType='application/json',
            )
            
            print(f"✅ Uploaded {filename} to S3")
            return True
            
        except Exception as e:
            print(f"❌ Failed to upload {source}: {e}")
            return False
    
    def _sync_knowledge_base(self) -> bool:
        """Trigger Knowledge Base to sync with new S3 data."""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=settings.bedrock_knowledge_base_id,
                dataSourceId='karmona-astrology-data',  # Your data source name
            )
            
            ingestion_job_id = response['ingestionJob']['ingestionJobId']
            print(f"✅ Started KB sync job: {ingestion_job_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to sync KB: {e}")
            return False
    
    def run_daily_scrape(self) -> Dict[str, Any]:
        """
        Main method: Run full daily scraping pipeline.
        
        Returns:
            Summary of scraping results
        """
        today = date.today()
        print(f"🌅 Starting daily scrape for {today.isoformat()}")
        print("=" * 60)
        
        results = {
            "date": today.isoformat(),
            "scraped": [],
            "failed": [],
            "uploaded": 0,
        }
        
        # Scrape all sources (synchronously, one at a time)
        scraping_tasks = [
            ("nypost", self.scrape_nypost_astrology),
            ("cafeastrology", self.scrape_cafe_astrology),
            ("tinybuddha", self.scrape_spiritual_wisdom),
        ]
        
        for source_name, scrape_func in scraping_tasks:
            print(f"\n📰 Scraping {source_name}...")
            try:
                document = scrape_func()
                if document:
                    # Upload to S3
                    if self._upload_to_s3(document, today):
                        results['scraped'].append(source_name)
                        results['uploaded'] += 1
                    else:
                        results['failed'].append(source_name)
                else:
                    results['failed'].append(source_name)
            except Exception as e:
                print(f"❌ Error scraping {source_name}: {e}")
                results['failed'].append(source_name)
        
        # Sync Knowledge Base with new data
        if results['uploaded'] > 0:
            print(f"\n🔄 Syncing Knowledge Base...")
            self._sync_knowledge_base()
        
        print("\n" + "=" * 60)
        print(f"✅ Daily scrape complete!")
        print(f"   Scraped: {len(results['scraped'])}")
        print(f"   Failed: {len(results['failed'])}")
        print(f"   Uploaded: {results['uploaded']}")
        
        return results

