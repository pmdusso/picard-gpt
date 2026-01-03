# GEMINI.md

Context and instructions for the Picard-GPT project.

## Project Overview

**Picard-GPT** is a Python-based utility designed to create a personal shopping assistant for Picard (a French frozen food retailer). It automates the process of:
1.  **Scraping** the Picard website for product data (names, prices, dietary info).
2.  **Structuring** that data using Pydantic models.
3.  **Injecting** the product catalog into a system prompt template.

The resulting prompt allows an LLM to act as a knowledgeable shopping assistant that can plan meals within a budget and respect dietary restrictions (Vegetarian, Vegan, Gluten-Free, Lactose-Free).

## Technology Stack

*   **Language:** Python 3
*   **Scraping:** [Firecrawl](https://firecrawl.dev) (via `firecrawl-py`)
*   **Validation:** Pydantic
*   **Config:** `python-dotenv` for environment variables

## Architecture & Data Flow

1.  **Acquisition:** `run_scraper.py` triggers the `scraper` module.
    *   **Mapping:** Discovers all product URLs on the site and stores them in `data/urls.json`.
    *   **Crawling:** Processes pending URLs from `urls.json`, extracts data using Pydantic models, and appends results to `data/products.json`.
    *   **Incremental/Resumable:** The process tracks finished and failed URLs, allowing it to be stopped and resumed without duplicating work.
2.  **Generation:** `build_prompt.py` reads the JSON catalog.
    *   Minifies the data (keeping only relevant fields for the LLM).
    *   Injects it into `prompts/system_prompt.md` replacing the `{{PRODUCTS_JSON}}` placeholder.
    *   Outputs the final artifact to `prompts/ready_prompt.md`.

## Key Files

*   `run_scraper.py`: Main entry point for the mapping and scraping process.
*   `build_prompt.py`: Main entry point for generating the LLM prompt.
*   `scraper/schemas.py`: Defines the `Product` Pydantic model and `ProductType` enum.
*   `scraper/crawler.py`: Handles interaction with Firecrawl and local state management.
*   `data/urls.json`: Tracks URL state (pending, crawled, failed).
*   `data/products.json`: Incremental product catalog.
*   `prompts/system_prompt.md`: The base template for the AI assistant.
*   `.env`: Stores the `FIRECRAWL_API_KEY`.

## Setup & Usage

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Configuration

Ensure a `.env` file exists in the root directory with your Firecrawl API key:

```env
FIRECRAWL_API_KEY=fc_...
```

### 3. Scraping Products

The scraper works in steps to allow for large-scale crawling with progress tracking.

**Step 1: Map the website (Discovery)**
Discovers all product URLs on picard.fr.
```bash
python run_scraper.py --map
```

**Step 2: Crawl products (Extraction)**
Extracts structured data from discovered URLs. Use `--limit` to process in batches.
```bash
# Crawl 50 products
python run_scraper.py --crawl --limit 50

# Crawl all remaining pending products
python run_scraper.py --crawl
```

**Step 3: Check Progress**
View counts for pending, crawled, and failed URLs.
```bash
python run_scraper.py --status
```

**Optional: Reset Data**
Deletes all local data to start fresh.
```bash
python run_scraper.py --reset
```

### 4. Building the Prompt

Once `data/products.json` is populated:
```bash
python build_prompt.py
```
The final prompt will be available at `prompts/ready_prompt.md`.

## Development Conventions

*   **Data Validation:** All scrapped data must validate against the Pydantic models in `scraper/schemas.py`.
*   **Prompt Efficiency:** The `build_prompt.py` script filters fields to reduce token usage (e.g., removing full image URLs if not needed for the text-only prompt).
*   **Secrets:** Never commit `.env` or API keys.
