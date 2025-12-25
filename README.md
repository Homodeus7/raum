# Raum

E-commerce platform for stylish eyewear frames.

## Tech Stack

- **Backend:** Django 6.0 + HTMX
- **Database:** PostgreSQL (prod) / SQLite3 (dev)
- **Frontend:** Tailwind CSS + Alpine.js
- **Payments:** NOWPayments (crypto)
- **Deploy:** Docker + Nginx

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run
python manage.py migrate
python manage.py runserver
```

Open http://localhost:8000

## Docker

```bash
docker-compose up --build
```

## Project Structure

```
apps/
├── catalog/    # Products, categories
├── cart/       # Shopping cart
├── orders/     # Order management
└── payments/   # NOWPayments integration
```

## License

MIT
