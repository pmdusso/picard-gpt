#!/usr/bin/env python3
"""
Build the final prompt by injecting product catalog into the template.

Usage:
    python build_prompt.py
    python build_prompt.py --catalog data/products.json --output prompts/ready_prompt.md
"""
import argparse
import json
from pathlib import Path


def build_prompt(catalog_path: str, template_path: str, output_path: str) -> None:
    """Build the final prompt with product data."""

    # Load catalog
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Create a compact version of products for the prompt
    # (only include fields needed for recommendations)
    products_for_prompt = []
    for p in catalog["products"]:
        products_for_prompt.append({
            "name": p["name"],
            "price": p["price"],
            "category": p["category"],
            "type": p["product_type"],
            "vegetarian": p["is_vegetarian"],
            "vegan": p["is_vegan"],
            "gluten_free": p["is_gluten_free"],
            "lactose_free": p["is_lactose_free"],
            "servings": p.get("servings"),
            "weight_grams": p.get("weight_grams"),
        })

    products_json = json.dumps(products_for_prompt, ensure_ascii=False, indent=2)

    # Replace placeholder
    final_prompt = template.replace("{{PRODUCTS_JSON}}", products_json)

    # Save output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(final_prompt)

    print(f"Built prompt with {len(products_for_prompt)} products")
    print(f"  Catalog: {catalog_path}")
    print(f"  Template: {template_path}")
    print(f"  Output: {output_path}")
    print()
    print(f"Prompt size: {len(final_prompt):,} characters")


def main():
    parser = argparse.ArgumentParser(description="Build final prompt with product catalog")
    parser.add_argument(
        "--catalog",
        type=str,
        default="data/products.json",
        help="Path to product catalog JSON"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="prompts/system_prompt.md",
        help="Path to prompt template"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="prompts/ready_prompt.md",
        help="Output path for final prompt"
    )
    args = parser.parse_args()

    build_prompt(args.catalog, args.template, args.output)


if __name__ == "__main__":
    main()
