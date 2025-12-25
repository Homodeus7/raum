from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from .services import CartService
from .dto import AddToCartDTO, UpdateCartItemDTO, RemoveFromCartDTO


@require_GET
def cart_modal(request: HttpRequest) -> HttpResponse:
    service = CartService(request)
    cart_dto = service.get_cart_dto()

    return render(request, 'cart/cart_modal_content.html', {
        'cart': cart_dto,
    })


@require_POST
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    size = request.POST.get('size')
    if not size:
        return HttpResponse('Size is required', status=400)

    quantity = int(request.POST.get('quantity', 1))

    service = CartService(request)
    dto = AddToCartDTO(product_id=product_id, size=size, quantity=quantity)
    cart_dto = service.add_item(dto)

    response = HttpResponse('')
    response['HX-Trigger'] = f'{{"cartUpdated": {{"count": {cart_dto.total_items}}}}}'
    return response


@require_POST
def update_cart_item(request: HttpRequest, product_id: int) -> HttpResponse:
    size = request.POST.get('size')
    if not size:
        return HttpResponse('Size is required', status=400)

    delta = int(request.POST.get('delta', 0))
    quantity = request.POST.get('quantity')

    service = CartService(request)

    if quantity is not None:
        dto = UpdateCartItemDTO(product_id=product_id, size=size, quantity=int(quantity))
        cart_dto = service.update_item_quantity(dto)
    else:
        cart_dto = service.increment_item(product_id, size, delta)

    response = HttpResponse('')
    response['HX-Trigger'] = f'{{"cartUpdated": {{"count": {cart_dto.total_items}}}}}'
    return response


@require_POST
def remove_from_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    size = request.POST.get('size')
    if not size:
        return HttpResponse('Size is required', status=400)

    service = CartService(request)
    dto = RemoveFromCartDTO(product_id=product_id, size=size)
    cart_dto = service.remove_item(dto)

    response = HttpResponse('')
    response['HX-Trigger'] = f'{{"cartUpdated": {{"count": {cart_dto.total_items}}}}}'
    return response


@require_POST
def clear_cart(request: HttpRequest) -> HttpResponse:
    service = CartService(request)
    cart_dto = service.clear_cart()

    response = HttpResponse('')
    response['HX-Trigger'] = '{"cartUpdated": {"count": 0}}'
    return response


def get_cart_count(request: HttpRequest) -> HttpResponse:
    service = CartService(request)
    count = service.get_cart_count()
    return HttpResponse(str(count))
