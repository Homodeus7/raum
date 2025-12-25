from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from apps.catalog.models import Product


@dataclass(frozen=True)
class CartItemDTO:
    product_id: int
    product_name: str
    product_slug: str
    product_price: Decimal
    product_brand: str
    product_image_url: Optional[str]
    size: str
    quantity: int

    @property
    def line_total(self) -> Decimal:
        return self.product_price * self.quantity

    @classmethod
    def from_cart_item(cls, cart_item) -> 'CartItemDTO':
        main_image = cart_item.product.images.filter(is_main=True).first()
        if not main_image:
            main_image = cart_item.product.images.first()

        return cls(
            product_id=cart_item.product.id,
            product_name=cart_item.product.name,
            product_slug=cart_item.product.slug,
            product_price=cart_item.product.price,
            product_brand=cart_item.product.brand,
            product_image_url=main_image.image.url if main_image else None,
            size=cart_item.size,
            quantity=cart_item.quantity,
        )


@dataclass(frozen=True)
class CartDTO:
    items: list[CartItemDTO]

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self) -> Decimal:
        return sum(item.line_total for item in self.items)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    @classmethod
    def from_cart(cls, cart) -> 'CartDTO':
        items = [CartItemDTO.from_cart_item(item) for item in cart.items.all()]
        return cls(items=items)

    @classmethod
    def empty(cls) -> 'CartDTO':
        return cls(items=[])


@dataclass(frozen=True)
class AddToCartDTO:
    product_id: int
    size: str
    quantity: int = 1


@dataclass(frozen=True)
class UpdateCartItemDTO:
    product_id: int
    size: str
    quantity: int


@dataclass(frozen=True)
class RemoveFromCartDTO:
    product_id: int
    size: str
