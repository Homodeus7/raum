from decimal import Decimal
from django.db import models


class Payment(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_CONFIRMING = 'confirming'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SENDING = 'sending'
    STATUS_PARTIALLY_PAID = 'partially_paid'
    STATUS_FINISHED = 'finished'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_WAITING, 'Waiting'),
        (STATUS_CONFIRMING, 'Confirming'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SENDING, 'Sending'),
        (STATUS_PARTIALLY_PAID, 'Partially Paid'),
        (STATUS_FINISHED, 'Finished'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment'
    )

    nowpayments_invoice_id = models.CharField(max_length=100, unique=True, db_index=True)
    nowpayments_payment_id = models.CharField(max_length=100, blank=True, db_index=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING, db_index=True)

    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    price_currency = models.CharField(max_length=10, default='usd')

    pay_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pay_currency = models.CharField(max_length=10, blank=True)

    actually_paid = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    invoice_url = models.URLField(max_length=500)

    webhook_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nowpayments_invoice_id']),
            models.Index(fields=['nowpayments_payment_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self) -> str:
        return f"Payment for Order {self.order.order_id} - {self.get_status_display()}"

    @property
    def is_successful(self) -> bool:
        return self.status in [self.STATUS_FINISHED, self.STATUS_CONFIRMED]

    @property
    def is_pending(self) -> bool:
        return self.status in [self.STATUS_WAITING, self.STATUS_CONFIRMING, self.STATUS_SENDING]

    @property
    def is_failed(self) -> bool:
        return self.status in [self.STATUS_FAILED, self.STATUS_EXPIRED, self.STATUS_REFUNDED]
