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


# Paleo diet exclusion keywords (grains, dairy, legumes, processed)
PALEO_EXCLUDE_KEYWORDS = [
    'pizza', 'pâte', 'pain', 'riz', 'pâtes', 'crêpe', 'gaufre',
    'brioche', 'croissant', 'biscuit', 'gâteau', 'tarte', 'feuilleté',
    'gratin', 'béchamel', 'fromage', 'emmental', 'mozzarella',
    'haricot', 'lentille', 'pois chiche', 'fève'
]

# Lite version: main meals + breakfast (no desserts, appetizers, fruits, other)
LITE_TYPES = ['ready_meal', 'meat', 'fish', 'vegetable', 'bread', 'breakfast']


def is_paleo_excluded(product: dict) -> bool:
    """Check if product should be excluded from paleo diet."""
    text = (product['name'] + ' ' + product['category']).lower()
    return any(kw in text for kw in PALEO_EXCLUDE_KEYWORDS)


def filter_paleo(products: list) -> list:
    """Filter products for paleo diet compatibility."""
    paleo_types = ['meat', 'fish', 'vegetable', 'fruit']
    result = []

    for p in products:
        # Skip if excluded by keywords
        if is_paleo_excluded(p):
            continue

        # Include base paleo types
        if p['product_type'] in paleo_types:
            result.append(p)
        # Include ready_meals only if gluten-free AND lactose-free
        elif p['product_type'] == 'ready_meal':
            if p.get('is_gluten_free') and p.get('is_lactose_free'):
                result.append(p)

    return result


def filter_lite(products: list) -> list:
    """Filter for lite version: main meals + breakfast, no desserts/appetizers."""
    return [p for p in products if p['product_type'] in LITE_TYPES]


def build_prompt(catalog_path: str, template_path: str, output_path: str, filters: dict = None) -> None:
    """Build the final prompt with product data and optional filtering."""

    # Load catalog
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Apply filters if provided
    products = catalog["products"]
    if filters:
        # Special composite filters
        if filters.get("paleo"):
            products = filter_paleo(products)
        if filters.get("lite"):
            products = filter_lite(products)
        # Simple boolean filters
        if filters.get("vegetarian"):
            products = [p for p in products if p.get("is_vegetarian")]
        if filters.get("vegan"):
            products = [p for p in products if p.get("is_vegan")]
        if filters.get("gluten_free"):
            products = [p for p in products if p.get("is_gluten_free")]
        if filters.get("lactose_free"):
            products = [p for p in products if p.get("is_lactose_free")]

    # Create a compact version of products for the prompt
    # (only include fields needed for recommendations)
    products_for_prompt = []
    for p in products:
        product = {
            "n": p["name"],
            "p": p["price"],
            "c": p["category"],
            "t": p["product_type"],
            "vg": p["is_vegetarian"],
            "vn": p["is_vegan"],
            "gf": p["is_gluten_free"],
            "lf": p["is_lactose_free"],
            "s": p.get("servings"),
            "w": p.get("weight_grams"),
        }
        # Add new fields if present
        if p.get("ref"):
            product["ref"] = p["ref"]
        if p.get("price_per_kg"):
            product["pk"] = p["price_per_kg"]  # pk = price per kg
        if p.get("nutriscore"):
            product["ns"] = p["nutriscore"]  # ns = nutriscore
        products_for_prompt.append(product)

    products_json = json.dumps(products_for_prompt, ensure_ascii=False)

    # Replace placeholder
    final_prompt = template.replace("{{PRODUCTS_JSON}}", products_json)

    # Save output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(final_prompt)

    print(f"Built prompt with {len(products_for_prompt)} products")
    if filters:
        active_filters = [k for k, v in filters.items() if v]
        if active_filters:
            print(f"  Applied filters: {', '.join(active_filters)}")
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
    parser.add_argument(
        "--vegetarian",
        action="store_true",
        help="Filter for vegetarian products only"
    )
    parser.add_argument(
        "--vegan",
        action="store_true",
        help="Filter for vegan products only"
    )
    parser.add_argument(
        "--gluten-free",
        action="store_true",
        help="Filter for gluten-free products only"
    )
    parser.add_argument(
        "--lactose-free",
        action="store_true",
        help="Filter for lactose-free products only"
    )
    parser.add_argument(
        "--paleo",
        action="store_true",
        help="Filter for paleo diet (meat, fish, vegetables, fruits; no grains/dairy/legumes)"
    )
    parser.add_argument(
        "--lite",
        action="store_true",
        help="Lite version: main meals + breakfast (no desserts, appetizers, fruits)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all prompt variations (full + dietary filters)"
    )
    args = parser.parse_args()

    if args.all:
        # 1. Full prompt
        build_prompt(args.catalog, args.template, args.output)

        # 2. Dietary variations
        variations = [
            ("vegetarian", {"vegetarian": True}),
            ("vegan", {"vegan": True}),
            ("gluten_free", {"gluten_free": True}),
            ("lactose_free", {"lactose_free": True}),
            ("paleo", {"paleo": True}),
            ("lite", {"lite": True}),
        ]

        base_output = Path(args.output)
        for name, filters in variations:
            # Create filename like ready_prompt_vegan.md
            var_output = base_output.parent / f"{base_output.stem}_{name}{base_output.suffix}"
            build_prompt(args.catalog, args.template, str(var_output), filters)
    else:
        filters = {
            "vegetarian": args.vegetarian,
            "vegan": args.vegan,
            "gluten_free": args.gluten_free,
            "lactose_free": args.lactose_free,
            "paleo": args.paleo,
            "lite": args.lite,
        }
        build_prompt(args.catalog, args.template, args.output, filters)


if __name__ == "__main__":
    main()
