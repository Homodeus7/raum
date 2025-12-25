from typing import Optional
from django.db import transaction
from django.contrib.auth.models import AbstractUser

from .models import Cart, CartItem
from apps.catalog.models import Product


class CartRepository:
    @staticmethod
    def get_or_create_cart(
        session_key: Optional[str] = None,
        user: Optional[AbstractUser] = None
    ) -> Cart:
        if user and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            return cart

        if session_key:
            cart, _ = Cart.objects.get_or_create(session_key=session_key)
            return cart

        raise ValueError("Either session_key or authenticated user is required")

    @staticmethod
    def get_cart(
        session_key: Optional[str] = None,
        user: Optional[AbstractUser] = None
    ) -> Optional[Cart]:
        if user and user.is_authenticated:
            return Cart.objects.filter(user=user).first()

        if session_key:
            return Cart.objects.filter(session_key=session_key).first()

        return None

    @staticmethod
    def get_cart_with_items(
        session_key: Optional[str] = None,
        user: Optional[AbstractUser] = None
    ) -> Optional[Cart]:
        if user and user.is_authenticated:
            return (
                Cart.objects
                .filter(user=user)
                .prefetch_related('items__product__images')
                .first()
            )

        if session_key:
            return (
                Cart.objects
                .filter(session_key=session_key)
                .prefetch_related('items__product__images')
                .first()
            )

        return None

    @staticmethod
    def delete_cart(cart: Cart) -> None:
        cart.delete()

    @staticmethod
    def merge_carts(session_cart: Cart, user_cart: Cart) -> Cart:
        with transaction.atomic():
            for item in session_cart.items.all():
                existing_item = user_cart.items.filter(
                    product=item.product,
                    size=item.size
                ).first()

                if existing_item:
                    existing_item.quantity += item.quantity
                    existing_item.save()
                else:
                    item.cart = user_cart
                    item.save()

            session_cart.delete()

        return user_cart


class CartItemRepository:
    @staticmethod
    def get_item(cart: Cart, product: Product, size: str) -> Optional[CartItem]:
        return cart.items.filter(product=product, size=size).first()

    @staticmethod
    def add_item(cart: Cart, product: Product, size: str, quantity: int = 1) -> CartItem:
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={'quantity': quantity}
        )

        if not created:
            item.quantity += quantity
            item.save()

        return item

    @staticmethod
    def update_item_quantity(item: CartItem, quantity: int) -> CartItem:
        item.quantity = max(1, quantity)
        item.save()
        return item

    @staticmethod
    def increment_item_quantity(item: CartItem, delta: int = 1) -> CartItem:
        item.quantity = max(1, item.quantity + delta)
        item.save()
        return item

    @staticmethod
    def remove_item(item: CartItem) -> None:
        item.delete()

    @staticmethod
    def clear_cart(cart: Cart) -> None:
        cart.items.all().delete()
