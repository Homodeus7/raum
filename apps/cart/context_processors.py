from django.http import HttpRequest

from .services import CartService


def cart_context(request: HttpRequest) -> dict:
    service = CartService(request)
    return {
        'cart_count': service.get_cart_count(),
    }
