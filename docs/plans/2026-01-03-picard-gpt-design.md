# Picard-GPT Design Document

**Date:** 2026-01-03
**Status:** Approved

## Overview

A personal shopping assistant for Picard (French frozen food store) that helps non-French speakers navigate the product catalog, plan meals within a budget, and respect dietary restrictions.

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | Best for LLM tooling, Pydantic schemas, data processing |
| Data scope | Minimal catalog | Fast validation, lower API costs |
| Interface | Prompt template only | No UI needed for MVP, portable to any LLM |
| Dietary filters | Basic (vegetarian, vegan, gluten-free, lactose-free) | Matches minimal data approach |
| Pricing model | Budget planner | Weekly/monthly meal planning within budget |
| Data freshness | Manual refresh | Simple, no infrastructure needed |

## Project Structure

```
picard-gpt/
├── scraper/
│   ├── __init__.py
│   ├── crawler.py        # Firecrawl integration
│   ├── schemas.py        # Pydantic models for product data
│   └── config.py         # Load API keys from .env
├── data/
│   └── products.json     # Extracted product catalog
├── prompts/
│   └── system_prompt.md  # The LLM system prompt template
├── requirements.txt
├── .env                  # API keys (not committed)
└── README.md
```

## Product Data Schema

```python
from pydantic import BaseModel, Field
from enum import Enum

class ProductType(str, Enum):
    MEAT = "meat"
    FISH = "fish"
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    READY_MEAL = "ready_meal"
    APPETIZER = "appetizer"
    DESSERT = "dessert"
    BREAD = "bread"
    BREAKFAST = "breakfast"
    OTHER = "other"

class Product(BaseModel):
    name: str = Field(description="Product name")
    price: float = Field(description="Price in EUR")
    category: str = Field(description="Picard category (e.g., 'Plats cuisinés')")
    product_type: ProductType = Field(description="General food type")
    url: str = Field(description="Product page URL")
    image_url: str | None = Field(description="Main product image")

    # Dietary flags
    is_vegetarian: bool = Field(default=False)
    is_vegan: bool = Field(default=False)
    is_gluten_free: bool = Field(default=False)
    is_lactose_free: bool = Field(default=False)

    # For budget planning
    weight_grams: int | None = Field(description="Net weight in grams")
    servings: int | None = Field(description="Number of portions")
```

## Crawling Strategy

1. Use Firecrawl's `map_url` to discover all product URLs on picard.fr
2. Extract structured data from each product page using the Pydantic schema
3. Save results to `data/products.json` with timestamp metadata
4. Log failed extractions for manual review

```python
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os

load_dotenv()
app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

# Discover product URLs
urls = app.map_url("https://www.picard.fr", search="produits")

# Extract from each page
products = []
for url in urls:
    result = app.scrape_url(url, {
        "formats": ["extract"],
        "extract": {"schema": Product.model_json_schema()}
    })
    products.append(result["extract"])
```

## System Prompt Template

```markdown
# You are a personal Picard shopping assistant

You help users plan their meals and shopping at Picard (a French frozen food
store) while respecting their budget and dietary restrictions.

## Your capabilities

- Suggest products based on preferences (meat, fish, vegetarian, desserts...)
- Plan meals for a week within a given budget
- Filter products by dietary needs: vegetarian, vegan, gluten-free, lactose-free
- Propose balanced meal combinations (starter/main/dessert)
- Translate French product names and explain what dishes are

## How to interact

1. First, ask for the budget (weekly or monthly)
2. Ask about dietary restrictions
3. Ask about preferences (types of dishes, number of meals to plan)
4. Propose a meal plan with products and running total

## Product catalog

<products>
{{PRODUCTS_JSON}}
</products>

## Rules

- Stay within the stated budget
- NEVER recommend a product that violates the user's dietary restrictions
- Show the price for each suggested product
- Provide a running total with each suggestion
- Explain what each French dish/product is in English
```

## Implementation Phases

### Phase 1: Project Setup
- Initialize Python project with `requirements.txt`
- Create folder structure
- Configure `.env` for API key

### Phase 2: Scraper Development
- Implement Pydantic schema (`schemas.py`)
- Build crawler to discover product URLs
- Extract structured data to `data/products.json`
- Add error handling and logging

### Phase 3: Prompt Template
- Create `prompts/system_prompt.md`
- Build script to inject products into prompt
- Output ready-to-use prompt file

### Phase 4: Validation
- Test complete prompt with Claude or other LLM
- Verify recommendations accuracy
- Adjust schema/prompt based on real data quality
