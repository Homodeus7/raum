from decimal import Decimal
from django.db import models
from django.conf import settings


class Cart(models.Model):
    session_key = models.CharField(max_length=40, db_index=True, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user']),
        ]

    def __str__(self) -> str:
        if self.user:
            return f"Cart #{self.id} for {self.user}"
        return f"Cart #{self.id} (session: {self.session_key[:8]}...)"

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self) -> Decimal:
        return sum(item.line_total for item in self.items.all())


class CartItem(models.Model):
    SIZES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    size = models.CharField(max_length=5, choices=SIZES, default='M')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'size']
        indexes = [
            models.Index(fields=['cart', 'product', 'size']),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product.name} ({self.size})"

    @property
    def line_total(self) -> Decimal:
        return self.product.price * self.quantity
