# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Picard-GPT is a personal shopping assistant for Picard (French frozen food store). It scrapes the product catalog using Firecrawl and generates an LLM system prompt for meal planning within budget and dietary constraints.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Step 1: Map all product URLs
python run_scraper.py --map

# Step 2: Crawl products (incremental)
python run_scraper.py --crawl --limit 50  # Batch of 50
python run_scraper.py --crawl             # All remaining

# Check progress
python run_scraper.py --status

# Retry failed URLs
python run_scraper.py --retry-failed

# Update existing products with new fields (ref, price_per_kg, nutriscore)
python run_scraper.py --update-fields --limit 50  # Batch of 50
python run_scraper.py --update-fields             # All missing

# Reset all data
python run_scraper.py --reset

# Build the final prompt
python build_prompt.py         # Full catalog
python build_prompt.py --all   # Full catalog + dietary variations
```

## Product Schema

Key fields extracted from each product:
- `name`: Product name (French)
- `ref`: Product reference ID (e.g., "060489")
- `price`: Price in EUR
- `price_per_kg`: Price per kilogram (for value comparison)
- `nutriscore`: NutriScore rating (A, B, C, D, E)
- `category`: Picard category
- `product_type`: meat, fish, vegetable, ready_meal, dessert, etc.
- `is_vegetarian`, `is_vegan`, `is_gluten_free`, `is_lactose_free`: Dietary flags
- `weight_grams`, `servings`: For portion planning

## Dietary Filtering

The `build_prompt.py` script supports dietary filtering to generate specialized, token-efficient prompts:
- `--vegetarian`
- `--vegan`
- `--gluten-free`
- `--lactose-free`
- `--all`: Generates all variations at once (e.g., `ready_prompt_vegan.md`)

## Architecture

**Data Flow:**
1. `--map` → discovers URLs → saves to `data/urls.json`
2. `--crawl` → extracts products from pending URLs → appends to `data/products.json`
3. `--update-fields` → re-extracts missing fields from existing products
4. `build_prompt.py` → filters (optional) → injects products (compact JSON) into template → outputs `prompts/ready_prompt.md`

**Key Components:**
- `scraper/schemas.py`: Pydantic `Product` model with dietary flags and NutriScore
- `scraper/crawler.py`: Firecrawl integration with URL state tracking
- `prompts/system_prompt.md`: Template with `{{PRODUCTS_JSON}}` placeholder

**Data Files:**
- `data/urls.json`: Tracks pending/crawled/failed URLs
- `data/products.json`: Product catalog (incremental append)

**Configuration:**
- Firecrawl API key loaded from `.env` via `scraper/config.py`
