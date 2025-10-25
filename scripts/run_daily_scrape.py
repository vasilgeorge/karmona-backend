"""
Script to manually run daily scraping job.
Use this to test the scraping pipeline.
"""

import sys
sys.path.insert(0, '/Users/georgiosvasilakis/src/karmona-backend')

from app.services.daily_scraper import DailyScraper


def main():
    """Run the daily scraping job."""
    print("🌅 KARMONA DAILY ASTROLOGY SCRAPER")
    print("=" * 60)
    print("This will:")
    print("  1. Scrape astrology sites (NY Post, Cafe Astrology, etc.)")
    print("  2. Upload to S3 AND Supabase pgvector")
    print("  3. Sync Knowledge Base (optional)")
    print("=" * 60)
    print()

    scraper = DailyScraper()
    results = scraper.run_daily_scrape()

    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print("=" * 60)
    print(f"Date: {results['date']}")
    print(f"Successfully scraped: {', '.join(results['scraped']) if results['scraped'] else 'None'}")
    print(f"Failed: {', '.join(results['failed']) if results['failed'] else 'None'}")
    print(f"Uploaded to S3 + Supabase: {results['uploaded']} documents")
    print("=" * 60)


if __name__ == "__main__":
    main()

