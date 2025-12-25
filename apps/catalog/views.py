from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.core.paginator import Paginator
from decimal import Decimal

from .models import Product, Category
from .utils import is_htmx
from apps.cart.services import CartService


AVAILABLE_SIZES = ['XS', 'S', 'M', 'L', 'XL']


def product_list(request: HttpRequest) -> HttpResponse:
    products = Product.objects.select_related('category').prefetch_related('images').all()
    categories = Category.objects.all()

    selected_category = None
    category_slug = request.GET.get('category')
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    brands = request.GET.getlist('brand')
    if brands:
        products = products.filter(brand__in=brands)

    materials = request.GET.getlist('material')
    if materials:
        products = products.filter(material__in=materials)

    shapes = request.GET.getlist('shape')
    if shapes:
        products = products.filter(shape__in=shapes)

    colors = request.GET.getlist('color')
    if colors:
        products = products.filter(color__in=colors)

    price_min = request.GET.get('price_min')
    if price_min:
        products = products.filter(price__gte=Decimal(price_min))

    price_max = request.GET.get('price_max')
    if price_max:
        products = products.filter(price__lte=Decimal(price_max))

    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    elif sort_option == 'newest':
        products = products.order_by('-created_at')

    all_products = Product.objects.all()
    if selected_category:
        all_products = all_products.filter(category=selected_category)

    filter_options = {
        'brands': sorted([b for b in all_products.values_list('brand', flat=True).distinct() if b]),
        'materials': sorted([m for m in all_products.values_list('material', flat=True).distinct() if m]),
        'shapes': sorted([s for s in all_products.values_list('shape', flat=True).distinct() if s]),
        'colors': sorted([c for c in all_products.values_list('color', flat=True).distinct() if c]),
    }

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    for product in page_obj:
        product.main_image = product.images.filter(is_main=True).first() or product.images.first()

    cart_service = CartService(request)

    context = {
        'products': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'filter_options': filter_options,
        'cart_count': cart_service.get_cart_count(),
    }

    if is_htmx(request):
        hx_target = request.headers.get('HX-Target', '')
        if hx_target == 'product-grid':
            return render(request, 'catalog/partials/product_grid.html', context)
        return render(request, 'catalog/partials/product_list_content.html', context)

    return render(request, 'catalog/product_list.html', context)


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug
    )

    related_products = Product.objects.filter(
        category=product.category
    ).exclude(
        id=product.id
    ).select_related('category').prefetch_related('images')[:4]

    for related_product in related_products:
        related_product.main_image = related_product.images.filter(is_main=True).first() or related_product.images.first()

    cart_service = CartService(request)

    context = {
        'product': product,
        'available_sizes': AVAILABLE_SIZES,
        'related_products': related_products,
        'cart_count': cart_service.get_cart_count(),
    }

    if is_htmx(request):
        return render(request, 'catalog/partials/product_detail_content.html', context)

    return render(request, 'catalog/product_detail.html', context)


def search_products(request: HttpRequest) -> HttpResponse:
    query = request.GET.get('q', '').strip()

    products = []
    if query:
        products = Product.objects.select_related('category').prefetch_related('images').filter(
            name__icontains=query
        ) | Product.objects.select_related('category').prefetch_related('images').filter(
            brand__icontains=query
        ) | Product.objects.select_related('category').prefetch_related('images').filter(
            description__icontains=query
        )
        products = products.distinct()[:12]

        for product in products:
            product.main_image = product.images.filter(is_main=True).first() or product.images.first()

    context = {
        'products': products,
        'query': query,
    }

    return render(request, 'catalog/partials/search_results.html', context)
