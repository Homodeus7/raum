from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj: ProductImage) -> str:
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj: Category) -> int:
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'brand',
        'category',
        'price',
        'material',
        'color',
        'created_at'
    ]
    list_filter = [
        'category',
        'brand',
        'material',
        'shape',
        'created_at'
    ]
    search_fields = ['name', 'brand', 'description', 'color']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    list_per_page = 25

    fieldsets = [
        ('Basic Information', {
            'fields': ['category', 'name', 'slug', 'description', 'price']
        }),
        ('Product Details', {
            'fields': [
                'brand',
                'material',
                'shape',
                'color',
                'collection',
                'lens_type',
                'lens_features'
            ]
        }),
        ('Manufacturing', {
            'fields': ['manufacturer', 'country_of_origin'],
            'classes': ['collapse']
        }),
        ('Dimensions (mm)', {
            'fields': [
                'lens_width_mm',
                'bridge_width_mm',
                'frame_width_mm',
                'temple_length_mm',
                'lens_height_mm'
            ],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('images')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'is_main', 'created_at']
    list_filter = ['is_main', 'created_at']
    search_fields = ['product__name']
    readonly_fields = ['image_preview', 'created_at']
    list_editable = ['is_main']

    def image_preview(self, obj: ProductImage) -> str:
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('product')
