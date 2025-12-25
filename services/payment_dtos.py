from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CreateInvoiceDTO:
    order_id: str
    price_amount: Decimal
    price_currency: str
    ipn_callback_url: str
    success_url: str
    cancel_url: str
    order_description: Optional[str] = None
    pay_currency: Optional[str] = None


@dataclass
class InvoiceCreatedDTO:
    invoice_id: str
    invoice_url: str
    order_id: str
    price_amount: Decimal
    price_currency: str
    pay_currency: Optional[str]


@dataclass
class WebhookPayloadDTO:
    payment_id: str
    invoice_id: str
    payment_status: str
    pay_amount: Decimal
    pay_currency: str
    actually_paid: Decimal
    price_amount: Decimal
    price_currency: str
    order_id: str
