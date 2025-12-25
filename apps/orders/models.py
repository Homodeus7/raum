from decimal import Decimal
from django.db import models
from django.core.validators import EmailValidator


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_AWAITING_PAYMENT = 'awaiting_payment'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),
        (STATUS_PAID, 'Paid'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    SHIPPING_STANDARD = 'standard'
    SHIPPING_EXPRESS = 'express'
    SHIPPING_OVERNIGHT = 'overnight'

    SHIPPING_CHOICES = [
        (SHIPPING_STANDARD, 'Standard Shipping'),
        (SHIPPING_EXPRESS, 'Express Shipping'),
        (SHIPPING_OVERNIGHT, 'Overnight Shipping'),
    ]

    order_id = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    customer_email = models.EmailField(validators=[EmailValidator()])
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)

    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)

    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default=SHIPPING_STANDARD)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['status']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self) -> str:
        return f"Order {self.order_id} - {self.get_status_display()}"

    @property
    def customer_full_name(self) -> str:
        return f"{self.customer_first_name} {self.customer_last_name}"

    @property
    def full_shipping_address(self) -> str:
        parts = [
            self.shipping_address_line1,
            self.shipping_address_line2,
            self.shipping_city,
            self.shipping_state,
            self.shipping_postal_code,
            self.shipping_country,
        ]
        return ', '.join(filter(None, parts))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    product_slug = models.SlugField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)

    size = models.CharField(max_length=5)
    quantity = models.PositiveIntegerField(default=1)

    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    product_snapshot = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['order', 'product_slug']),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_name} ({self.size}) - Order {self.order.order_id}"

    def save(self, *args, **kwargs):
        if not self.line_total:
            self.line_total = self.product_price * self.quantity
        super().save(*args, **kwargs)
