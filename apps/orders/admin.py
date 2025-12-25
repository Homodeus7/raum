from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem
from apps.payments.models import Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product_name', 'product_slug', 'product_price', 'size', 'quantity', 'line_total']
    readonly_fields = ['line_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id',
        'customer_full_name',
        'customer_email',
        'status_badge',
        'total',
        'created_at',
    ]
    list_filter = ['status', 'shipping_method', 'created_at']
    search_fields = ['order_id', 'customer_email', 'customer_first_name', 'customer_last_name']
    readonly_fields = [
        'order_id',
        'created_at',
        'updated_at',
        'customer_full_name',
        'full_shipping_address',
        'payment_info',
    ]
    inlines = [OrderItemInline]

    fieldsets = [
        ('Order Information', {
            'fields': ['order_id', 'status', 'created_at', 'updated_at', 'payment_info'],
        }),
        ('Customer Information', {
            'fields': [
                'customer_email',
                'customer_first_name',
                'customer_last_name',
                'customer_phone',
                'customer_full_name',
            ],
        }),
        ('Shipping Information', {
            'fields': [
                'shipping_address_line1',
                'shipping_address_line2',
                'shipping_city',
                'shipping_state',
                'shipping_postal_code',
                'shipping_country',
                'full_shipping_address',
                'shipping_method',
                'shipping_cost',
            ],
        }),
        ('Order Totals', {
            'fields': ['subtotal', 'total'],
        }),
        ('Additional Information', {
            'fields': ['notes'],
            'classes': ['collapse'],
        }),
    ]

    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'processing': '#0dcaf0',
            'awaiting_payment': '#ffc107',
            'paid': '#198754',
            'shipped': '#0d6efd',
            'delivered': '#20c997',
            'cancelled': '#dc3545',
            'refunded': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_info(self, obj):
        from django.urls import reverse
        try:
            payment = obj.payment
            url = reverse('admin:payments_payment_change', args=[payment.id])

            status_colors = {
                'waiting': '#6c757d',
                'confirming': '#0dcaf0',
                'confirmed': '#198754',
                'sending': '#0d6efd',
                'partially_paid': '#ffc107',
                'finished': '#20c997',
                'failed': '#dc3545',
                'refunded': '#fd7e14',
                'expired': '#6c757d',
            }
            color = status_colors.get(payment.status, '#6c757d')

            return format_html(
                '<div style="margin-bottom: 10px;">'
                '<strong>Payment ID:</strong> <a href="{}" target="_blank">{}</a><br>'
                '<strong>Invoice ID:</strong> {}<br>'
                '<strong>Status:</strong> <span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span><br>'
                '<strong>Amount:</strong> {} {}<br>'
                '<strong>Pay Currency:</strong> {}'
                '</div>',
                url,
                payment.nowpayments_payment_id or 'N/A',
                payment.nowpayments_invoice_id,
                color,
                payment.get_status_display(),
                payment.price_amount,
                payment.price_currency.upper(),
                payment.pay_currency.upper() if payment.pay_currency else 'N/A'
            )
        except Payment.DoesNotExist:
            return format_html('<em style="color: #999;">No payment associated</em>')
    payment_info.short_description = 'Payment Information'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment').prefetch_related('items')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product_name', 'size', 'quantity', 'line_total']
    list_filter = ['size', 'created_at']
    search_fields = ['product_name', 'order__order_id']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')
