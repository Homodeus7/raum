from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from apps.cart.models import Cart
from apps.cart.services import CartService
from apps.orders.models import Order
from apps.catalog.utils import is_htmx
from services.order_service import OrderService


@require_http_methods(['GET'])
def checkout_view(request: HttpRequest) -> HttpResponse:
    cart_service = CartService(request)
    cart_dto = cart_service.get_cart_dto()

    if cart_dto.is_empty:
        if is_htmx(request):
            return HttpResponse('<div class="text-center py-20"><p class="text-neutral-400">Your cart is empty.</p></div>')
        return redirect('catalog:product_list')

    context = {
        'cart': cart_dto,
        'shipping_methods': [
            {'value': 'standard', 'label': 'Standard Shipping', 'cost': Decimal('10.00')},
            {'value': 'express', 'label': 'Express Shipping', 'cost': Decimal('25.00')},
            {'value': 'overnight', 'label': 'Overnight Shipping', 'cost': Decimal('50.00')},
        ],
    }

    if is_htmx(request):
        return render(request, 'orders/partials/checkout_content.html', context)

    return render(request, 'orders/checkout.html', context)


@require_POST
def create_order_view(request: HttpRequest) -> HttpResponse:
    cart_service = CartService(request)
    cart = cart_service.get_cart()

    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    if not cart.items.exists():
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    cart = Cart.objects.prefetch_related('items__product').get(id=cart.id)

    customer_info = {
        'email': request.POST.get('email'),
        'first_name': request.POST.get('first_name'),
        'last_name': request.POST.get('last_name'),
        'phone': request.POST.get('phone'),
    }

    shipping_address = {
        'address_line1': request.POST.get('address_line1'),
        'address_line2': request.POST.get('address_line2', ''),
        'city': request.POST.get('city'),
        'state': request.POST.get('state', ''),
        'postal_code': request.POST.get('postal_code'),
        'country': request.POST.get('country'),
    }

    shipping_method = request.POST.get('shipping_method', 'standard')

    shipping_costs = {
        'standard': Decimal('10.00'),
        'express': Decimal('25.00'),
        'overnight': Decimal('50.00'),
    }
    shipping_cost = shipping_costs.get(shipping_method, Decimal('10.00'))

    notes = request.POST.get('notes', '')

    try:
        order_created = OrderService.create_order_from_cart(
            cart=cart,
            customer_info=customer_info,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            notes=notes,
        )

        payment_create_url = reverse('payments:create_invoice', kwargs={'order_id': order_created.order_id})

        return JsonResponse({
            'success': True,
            'order_id': order_created.order_id,
            'redirect_url': payment_create_url,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def order_detail_view(request: HttpRequest, order_id: str) -> HttpResponse:
    order = get_object_or_404(OrderService.get_order_by_id, order_id=order_id)

    context = {
        'order': order,
    }

    return render(request, 'orders/order_detail.html', context)


@require_http_methods(['GET'])
def awaiting_payment_view(request: HttpRequest, order_id: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('payment').prefetch_related('items'), order_id=order_id)

    context = {
        'order': order,
        'payment': getattr(order, 'payment', None),
    }

    return render(request, 'orders/awaiting_payment.html', context)
