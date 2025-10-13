"""
Daily scraping cron job for Railway.
Runs automatically every day at 3am UTC.
"""

import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, '/app')

from app.services.daily_scraper import DailyScraper


def run_daily_scrape():
    """Main function to run daily scraping."""
    logger.info("🌅 Starting daily astrology scrape job")
    
    try:
        scraper = DailyScraper()
        results = scraper.run_daily_scrape()
        
        logger.info(f"✅ Scraping complete!")
        logger.info(f"   Scraped: {len(results['scraped'])}/{results['total']}")
        logger.info(f"   Uploaded: {results['uploaded']}")
        logger.info(f"   Failed: {len(results['failed'])}")
        
        if results['failed']:
            logger.warning(f"   Failed sources: {', '.join(results['failed'])}")
        
        return 0  # Success
        
    except Exception as e:
        logger.error(f"❌ Scraping job failed: {e}")
        return 1  # Failure


if __name__ == "__main__":
    exit_code = run_daily_scrape()
    sys.exit(exit_code)

