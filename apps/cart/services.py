from typing import Optional
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem
from .dto import CartDTO, CartItemDTO, AddToCartDTO, UpdateCartItemDTO, RemoveFromCartDTO
from .repositories import CartRepository, CartItemRepository
from apps.catalog.models import Product


class CartService:
    def __init__(self, request: HttpRequest):
        self._request = request
        self._cart_repo = CartRepository()
        self._item_repo = CartItemRepository()

    def _get_session_key(self) -> str:
        if not self._request.session.session_key:
            self._request.session.create()
        return self._request.session.session_key

    def _get_user(self):
        if self._request.user.is_authenticated:
            return self._request.user
        return None

    def get_cart(self) -> Optional[Cart]:
        return self._cart_repo.get_cart_with_items(
            session_key=self._get_session_key(),
            user=self._get_user()
        )

    def get_or_create_cart(self) -> Cart:
        return self._cart_repo.get_or_create_cart(
            session_key=self._get_session_key(),
            user=self._get_user()
        )

    def get_cart_dto(self) -> CartDTO:
        cart = self.get_cart()
        if not cart:
            return CartDTO.empty()
        return CartDTO.from_cart(cart)

    def get_cart_count(self) -> int:
        cart = self.get_cart()
        if not cart:
            return 0
        return cart.total_items

    def add_item(self, dto: AddToCartDTO) -> CartDTO:
        product = get_object_or_404(Product, id=dto.product_id)
        cart = self.get_or_create_cart()

        self._item_repo.add_item(
            cart=cart,
            product=product,
            size=dto.size,
            quantity=dto.quantity
        )

        cart.refresh_from_db()
        return self.get_cart_dto()

    def update_item_quantity(self, dto: UpdateCartItemDTO) -> CartDTO:
        cart = self.get_cart()
        if not cart:
            return CartDTO.empty()

        product = get_object_or_404(Product, id=dto.product_id)
        item = self._item_repo.get_item(cart, product, dto.size)

        if item:
            if dto.quantity <= 0:
                self._item_repo.remove_item(item)
            else:
                self._item_repo.update_item_quantity(item, dto.quantity)

        return self.get_cart_dto()

    def increment_item(self, product_id: int, size: str, delta: int) -> CartDTO:
        cart = self.get_cart()
        if not cart:
            return CartDTO.empty()

        product = get_object_or_404(Product, id=product_id)
        item = self._item_repo.get_item(cart, product, size)

        if item:
            self._item_repo.increment_item_quantity(item, delta)

        return self.get_cart_dto()

    def remove_item(self, dto: RemoveFromCartDTO) -> CartDTO:
        cart = self.get_cart()
        if not cart:
            return CartDTO.empty()

        product = get_object_or_404(Product, id=dto.product_id)
        item = self._item_repo.get_item(cart, product, dto.size)

        if item:
            self._item_repo.remove_item(item)

        return self.get_cart_dto()

    def clear_cart(self) -> CartDTO:
        cart = self.get_cart()
        if cart:
            self._item_repo.clear_cart(cart)
        return CartDTO.empty()

    def merge_session_cart_to_user(self) -> None:
        if not self._request.user.is_authenticated:
            return

        session_key = self._get_session_key()
        session_cart = self._cart_repo.get_cart(session_key=session_key)

        if not session_cart:
            return

        user_cart = self._cart_repo.get_or_create_cart(user=self._request.user)
        self._cart_repo.merge_carts(session_cart, user_cart)
