#!/usr/bin/env python3
"""
Picard product catalog scraper.

Usage:
    python run_scraper.py --map              # Discover all product URLs
    python run_scraper.py --crawl            # Crawl pending URLs
    python run_scraper.py --crawl --limit 10 # Crawl 10 pending URLs
    python run_scraper.py                    # Map + crawl all (legacy mode)
    python run_scraper.py --status           # Show current status
    python run_scraper.py --reset            # Delete all data and start fresh
"""
import argparse
from pathlib import Path

from scraper.crawler import (
    map_urls,
    crawl_pending,
    crawl_all,
    reset_data,
    retry_failed,
    load_url_state,
    load_catalog,
    DEFAULT_URLS_PATH,
    DEFAULT_PRODUCTS_PATH,
)


def show_status():
    """Display current scraping status."""
    print("=" * 50)
    print("PICARD-GPT SCRAPER STATUS")
    print("=" * 50)

    # URL state
    state = load_url_state()
    print(f"\nURL State ({DEFAULT_URLS_PATH}):")
    print(f"  Pending:  {len(state['pending']):,} URLs")
    print(f"  Crawled:  {len(state['crawled']):,} URLs")
    print(f"  Failed:   {len(state['failed']):,} URLs")
    if state["metadata"]["mapped_at"]:
        print(f"  Last mapped: {state['metadata']['mapped_at']}")
    if state["metadata"]["last_crawl_at"]:
        print(f"  Last crawl:  {state['metadata']['last_crawl_at']}")

    # Product catalog
    catalog = load_catalog()
    print(f"\nProduct Catalog ({DEFAULT_PRODUCTS_PATH}):")
    print(f"  Products: {catalog['metadata']['product_count']:,}")
    if catalog["metadata"].get("last_updated_at"):
        print(f"  Last updated: {catalog['metadata']['last_updated_at']}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Picard product catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py --map              # Step 1: Discover URLs
  python run_scraper.py --crawl --limit 50 # Step 2: Crawl 50 products
  python run_scraper.py --crawl            # Step 2: Crawl all pending
  python run_scraper.py --status           # Check progress
  python run_scraper.py --reset            # Start over
        """
    )

    parser.add_argument(
        "--map",
        action="store_true",
        help="Discover product URLs from picard.fr (saves to data/urls.json)"
    )
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Crawl pending URLs and extract product data"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of URLs to crawl (use with --crawl)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current scraping status"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all data files and start fresh"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Move failed URLs back to pending for retry"
    )

    args = parser.parse_args()

    # Handle --status
    if args.status:
        show_status()
        return

    # Handle --reset
    if args.reset:
        confirm = input("This will delete all scraped data. Are you sure? [y/N] ")
        if confirm.lower() == 'y':
            reset_data()
            print("Data reset complete.")
        else:
            print("Cancelled.")
        return

    # Handle --retry-failed
    if args.retry_failed:
        state = load_url_state()
        failed_count = len(state["failed"])
        if failed_count == 0:
            print("No failed URLs to retry.")
            return

        count = retry_failed()
        print(f"Moved {count} failed URLs back to pending.")
        print()
        print("Next: Run 'python run_scraper.py --crawl' to retry")
        return

    # Handle --map
    if args.map:
        print("Mapping product URLs from picard.fr...")
        state = map_urls()
        print()
        print("=" * 50)
        print("Mapping complete!")
        print(f"  Pending URLs: {len(state['pending']):,}")
        print(f"  Already crawled: {len(state['crawled']):,}")
        print(f"  Previously failed: {len(state['failed']):,}")
        print()
        print("Next: Run 'python run_scraper.py --crawl' to extract products")
        return

    # Handle --crawl
    if args.crawl:
        state = load_url_state()
        if not state["pending"]:
            print("No pending URLs. Run 'python run_scraper.py --map' first.")
            return

        print(f"Crawling products from pending URLs...")
        print(f"  Pending: {len(state['pending']):,} URLs")
        if args.limit:
            print(f"  Limit: {args.limit}")
        print()

        products, failed = crawl_pending(limit=args.limit)

        print()
        print("=" * 50)
        print("Crawl complete!")
        print(f"  Extracted: {len(products)} products")
        print(f"  Failed: {len(failed)} URLs")

        # Show updated status
        state = load_url_state()
        catalog = load_catalog()
        print()
        print(f"  Total products in catalog: {catalog['metadata']['product_count']:,}")
        print(f"  Remaining pending URLs: {len(state['pending']):,}")

        if failed:
            print()
            print("Failed URLs (first 5):")
            for url in failed[:5]:
                print(f"  - {url}")
        return

    # Legacy mode: map + crawl all at once
    if not args.map and not args.crawl:
        print("Running in legacy mode (map + crawl all)...")
        print(f"  Limit: {args.limit or 'None (all products)'}")
        print()

        products, failed = crawl_all(limit=args.limit)

        print()
        print("=" * 50)
        print("Scraping complete!")
        print(f"  Successful: {len(products)} products")
        print(f"  Failed: {len(failed)} URLs")


if __name__ == "__main__":
    main()
