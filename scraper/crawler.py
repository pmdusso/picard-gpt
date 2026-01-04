import json
import logging
from datetime import datetime
from pathlib import Path

from firecrawl import FirecrawlApp

from .config import FIRECRAWL_API_KEY
from .schemas import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

# Default paths
DEFAULT_URLS_PATH = Path("data/urls.json")
DEFAULT_PRODUCTS_PATH = Path("data/products.json")


# =============================================================================
# URL State Management
# =============================================================================

def load_url_state(path: Path = DEFAULT_URLS_PATH) -> dict:
    """Load URL tracking state from JSON file."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "metadata": {
            "mapped_at": None,
            "last_crawl_at": None,
        },
        "pending": [],
        "crawled": [],
        "failed": []
    }


def save_url_state(state: dict, path: Path = DEFAULT_URLS_PATH) -> None:
    """Save URL tracking state to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved URL state to {path}")


def reset_data(urls_path: Path = DEFAULT_URLS_PATH, products_path: Path = DEFAULT_PRODUCTS_PATH) -> None:
    """Delete both URL state and products files."""
    for path in [urls_path, products_path]:
        if path.exists():
            path.unlink()
            logger.info(f"Deleted {path}")
        else:
            logger.info(f"{path} does not exist, skipping")


def retry_failed(urls_path: Path = DEFAULT_URLS_PATH) -> int:
    """Move all failed URLs back to pending for retry."""
    state = load_url_state(urls_path)

    failed_count = len(state["failed"])
    if failed_count == 0:
        logger.info("No failed URLs to retry.")
        return 0

    # Move failed to pending
    state["pending"].extend(state["failed"])
    state["failed"] = []

    save_url_state(state, urls_path)
    logger.info(f"Moved {failed_count} failed URLs back to pending")

    return failed_count


# =============================================================================
# URL Discovery (Mapping)
# =============================================================================

def map_urls(urls_path: Path = DEFAULT_URLS_PATH) -> dict:
    """
    Discover all product URLs from picard.fr and save to state file.
    Merges with existing URLs (won't re-add already crawled ones).
    """
    logger.info("Mapping product URLs from picard.fr...")

    result = app.map_url(
        "https://www.picard.fr",
        search="produits"
    ) if hasattr(app, 'map_url') else app.v1.map_url(
        "https://www.picard.fr",
        search="produits"
    )

    if isinstance(result, dict):
        urls = result.get("links", [])
    elif hasattr(result, "links"):
        urls = result.links
    else:
        urls = result

    logger.info(f"Discovered {len(urls)} total URLs from Firecrawl")

    # Filter to only product pages
    product_urls = set(url for url in urls if "/produits/" in url)
    logger.info(f"Filtered to {len(product_urls)} product URLs")

    # Load existing state and merge
    state = load_url_state(urls_path)

    existing_crawled = set(state["crawled"])
    existing_pending = set(state["pending"])
    existing_failed = set(state["failed"])

    # New URLs = discovered - (already crawled + already pending + already failed)
    all_known = existing_crawled | existing_pending | existing_failed
    new_urls = product_urls - all_known

    # Add new URLs to pending
    state["pending"] = list(existing_pending | new_urls)
    state["metadata"]["mapped_at"] = datetime.now().isoformat()

    save_url_state(state, urls_path)

    logger.info(f"URL state: {len(state['pending'])} pending, {len(state['crawled'])} crawled, {len(state['failed'])} failed")
    logger.info(f"Added {len(new_urls)} new URLs to pending")

    return state


# =============================================================================
# Product Extraction (Crawling)
# =============================================================================

def extract_product(url: str) -> Product | None:
    """Extract product data from a single URL."""
    try:
        result = app.scrape_url(
            url,
            formats=["extract"],
            extract={
                "schema": Product.model_json_schema(),
                "prompt": "Extract the product information from this Picard frozen food product page. Determine dietary flags (vegetarian, vegan, gluten-free, lactose-free) from ingredients or labels if available."
            }
        ) if hasattr(app, 'scrape_url') else app.v1.scrape_url(
            url,
            formats=["extract"],
            extract={
                "schema": Product.model_json_schema(),
                "prompt": "Extract the product information from this Picard frozen food product page. Determine dietary flags (vegetarian, vegan, gluten-free, lactose-free) from ingredients or labels if available."
            }
        )

        if isinstance(result, dict):
            extract_data = result.get("extract", {})
        elif hasattr(result, "extract"):
            extract_data = result.extract
        elif hasattr(result, "data") and isinstance(result.data, dict):
            extract_data = result.data.get("extract", {})
        else:
            logger.warning(f"Unexpected response format from Firecrawl: {type(result)}")
            return None

        if extract_data:
            if isinstance(extract_data, dict):
                extract_data["url"] = url
                return Product.model_validate(extract_data)
            else:
                data_dict = extract_data.model_dump() if hasattr(extract_data, "model_dump") else dict(extract_data)
                data_dict["url"] = url
                return Product.model_validate(data_dict)

        return None

    except Exception as e:
        logger.error(f"Failed to extract product from {url}: {e}")
        return None


def crawl_pending(
    limit: int | None = None,
    urls_path: Path = DEFAULT_URLS_PATH,
    products_path: Path = DEFAULT_PRODUCTS_PATH
) -> tuple[list[Product], list[str]]:
    """
    Crawl pending URLs and append products to catalog.

    Args:
        limit: Max number of URLs to crawl in this run
        urls_path: Path to URL state file
        products_path: Path to products catalog file

    Returns:
        Tuple of (newly extracted products, failed URLs)
    """
    # Load URL state
    state = load_url_state(urls_path)
    pending = state["pending"]

    if not pending:
        logger.info("No pending URLs to crawl. Run with --map first.")
        return [], []

    # Apply limit
    urls_to_crawl = pending[:limit] if limit else pending
    logger.info(f"Crawling {len(urls_to_crawl)} URLs (of {len(pending)} pending)")

    new_products: list[Product] = []
    new_failed: list[str] = []

    for i, url in enumerate(urls_to_crawl, 1):
        logger.info(f"Processing {i}/{len(urls_to_crawl)}: {url}")

        product = extract_product(url)
        if product:
            new_products.append(product)
            state["crawled"].append(url)
            logger.info(f"  -> Extracted: {product.name} ({product.price}EUR)")
        else:
            new_failed.append(url)
            state["failed"].append(url)
            logger.warning(f"  -> Failed to extract")

        # Remove from pending
        state["pending"].remove(url)

    # Update state
    state["metadata"]["last_crawl_at"] = datetime.now().isoformat()
    save_url_state(state, urls_path)

    # Append to products catalog
    if new_products:
        append_products(new_products, products_path)

    return new_products, new_failed


# =============================================================================
# Product Catalog Management
# =============================================================================

def load_catalog(path: Path = DEFAULT_PRODUCTS_PATH) -> dict:
    """Load existing product catalog."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated_at": None,
            "product_count": 0,
            "source": "picard.fr"
        },
        "products": []
    }


def append_products(new_products: list[Product], path: Path = DEFAULT_PRODUCTS_PATH) -> None:
    """Append new products to existing catalog (deduplicates by URL)."""
    catalog = load_catalog(path)

    # Build set of existing URLs for deduplication
    existing_urls = {p["url"] for p in catalog["products"]}

    # Add only new products
    added = 0
    for product in new_products:
        if product.url not in existing_urls:
            catalog["products"].append(product.model_dump())
            existing_urls.add(product.url)
            added += 1

    # Update metadata
    catalog["metadata"]["last_updated_at"] = datetime.now().isoformat()
    catalog["metadata"]["product_count"] = len(catalog["products"])

    # Save
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    logger.info(f"Added {added} new products to catalog (total: {len(catalog['products'])})")


def save_catalog(products: list[Product], path: str | Path) -> None:
    """Save products to JSON file (overwrites - use append_products for incremental)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    catalog = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated_at": datetime.now().isoformat(),
            "product_count": len(products),
            "source": "picard.fr"
        },
        "products": [p.model_dump() for p in products]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(products)} products to {path}")


# =============================================================================
# Legacy function for backward compatibility
# =============================================================================

def crawl_all(limit: int | None = None) -> tuple[list[Product], list[str]]:
    """
    Legacy function: discovers URLs and crawls in one go.
    For new code, use map_urls() + crawl_pending() separately.
    """
    state = map_urls()
    return crawl_pending(limit=limit)
