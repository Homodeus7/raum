from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_slug', 'product_price', 'size', 'quantity', 'line_total']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


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
    ]
    inlines = [OrderItemInline]

    fieldsets = [
        ('Order Information', {
            'fields': ['order_id', 'status', 'created_at', 'updated_at'],
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
