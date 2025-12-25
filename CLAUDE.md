# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

E-commerce platform for eyewear frames built with Django, featuring SPA-like behavior through HTMX instead of traditional frontend frameworks. The project uses server-side rendering with dynamic partial HTML updates for a modern UX without React/Vue.

**Tech Stack:**
- Django 6.0 + HTMX for SPA-like navigation
- PostgreSQL (production) / SQLite3 (development)
- Tailwind CSS + Alpine.js
- NOWPayments API for cryptocurrency payments
- Docker + Nginx for deployment

**Key Dependencies:**
- `django-htmx`: Middleware for HTMX request detection
- `python-decouple`: Environment variable management
- `Pillow`: Image processing for product images
- `psycopg2-binary`: PostgreSQL adapter
- `gunicorn`: WSGI HTTP server for production

## Common Commands

### Development Setup

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run development server
python manage.py runserver
# Access at http://localhost:8000
# Admin panel at http://localhost:8000/admin
```

### Database Operations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Load test data for catalog
python manage.py load_fixtures

# Create sample orders (requires products in DB)
python manage.py create_sample_orders

# Create sample payments (requires orders in DB)
python manage.py create_sample_payments

# Open Django shell for ORM queries
python manage.py shell

# Create a new Django app
python manage.py startapp <app_name>
```

### Production/Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Collect static files (for production)
python manage.py collectstatic --noinput
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.catalog

# Run specific test class
python manage.py test apps.catalog.tests.ProductModelTest
```

## Architecture

### Django MVT Pattern

This project follows Django's MVT (Model-View-Template) architecture:

- **Models** ([apps/catalog/models.py](apps/catalog/models.py)): Database schema using Django ORM
  - `Category`: Product categories with auto-generated slugs
  - `Product`: Eyewear products with detailed specs (dimensions, materials, brand)
  - `ProductImage`: Multiple images per product with main image flag

- **Views** (apps/*/views.py): Request handlers that return HTML (not JSON APIs)
  - Use Django ORM for database queries
  - Return rendered templates or HTML fragments for HTMX

- **Templates** (templates/): Server-rendered HTML with Django template language
  - Use `{% include %}` for reusable components
  - HTMX attributes for dynamic updates without page reloads

### App Structure

Django apps are independent modules in [apps/](apps/):

- **catalog/**: Product catalog
  - Models: Category, Product, ProductImage
  - Admin interface with inline image management
  - Management command: `load_fixtures` for test data

- **cart/**: Session-based shopping cart
  - Models: Cart, CartItem
  - Service layer with DTOs and Repository pattern
  - Context processor for cart data in all templates

- **orders/**: Order management
  - Models: Order, OrderItem
  - Service layer for order creation from cart
  - Management command: `create_sample_orders`

- **payments/**: NOWPayments cryptocurrency integration
  - Models: Payment
  - Service layer for payment creation and webhook handling
  - Management command: `create_sample_payments`

Each app contains:
- `models.py`: Database tables
- `views.py`: Request handlers
- `urls.py`: URL routing for the app
- `admin.py`: Django admin configuration
- `templates/<app_name>/`: App-specific templates

### HTMX Integration

The project uses HTMX for SPA-like behavior:
- Client-side: Add `hx-get`, `hx-post`, `hx-target`, `hx-swap` attributes to HTML
- Server-side: Views return HTML fragments (partials) instead of full pages
- `django-htmx` middleware provides `request.htmx` for detecting HTMX requests
- Use `hx-push-url` to update browser URL without full page reload

### URL Routing

Main router: [config/urls.py](config/urls.py)
- Delegates to app-specific URLs via `include()`
- Currently has placeholder home view and admin

App URLs: apps/<app_name>/urls.py (to be created)
- Define URL patterns with `path()` or `re_path()`
- Use named URLs for reverse lookups: `{% url 'product_detail' slug=product.slug %}`

### Django ORM Best Practices

When writing queries in views:

```python
# Use select_related() for ForeignKey to avoid N+1 queries
products = Product.objects.select_related('category').all()

# Use prefetch_related() for reverse ForeignKey (many-to-many)
categories = Category.objects.prefetch_related('products').all()

# For images with products
products = Product.objects.prefetch_related('images').all()
```

The admin is already optimized (see [apps/catalog/admin.py](apps/catalog/admin.py)).

## Important Implementation Details

### Cart Context Processor

Cart data is available in all templates via context processor ([apps/cart/context_processors.py](apps/cart/context_processors.py)):

```python
# In settings.py, cart_context is registered
# In templates, cart is always available:
{{ cart.total_items }}
{{ cart.subtotal }}
```

### HTMX Request Detection

Views can detect HTMX requests and return partial HTML:

```python
if request.htmx:
    return render(request, 'partials/content.html', context)
return render(request, 'full_page.html', context)
```

The `django-htmx` middleware adds `request.htmx` attribute automatically.

### Session Management

Cart uses Django sessions for anonymous users:

```python
cart_service = CartService(request)
cart_service.get_or_create_cart()
```

Session key is auto-created if it doesn't exist. User carts can be merged with session carts on login.

## Architecture Patterns

This project implements **Clean Architecture** with clear separation of concerns:

### Service Layer Pattern

Business logic is separated into two locations:

**Project-level services** ([services/](services/) at root):
- **Order Service** ([services/order_service.py](services/order_service.py)): Order creation, status updates
- **Payment Service** ([services/payment_service.py](services/payment_service.py)): NOWPayments integration
- DTOs ([services/order_dtos.py](services/order_dtos.py), [services/payment_dtos.py](services/payment_dtos.py)): Data transfer objects
- Use for cross-app business logic and external integrations

**App-level services** (e.g., [apps/cart/services.py](apps/cart/services.py)):
- **Cart Service**: Shopping cart operations
- Use for app-specific business logic
- Can depend on app repositories and DTOs

### Repository Pattern

Some apps (like cart) use the Repository pattern for data access:

- **CartRepository** ([apps/cart/repositories.py](apps/cart/repositories.py)): Database operations for Cart
- **CartItemRepository**: Database operations for CartItem
- Repositories encapsulate all database queries, keeping services clean

### DTO Pattern

Data Transfer Objects ensure type safety and decouple layers:

```python
@dataclass(frozen=True)
class CartItemDTO:
    product_id: int
    product_name: str
    product_price: Decimal
    size: str
    quantity: int
```

See [apps/cart/dto.py](apps/cart/dto.py) for examples.

### Service Usage Pattern

Services should be initialized with request context and handle business logic:

```python
from apps.cart.services import CartService
from apps.cart.dto import AddToCartDTO

def add_to_cart_view(request, product_id):
    cart_service = CartService(request)

    dto = AddToCartDTO(
        product_id=product_id,
        size=request.POST.get('size', 'M'),
        quantity=1
    )

    cart_dto = cart_service.add_item(dto)
    return render(request, 'cart/cart_content.html', {'cart': cart_dto})
```

**Key principles:**
- Services handle business logic and orchestration
- DTOs ensure type safety and validate data
- Repositories handle database operations
- Views only handle HTTP request/response

## Code Quality Standards

From [tech.md](tech.md):

- **No comments in code**: Code should be self-documenting
- **Type hints required**: Use Python type hints throughout
- **Clean architecture**: Separate concerns between layers
  - Models: Data structure only
  - Services: Business logic (in services/ or app services.py)
  - Repositories: Data access patterns (where applicable)
  - Views: Request/response handling only
- **DRY principle**: Avoid code duplication
- **No over-engineering**: Keep solutions minimal and focused

## Database Configuration

- **Development**: SQLite3 (current, see [config/settings.py](config/settings.py:77-82))
- **Production**: PostgreSQL via Docker Compose
- Switch by uncommenting PostgreSQL config in settings.py and setting env vars

PostgreSQL config uses environment variables from .env:
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

## Static Files & Media

- **Static files** (CSS/JS): [static/](static/) directory
  - `STATIC_URL = '/static/'`
  - `STATIC_ROOT = 'staticfiles/'` (for `collectstatic`)

- **Media files** (user uploads): [media/](media/) directory
  - `MEDIA_URL = '/media/'`
  - Product images uploaded to `media/products/`

## Environment Variables

Copy [.env.example](.env.example) to `.env` and configure:

- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: True for development, False for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `DB_*`: Database credentials (for PostgreSQL)
- `NOWPAYMENTS_API_KEY`: NOWPayments API credentials (for payment integration)

## Admin Interface

Fully configured Django admin at `/admin/`:
- Category management with product count
- Product management with:
  - Inline image uploads with previews
  - Collapsible fieldsets for dimensions and manufacturing
  - Filtering by category, brand, material, shape
  - Search by name, brand, description, color
- Optimized queries using `select_related()` and `prefetch_related()`

## Project Status

The core e-commerce functionality is implemented:

**Completed:**
- Product catalog with categories and images
- Session-based shopping cart with Service/Repository pattern
- Order management with order creation from cart
- Payment integration with NOWPayments API
- Admin interface for all models
- Management commands for test data generation
- HTMX-powered dynamic UI updates

**Architecture implemented:**
- Clean Architecture with Service Layer
- Repository Pattern for data access
- DTO Pattern for type-safe data transfer
- Context processors for global template data

See [git status](#) for current working changes and [BACKEND_GUIDE.local.md](BACKEND_GUIDE.local.md) for detailed technical documentation.

## Docker Stack

[docker-compose.yml](docker-compose.yml) defines:
- **web**: Django app with Gunicorn
- **db**: PostgreSQL 15
- **redis**: Redis 7 for caching/queues
- **celery**: Background task processing
- **nginx**: Reverse proxy and static file serving

All services communicate via `internal_network`.
