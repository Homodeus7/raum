from django.core.management.base import BaseCommand
from apps.catalog.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load synthetic data for categories and products'

    def handle(self, *args, **options):
        self.stdout.write('Loading synthetic data...')

        glasses_category, created = Category.objects.get_or_create(
            name='Glasses',
            defaults={'description': 'Optical frames for prescription lenses'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {glasses_category.name}'))
        else:
            self.stdout.write(f'Category already exists: {glasses_category.name}')

        sunglasses_category, created = Category.objects.get_or_create(
            name='Sunglasses',
            defaults={'description': 'Sun protection eyewear with UV filters'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {sunglasses_category.name}'))
        else:
            self.stdout.write(f'Category already exists: {sunglasses_category.name}')

        products_data = [
            {
                'name': 'Heavenly 02',
                'category': glasses_category,
                'price': Decimal('80339.00'),
                'brand': 'Heavenly',
                'description': 'Elegant rimless frame with sleek titanium temples. Perfect for minimalist style.',
                'color': 'Silver',
                'material': 'Titanium',
                'shape': 'Rectangle',
                'lens_width_mm': Decimal('52.0'),
                'bridge_width_mm': Decimal('18.0'),
                'temple_length_mm': Decimal('140.0'),
                'frame_width_mm': Decimal('135.0'),
                'lens_height_mm': Decimal('32.0'),
            },
            {
                'name': 'Rollie 02',
                'category': glasses_category,
                'price': Decimal('73531.00'),
                'brand': 'Rollie',
                'description': 'Classic oval metal frame with comfortable nose pads. Timeless design for everyday wear.',
                'color': 'Silver',
                'material': 'Metal',
                'shape': 'Oval',
                'lens_width_mm': Decimal('50.0'),
                'bridge_width_mm': Decimal('17.0'),
                'temple_length_mm': Decimal('138.0'),
                'frame_width_mm': Decimal('130.0'),
                'lens_height_mm': Decimal('36.0'),
            },
            {
                'name': 'Lolos 02',
                'category': glasses_category,
                'price': Decimal('70807.00'),
                'brand': 'Lolos',
                'description': 'Sophisticated oval frame with unique temple design. Combines style and comfort.',
                'color': 'Silver',
                'material': 'Metal',
                'shape': 'Oval',
                'lens_width_mm': Decimal('48.0'),
                'bridge_width_mm': Decimal('19.0'),
                'temple_length_mm': Decimal('142.0'),
                'frame_width_mm': Decimal('128.0'),
                'lens_height_mm': Decimal('34.0'),
            },
            {
                'name': 'Boba 02',
                'category': glasses_category,
                'price': Decimal('80339.00'),
                'brand': 'Boba',
                'description': 'Refined oval metal frame with clean lines. Lightweight and durable construction.',
                'color': 'Silver',
                'material': 'Metal',
                'shape': 'Oval',
                'lens_width_mm': Decimal('51.0'),
                'bridge_width_mm': Decimal('18.0'),
                'temple_length_mm': Decimal('140.0'),
                'frame_width_mm': Decimal('132.0'),
                'lens_height_mm': Decimal('35.0'),
            },
            {
                'name': 'Limes 02',
                'category': glasses_category,
                'price': Decimal('76254.00'),
                'brand': 'Limes',
                'description': 'Modern oval frame with acetate temples. Bold yet sophisticated look. Currently being restocked.',
                'color': 'Silver/Black',
                'material': 'Mixed',
                'shape': 'Oval',
                'lens_width_mm': Decimal('50.0'),
                'bridge_width_mm': Decimal('18.0'),
                'temple_length_mm': Decimal('140.0'),
                'frame_width_mm': Decimal('130.0'),
                'lens_height_mm': Decimal('36.0'),
            },
            {
                'name': 'Moody 02',
                'category': glasses_category,
                'price': Decimal('73531.00'),
                'brand': 'Moody',
                'description': 'Stylish oval frame with contrasting temple accents. Perfect balance of form and function.',
                'color': 'Silver/Black',
                'material': 'Mixed',
                'shape': 'Oval',
                'lens_width_mm': Decimal('49.0'),
                'bridge_width_mm': Decimal('19.0'),
                'temple_length_mm': Decimal('142.0'),
                'frame_width_mm': Decimal('129.0'),
                'lens_height_mm': Decimal('35.0'),
            },
        ]

        created_count = 0
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
            else:
                self.stdout.write(f'Product already exists: {product.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nData loading complete! Created {created_count} new products.'
        ))
