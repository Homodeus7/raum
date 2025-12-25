from django.contrib import admin
from django.utils.html import format_html

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['line_total_display']
    raw_id_fields = ['product']

    def line_total_display(self, obj: CartItem) -> str:
        return f"${obj.line_total:.2f}"
    line_total_display.short_description = 'Line Total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key_short', 'items_count', 'subtotal_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['session_key', 'created_at', 'updated_at']
    inlines = [CartItemInline]

    def session_key_short(self, obj: Cart) -> str:
        if obj.session_key:
            return f"{obj.session_key[:12]}..."
        return "-"
    session_key_short.short_description = 'Session'

    def items_count(self, obj: Cart) -> int:
        return obj.total_items
    items_count.short_description = 'Items'

    def subtotal_display(self, obj: Cart) -> str:
        return f"${obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'size', 'quantity', 'line_total_display']
    list_filter = ['size', 'created_at']
    search_fields = ['product__name', 'cart__user__email']
    raw_id_fields = ['cart', 'product']

    def line_total_display(self, obj: CartItem) -> str:
        return f"${obj.line_total:.2f}"
    line_total_display.short_description = 'Line Total'
