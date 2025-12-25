import hmac
import hashlib
import json
import requests
from decimal import Decimal
from typing import Optional
from django.conf import settings
from django.db import transaction

from apps.payments.models import Payment
from apps.orders.models import Order
from .payment_dtos import CreateInvoiceDTO, InvoiceCreatedDTO, WebhookPayloadDTO


class NOWPaymentsClient:
    BASE_URL = 'https://api.nowpayments.io/v1'

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
        }

    def create_invoice(self, dto: CreateInvoiceDTO) -> dict:
        url = f'{self.BASE_URL}/invoice'

        payload = {
            'price_amount': float(dto.price_amount),
            'price_currency': dto.price_currency,
            'order_id': dto.order_id,
            'ipn_callback_url': dto.ipn_callback_url,
            'success_url': dto.success_url,
            'cancel_url': dto.cancel_url,
        }

        if dto.order_description:
            payload['order_description'] = dto.order_description

        if dto.pay_currency:
            payload['pay_currency'] = dto.pay_currency

        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()

        return response.json()


class WebhookValidator:
    @staticmethod
    def sort_dict(data: dict) -> dict:
        return {k: WebhookValidator.sort_dict(v) if isinstance(v, dict) else v
                for k, v in sorted(data.items())}

    @staticmethod
    def verify_signature(payload: dict, signature: str, secret_key: str) -> bool:
        sorted_payload = WebhookValidator.sort_dict(payload)
        json_string = json.dumps(sorted_payload, separators=(',', ':'))

        calculated_signature = hmac.new(
            secret_key.encode(),
            json_string.encode(),
            hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(calculated_signature, signature)


class PaymentService:
    @staticmethod
    def get_nowpayments_client() -> NOWPaymentsClient:
        api_key = getattr(settings, 'NOWPAYMENTS_API_KEY', '')
        if not api_key:
            raise ValueError('NOWPAYMENTS_API_KEY is not configured')
        return NOWPaymentsClient(api_key)

    @staticmethod
    @transaction.atomic
    def create_invoice_for_order(order: Order, ipn_callback_url: str, success_url: str, cancel_url: str) -> InvoiceCreatedDTO:
        client = PaymentService.get_nowpayments_client()

        dto = CreateInvoiceDTO(
            order_id=order.order_id,
            price_amount=order.total,
            price_currency='usd',
            ipn_callback_url=ipn_callback_url,
            success_url=success_url,
            cancel_url=cancel_url,
            order_description=f"Order {order.order_id}",
        )

        response = client.create_invoice(dto)

        payment = Payment.objects.create(
            order=order,
            nowpayments_invoice_id=response['id'],
            status=Payment.STATUS_WAITING,
            price_amount=Decimal(str(response['price_amount'])),
            price_currency=response['price_currency'],
            pay_currency=response.get('pay_currency') or '',
            invoice_url=response['invoice_url'],
        )

        order.status = Order.STATUS_AWAITING_PAYMENT
        order.save(update_fields=['status', 'updated_at'])

        return InvoiceCreatedDTO(
            invoice_id=payment.nowpayments_invoice_id,
            invoice_url=payment.invoice_url,
            order_id=order.order_id,
            price_amount=payment.price_amount,
            price_currency=payment.price_currency,
            pay_currency=payment.pay_currency or None,
        )

    @staticmethod
    def verify_webhook_signature(payload: dict, signature: str) -> bool:
        secret_key = getattr(settings, 'NOWPAYMENTS_IPN_SECRET', '')
        if not secret_key:
            raise ValueError('NOWPAYMENTS_IPN_SECRET is not configured')
        return WebhookValidator.verify_signature(payload, signature, secret_key)

    @staticmethod
    def parse_webhook_payload(data: dict) -> WebhookPayloadDTO:
        return WebhookPayloadDTO(
            payment_id=str(data.get('payment_id', '')),
            invoice_id=str(data.get('invoice_id', '')),
            payment_status=data.get('payment_status', ''),
            pay_amount=Decimal(str(data.get('pay_amount', '0'))),
            pay_currency=data.get('pay_currency', ''),
            actually_paid=Decimal(str(data.get('actually_paid', '0'))),
            price_amount=Decimal(str(data.get('price_amount', '0'))),
            price_currency=data.get('price_currency', ''),
            order_id=data.get('order_id', ''),
        )

    @staticmethod
    @transaction.atomic
    def process_webhook(payload_dto: WebhookPayloadDTO, raw_payload: dict) -> Payment:
        payment = Payment.objects.select_related('order').get(
            nowpayments_invoice_id=payload_dto.invoice_id
        )

        payment.nowpayments_payment_id = payload_dto.payment_id
        payment.pay_amount = payload_dto.pay_amount
        payment.pay_currency = payload_dto.pay_currency
        payment.actually_paid = payload_dto.actually_paid
        payment.webhook_data = raw_payload

        status_mapping = {
            'waiting': Payment.STATUS_WAITING,
            'confirming': Payment.STATUS_CONFIRMING,
            'confirmed': Payment.STATUS_CONFIRMED,
            'sending': Payment.STATUS_SENDING,
            'partially_paid': Payment.STATUS_PARTIALLY_PAID,
            'finished': Payment.STATUS_FINISHED,
            'failed': Payment.STATUS_FAILED,
            'refunded': Payment.STATUS_REFUNDED,
            'expired': Payment.STATUS_EXPIRED,
        }

        payment.status = status_mapping.get(payload_dto.payment_status.lower(), Payment.STATUS_WAITING)
        payment.save()

        if payment.is_successful:
            from .order_service import OrderService
            OrderService.mark_order_as_paid(payment.order.order_id)

        return payment

    @staticmethod
    def get_payment_by_invoice_id(invoice_id: str) -> Optional[Payment]:
        try:
            return Payment.objects.select_related('order').get(nowpayments_invoice_id=invoice_id)
        except Payment.DoesNotExist:
            return None
