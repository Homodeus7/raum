import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Creates sample orders with multiple products for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of orders to create (default: 5)',
        )

    def handle(self, *args, **options):
        count = options['count']

        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.ERROR('No products found. Please add products first.'))
            return

        statuses = [
            Order.STATUS_PENDING,
            Order.STATUS_PROCESSING,
            Order.STATUS_AWAITING_PAYMENT,
            Order.STATUS_PAID,
            Order.STATUS_SHIPPED,
        ]

        shipping_methods = [
            Order.SHIPPING_STANDARD,
            Order.SHIPPING_EXPRESS,
            Order.SHIPPING_OVERNIGHT,
        ]

        shipping_costs = {
            Order.SHIPPING_STANDARD: Decimal('5.00'),
            Order.SHIPPING_EXPRESS: Decimal('15.00'),
            Order.SHIPPING_OVERNIGHT: Decimal('25.00'),
        }

        first_names = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'Robert', 'Lisa', 'James', 'Maria']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
        states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA']
        countries = ['USA', 'Canada', 'UK', 'Germany', 'France']

        sizes = ['S', 'M', 'L']

        created_orders = []

        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            city_index = random.randint(0, len(cities) - 1)
            country = random.choice(countries)
            shipping_method = random.choice(shipping_methods)

            order = Order.objects.create(
                order_id=f'ORD-{get_random_string(8).upper()}',
                status=random.choice(statuses),
                customer_email=f'{first_name.lower()}.{last_name.lower()}@example.com',
                customer_first_name=first_name,
                customer_last_name=last_name,
                customer_phone=f'+1{random.randint(1000000000, 9999999999)}',
                shipping_address_line1=f'{random.randint(100, 9999)} {random.choice(["Main", "Oak", "Pine", "Maple", "Cedar"])} Street',
                shipping_address_line2=f'Apt {random.randint(1, 999)}' if random.choice([True, False]) else '',
                shipping_city=cities[city_index],
                shipping_state=states[city_index] if country == 'USA' else '',
                shipping_postal_code=f'{random.randint(10000, 99999)}',
                shipping_country=country,
                shipping_method=shipping_method,
                shipping_cost=shipping_costs[shipping_method],
                subtotal=Decimal('0.00'),
                total=Decimal('0.00'),
            )

            num_items = random.randint(2, 5)
            selected_products = random.sample(products, min(num_items, len(products)))

            subtotal = Decimal('0.00')

            for product in selected_products:
                quantity = random.randint(1, 3)
                line_total = product.price * quantity

                OrderItem.objects.create(
                    order=order,
                    product_name=product.name,
                    product_slug=product.slug,
                    product_price=product.price,
                    size=random.choice(sizes),
                    quantity=quantity,
                    line_total=line_total,
                    product_snapshot={
                        'name': product.name,
                        'brand': product.brand,
                        'material': product.material,
                        'color': product.color,
                    }
                )

                subtotal += line_total

            order.subtotal = subtotal
            order.total = subtotal + order.shipping_cost
            order.save()

            created_orders.append(order)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created order {order.order_id} with {num_items} items (Total: ${order.total})'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {count} sample orders with products!'
            )
        )
