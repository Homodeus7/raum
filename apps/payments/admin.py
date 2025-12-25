from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order_link',
        'status_badge',
        'price_amount',
        'price_currency',
        'pay_currency',
        'created_at',
    ]
    list_filter = ['status', 'price_currency', 'pay_currency', 'created_at']
    search_fields = ['nowpayments_invoice_id', 'nowpayments_payment_id', 'order__order_id']
    readonly_fields = [
        'order',
        'nowpayments_invoice_id',
        'nowpayments_payment_id',
        'price_amount',
        'price_currency',
        'pay_amount',
        'pay_currency',
        'actually_paid',
        'invoice_url_link',
        'webhook_data',
        'created_at',
        'updated_at',
    ]

    fieldsets = [
        ('Payment Information', {
            'fields': ['order', 'status', 'created_at', 'updated_at'],
        }),
        ('NOWPayments Details', {
            'fields': [
                'nowpayments_invoice_id',
                'nowpayments_payment_id',
                'invoice_url_link',
            ],
        }),
        ('Amounts', {
            'fields': [
                'price_amount',
                'price_currency',
                'pay_amount',
                'pay_currency',
                'actually_paid',
            ],
        }),
        ('Webhook Data', {
            'fields': ['webhook_data'],
            'classes': ['collapse'],
        }),
    ]

    def status_badge(self, obj):
        colors = {
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
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_id)
    order_link.short_description = 'Order'

    def invoice_url_link(self, obj):
        if obj.invoice_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.invoice_url, obj.invoice_url)
        return '-'
    invoice_url_link.short_description = 'Invoice URL'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
