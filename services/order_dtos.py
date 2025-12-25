from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CustomerInfoDTO:
    email: str
    first_name: str
    last_name: str
    phone: str


@dataclass
class ShippingAddressDTO:
    address_line1: str
    city: str
    postal_code: str
    country: str
    address_line2: Optional[str] = None
    state: Optional[str] = None


@dataclass
class OrderItemDTO:
    product_id: int
    product_name: str
    product_slug: str
    product_price: Decimal
    size: str
    quantity: int
    product_snapshot: dict


@dataclass
class CreateOrderDTO:
    customer_info: CustomerInfoDTO
    shipping_address: ShippingAddressDTO
    items: list[OrderItemDTO]
    shipping_method: str
    shipping_cost: Decimal
    subtotal: Decimal
    total: Decimal
    notes: Optional[str] = None


@dataclass
class OrderCreatedDTO:
    order_id: str
    total: Decimal
    customer_email: str
