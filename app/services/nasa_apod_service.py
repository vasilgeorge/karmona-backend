"""
NASA APOD (Astronomy Picture of the Day) Service
Fetches daily astronomy images and descriptions via NASA API
"""

import httpx
from datetime import date
from typing import Dict, Any
import json
import boto3

from app.core.config import settings


class NASAAPODService:
    """
    Fetch NASA's Astronomy Picture of the Day.
    
    Provides cosmic/astronomical context that can enrich astrological insights.
    """
    
    def __init__(self):
        """Initialize NASA APOD service."""
        self.api_key = settings.nasa_api_key if hasattr(settings, 'nasa_api_key') else 'DEMO_KEY'
        self.base_url = "https://api.nasa.gov/planetary/apod"
        
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    
    def fetch_apod(self, target_date: date | None = None) -> Dict[str, Any]:
        """
        Fetch APOD for a specific date.
        
        Args:
            target_date: Date to fetch (defaults to today)
            
        Returns:
            Dictionary with APOD data
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            params = {
                'api_key': self.api_key,
                'date': target_date.isoformat(),
            }
            
            response = httpx.get(self.base_url, params=params, timeout=60.0)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'success': True,
                'date': data.get('date'),
                'title': data.get('title'),
                'explanation': data.get('explanation'),
                'url': data.get('url'),
                'hdurl': data.get('hdurl'),
                'media_type': data.get('media_type', 'image'),
                'copyright': data.get('copyright'),
            }
            
        except Exception as e:
            print(f"❌ Error fetching NASA APOD: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def upload_to_s3(self, apod_data: Dict[str, Any]) -> bool:
        """
        Upload APOD data to S3 for knowledge base.
        
        Args:
            apod_data: APOD data from fetch_apod()
            
        Returns:
            True if successful
        """
        if not apod_data.get('success'):
            return False
        
        try:
            target_date = apod_data['date']
            
            # Format content for LLM
            content_parts = [
                f"**Astronomy Picture of the Day - {target_date}**",
                f"",
                f"**Title:** {apod_data['title']}",
                f"",
                f"**Description:**",
                apod_data['explanation'],
            ]
            
            if apod_data.get('copyright'):
                content_parts.append(f"")
                content_parts.append(f"**Credit:** {apod_data['copyright']}")
            
            content = "\n".join(content_parts)
            
            # Create filename
            filename = f"daily/{target_date}/nasa_apod.json"
            
            # Format for knowledge base
            kb_document = {
                "id": f"nasa_apod-{target_date}",
                "date": target_date,
                "source": "nasa_apod",
                "content": content,
                "data": {
                    "title": apod_data['title'],
                    "explanation": apod_data['explanation'],
                    "url": apod_data.get('url'),
                    "media_type": apod_data.get('media_type'),
                },
                "metadata": {
                    "tags": ["astronomy", "nasa", "daily", "cosmic"],
                    "fetched_at": date.today().isoformat(),
                }
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.s3_astrology_bucket,
                Key=filename,
                Body=json.dumps(kb_document, indent=2),
                ContentType='application/json',
            )
            
            print(f"✅ Uploaded NASA APOD to S3: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to upload NASA APOD: {e}")
            return False
    
    def run_daily_fetch(self, target_date: date | None = None) -> Dict[str, Any]:
        """
        Main method: Fetch APOD and upload to S3.
        
        Args:
            target_date: Date to fetch (defaults to today)
            
        Returns:
            Results dictionary
        """
        if target_date is None:
            target_date = date.today()
        
        print(f"🌌 Fetching NASA APOD for {target_date.isoformat()}...")
        
        # Fetch APOD
        apod_data = self.fetch_apod(target_date)
        
        if not apod_data.get('success'):
            return {
                'success': False,
                'error': apod_data.get('error'),
            }
        
        print(f"   Title: {apod_data['title']}")
        print(f"   Type: {apod_data.get('media_type', 'image')}")
        
        # Upload to S3
        uploaded = self.upload_to_s3(apod_data)
        
        return {
            'success': uploaded,
            'date': target_date.isoformat(),
            'title': apod_data['title'],
        }
