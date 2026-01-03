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


class Product(BaseModel):
    name: str = Field(description="Product name")
    price: float = Field(description="Price in EUR")
    category: str = Field(description="Picard category (e.g., 'Plats cuisines')")
    product_type: ProductType = Field(description="General food type")
    url: str = Field(description="Product page URL")
    image_url: str | None = Field(default=None, description="Main product image")

    # Dietary flags
    is_vegetarian: bool = Field(default=False, description="Is the product vegetarian")
    is_vegan: bool = Field(default=False, description="Is the product vegan")
    is_gluten_free: bool = Field(default=False, description="Is the product gluten-free")
    is_lactose_free: bool = Field(default=False, description="Is the product lactose-free")

    # For budget planning
    weight_grams: int | None = Field(default=None, description="Net weight in grams")
    servings: int | None = Field(default=None, description="Number of portions")
