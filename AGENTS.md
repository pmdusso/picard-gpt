# Repository Guidelines

## Project Structure & Module Organization
- `run_scraper.py`: CLI entry point for mapping and crawling Picard product pages.
- `build_prompt.py`: Builds final prompts by injecting catalog JSON into `prompts/system_prompt.md`.
- `scraper/`: Core modules (`crawler.py` for Firecrawl orchestration, `schemas.py` for Pydantic models, `config.py` for `.env`).
- `prompts/`: Prompt template plus generated `ready_prompt*.md` outputs.
- `data/`: Generated state (`urls.json`, `products.json`), ignored by git.
- `docs/`: Local design docs; ignored by git.

## Build, Test, and Development Commands
- `pip install -r requirements.txt`: Install runtime dependencies.
- `python run_scraper.py --map`: Discover product URLs and write `data/urls.json`.
- `python run_scraper.py --crawl --limit 50`: Crawl a batch of pending URLs.
- `python run_scraper.py --status`: Show URL/product counts and missing fields.
- `python run_scraper.py --retry-failed`: Move failed URLs back to pending.
- `python run_scraper.py --update-fields`: Re-extract missing fields like `ref`, `price_per_kg`, `nutriscore`.
- `python build_prompt.py --all`: Generate full + dietary prompt variants in `prompts/`.

## Coding Style & Naming Conventions
- Python 3, 4-space indentation, `snake_case` for functions/vars, `PascalCase` for classes.
- Keep Pydantic fields aligned with `scraper/schemas.py`; update extraction prompts accordingly.
- Prompt JSON keys are abbreviated in `build_prompt.py` (`n`, `p`, `gf`, `lf`, etc.); preserve or document changes.
- No enforced formatter or linter; match existing style and type hints.

## Testing Guidelines
- No automated test suite in this repository.
- Use manual checks: run `--status`, inspect `data/products.json`, and open `prompts/ready_prompt*.md` for sanity.
- If you add tests, document how to run them in this section.

## Commit & Pull Request Guidelines
- Commit messages are short, imperative, and descriptive (e.g., “Add User Guide for non-developers”).
- PRs should include a concise summary, commands run, and any prompt/catalog changes.
- Do not commit secrets or generated data (`.env`, `data/*.json`).

## Security & Configuration Tips
- Set `FIRECRAWL_API_KEY` in `.env`; the scraper raises if it is missing.
- Treat scraped data as generated artifacts; regenerate instead of hand-editing.
