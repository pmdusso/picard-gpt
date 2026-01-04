from enum import Enum
from pydantic import BaseModel, Field


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


class NutriScore(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Product(BaseModel):
    name: str = Field(description="Product name")
    ref: str | None = Field(default=None, description="Product reference ID (e.g., '060489' from Ref.: 060489)")
    price: float = Field(description="Price in EUR")
    price_per_kg: float | None = Field(default=None, description="Price per kilogram in EUR (e.g., 24.97 from '€24,97/kg')")
    category: str = Field(description="Picard category (e.g., 'Plats cuisines')")
    product_type: ProductType = Field(description="General food type")
    url: str = Field(description="Product page URL")
    image_url: str | None = Field(default=None, description="Main product image")

    # Nutrition
    nutriscore: NutriScore | None = Field(default=None, description="NutriScore rating (A, B, C, D, or E)")

    # Dietary flags
    is_vegetarian: bool = Field(default=False, description="Is the product vegetarian")
    is_vegan: bool = Field(default=False, description="Is the product vegan")
    is_gluten_free: bool = Field(default=False, description="Is the product gluten-free")
    is_lactose_free: bool = Field(default=False, description="Is the product lactose-free")

    # For budget planning
    weight_grams: int | None = Field(default=None, description="Net weight in grams")
    servings: int | None = Field(default=None, description="Number of portions")
