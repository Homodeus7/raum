import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from apps.orders.models import Order
from services.payment_service import PaymentService

logger = logging.getLogger(__name__)


@require_http_methods(['GET', 'POST'])
def create_invoice_view(request: HttpRequest, order_id: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('payment'), order_id=order_id)

    if hasattr(order, 'payment'):
        return redirect(order.payment.invoice_url)

    base_url = request.build_absolute_uri('/')[:-1]
    ipn_callback_url = base_url + reverse('payments:webhook')
    success_url = base_url + reverse('payments:success', kwargs={'order_id': order.order_id})
    cancel_url = base_url + reverse('payments:failed', kwargs={'order_id': order.order_id})

    try:
        invoice_created = PaymentService.create_invoice_for_order(
            order=order,
            ipn_callback_url=ipn_callback_url,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return redirect(invoice_created.invoice_url)

    except Exception as e:
        logger.error(f"Failed to create invoice for order {order_id}: {str(e)}", exc_info=True)

        context = {
            'order': order,
            'error': str(e),
        }
        return render(request, 'payments/error.html', context, status=500)


@csrf_exempt
@require_POST
def webhook_view(request: HttpRequest) -> HttpResponse:
    signature = request.headers.get('x-nowpayments-sig', '')

    if not signature:
        logger.warning("Webhook received without signature")
        return JsonResponse({'error': 'No signature provided'}, status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Webhook received with invalid JSON")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        is_valid = PaymentService.verify_webhook_signature(payload, signature)
    except ValueError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return JsonResponse({'error': 'Configuration error'}, status=500)

    if not is_valid:
        logger.warning(f"Invalid webhook signature for payload: {payload}")
        return JsonResponse({'error': 'Invalid signature'}, status=403)

    try:
        payload_dto = PaymentService.parse_webhook_payload(payload)
        payment = PaymentService.process_webhook(payload_dto, payload)

        logger.info(f"Webhook processed successfully for payment {payment.id}, status: {payment.status}")

        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'status': payment.status,
        })

    except Exception as e:
        logger.error(f"Failed to process webhook: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Processing failed'}, status=500)


@require_http_methods(['GET'])
def success_view(request: HttpRequest, order_id: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('payment').prefetch_related('items'), order_id=order_id)

    context = {
        'order': order,
        'payment': getattr(order, 'payment', None),
    }

    return render(request, 'payments/success.html', context)


@require_http_methods(['GET'])
def failed_view(request: HttpRequest, order_id: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('payment'), order_id=order_id)

    context = {
        'order': order,
        'payment': getattr(order, 'payment', None),
    }

    return render(request, 'payments/failed.html', context)
