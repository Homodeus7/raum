from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from apps.cart.models import Cart
from services.order_service import OrderService


@require_http_methods(['GET'])
def checkout_view(request: HttpRequest) -> HttpResponse:
    session_key = request.session.session_key
    if not session_key:
        return redirect('cart:view')

    try:
        cart = Cart.objects.prefetch_related('items__product').get(session_key=session_key)
    except Cart.DoesNotExist:
        return redirect('cart:view')

    if not cart.items.exists():
        return redirect('cart:view')

    context = {
        'cart': cart,
        'shipping_methods': [
            {'value': 'standard', 'label': 'Standard Shipping', 'cost': Decimal('10.00')},
            {'value': 'express', 'label': 'Express Shipping', 'cost': Decimal('25.00')},
            {'value': 'overnight', 'label': 'Overnight Shipping', 'cost': Decimal('50.00')},
        ],
    }

    return render(request, 'orders/checkout.html', context)


@require_POST
def create_order_view(request: HttpRequest) -> HttpResponse:
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No cart found'}, status=400)

    try:
        cart = Cart.objects.prefetch_related('items__product').get(session_key=session_key)
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    if not cart.items.exists():
        return JsonResponse({'error': 'Cart is empty'}, status=400)

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
