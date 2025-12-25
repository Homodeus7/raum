import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from apps.orders.models import Order
from apps.payments.models import Payment


class Command(BaseCommand):
    help = 'Creates sample payments for existing orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of payments to create (default: 3)',
        )

    def handle(self, *args, **options):
        count = options['count']

        orders_without_payment = Order.objects.filter(payment__isnull=True)[:count]

        if not orders_without_payment:
            self.stdout.write(self.style.ERROR('No orders without payment found.'))
            return

        statuses = [
            Payment.STATUS_WAITING,
            Payment.STATUS_CONFIRMING,
            Payment.STATUS_CONFIRMED,
            Payment.STATUS_FINISHED,
            Payment.STATUS_PARTIALLY_PAID,
        ]

        crypto_currencies = ['btc', 'eth', 'usdt', 'ltc', 'bnb', 'ada', 'doge', 'xrp']

        created_payments = []

        for order in orders_without_payment:
            status = random.choice(statuses)
            pay_currency = random.choice(crypto_currencies)

            crypto_rates = {
                'btc': Decimal('42000.00'),
                'eth': Decimal('2200.00'),
                'usdt': Decimal('1.00'),
                'ltc': Decimal('70.00'),
                'bnb': Decimal('300.00'),
                'ada': Decimal('0.50'),
                'doge': Decimal('0.08'),
                'xrp': Decimal('0.60'),
            }

            rate = crypto_rates.get(pay_currency, Decimal('1.00'))
            pay_amount = order.total / rate

            actually_paid = None
            if status in [Payment.STATUS_FINISHED, Payment.STATUS_CONFIRMED]:
                variation = Decimal(str(random.uniform(0.98, 1.02)))
                actually_paid = pay_amount * variation

            payment = Payment.objects.create(
                order=order,
                nowpayments_invoice_id=f'INV-{get_random_string(12).upper()}',
                nowpayments_payment_id=f'PAY-{get_random_string(16).upper()}' if status != Payment.STATUS_WAITING else '',
                status=status,
                price_amount=order.total,
                price_currency='usd',
                pay_amount=pay_amount,
                pay_currency=pay_currency,
                actually_paid=actually_paid,
                invoice_url=f'https://nowpayments.io/payment/{get_random_string(32).lower()}',
                webhook_data={
                    'payment_status': status,
                    'invoice_id': f'INV-{get_random_string(12).upper()}',
                }
            )

            if status in [Payment.STATUS_FINISHED, Payment.STATUS_CONFIRMED]:
                order.status = Order.STATUS_PAID
                order.save()

            created_payments.append(payment)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created payment for order {order.order_id} - Status: {payment.get_status_display()} - {pay_amount:.8f} {pay_currency.upper()}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {len(created_payments)} sample payments!'
            )
        )
