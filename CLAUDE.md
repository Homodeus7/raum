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

- **catalog/**: Product catalog (implemented)
  - Categories, products, product images
  - Admin interface configured with inline image management

- **cart/**: Shopping cart (planned)
- **orders/**: Order management (planned)
- **payments/**: NOWPayments integration (planned)

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

The admin is already optimized (see [apps/catalog/admin.py](apps/catalog/admin.py:95-97)).

## Code Quality Standards

From [tech.md](tech.md):

- **No comments in code**: Code should be self-documenting
- **Type hints required**: Use Python type hints throughout
- **Clean architecture**: Separate concerns between layers
  - Models: Data structure only
  - Services layer: Business logic (to be created in services/)
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

## Project Roadmap

Current status: Models and admin completed for catalog app.

Next steps from [BACKEND_GUIDE.md](BACKEND_GUIDE.md):
1. Create views and URL routing for catalog
2. Build templates with HTMX for SPA navigation
3. Implement cart functionality (session-based, no registration required)
4. Create order management system
5. Integrate NOWPayments for cryptocurrency payments

## Docker Stack

[docker-compose.yml](docker-compose.yml) defines:
- **web**: Django app with Gunicorn
- **db**: PostgreSQL 15
- **redis**: Redis 7 for caching/queues
- **celery**: Background task processing
- **nginx**: Reverse proxy and static file serving

All services communicate via `internal_network`.
