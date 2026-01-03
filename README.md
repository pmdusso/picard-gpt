# Picard-GPT

A personal shopping assistant for [Picard](https://www.picard.fr) (French frozen food store) that helps non-French speakers navigate the product catalog, plan meals within a budget, and respect dietary restrictions.

## Features

- Scrapes Picard's product catalog using [Firecrawl](https://firecrawl.dev)
- Extracts product data: name, price, category, type, dietary flags
- Generates an LLM system prompt for personalized meal planning
- Supports dietary filters: vegetarian, vegan, gluten-free, lactose-free
- Budget-aware meal planning (weekly/monthly)
- Incremental scraping with resume support

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Firecrawl API key:**
   ```bash
   echo "FIRECRAWL_API_KEY=your-api-key" > .env
   ```

## Usage

### 1. Scrape the product catalog

**Step 1: Map all product URLs**
```bash
python run_scraper.py --map
```
This discovers all product URLs and saves them to `data/urls.json`.

**Step 2: Crawl products (in batches)**
```bash
python run_scraper.py --crawl --limit 50  # Crawl 50 products
python run_scraper.py --crawl             # Crawl all remaining
```
Products are appended to `data/products.json`. Run multiple times to continue where you left off.

**Check progress:**
```bash
python run_scraper.py --status
```

**Start over:**
```bash
python run_scraper.py --reset
```

### 2. Build the prompt

```bash
python build_prompt.py
```

Output: `prompts/ready_prompt.md`

### 3. Use with an LLM

Copy the contents of `prompts/ready_prompt.md` as your system prompt in Claude, ChatGPT, or any LLM.

## Project Structure

```
picard-gpt/
├── run_scraper.py      # Entry point for scraping
├── build_prompt.py     # Builds final prompt with products
├── scraper/
│   ├── config.py       # Loads API key from .env
│   ├── schemas.py      # Product data model
│   └── crawler.py      # Firecrawl integration
├── prompts/
│   └── system_prompt.md    # Prompt template
├── data/
│   ├── urls.json           # URL tracking state (generated)
│   └── products.json       # Scraped catalog (generated)
└── docs/
    └── plans/              # Design documents
```

## How It Works

1. **Mapping**: Uses Firecrawl's `map_url` to discover all product URLs on picard.fr
2. **Crawling**: Extracts product data from each URL using Pydantic schema
3. **Tracking**: Maintains state of pending/crawled/failed URLs for incremental runs
4. **Prompt Generation**: Injects the product catalog into a system prompt template
5. **Interaction**: The LLM uses the catalog to recommend products, plan meals, and translate French product names

## License

MIT
