import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.cart.models import Cart
from .order_dtos import CreateOrderDTO, OrderCreatedDTO, OrderItemDTO


class OrderService:
    @staticmethod
    def generate_order_id() -> str:
        timestamp = timezone.now().strftime('%Y%m%d')
        unique_part = str(uuid.uuid4().hex[:8]).upper()
        return f"ORD-{timestamp}-{unique_part}"

    @staticmethod
    @transaction.atomic
    def create_order_from_dto(dto: CreateOrderDTO) -> OrderCreatedDTO:
        order_id = OrderService.generate_order_id()

        order = Order.objects.create(
            order_id=order_id,
            status=Order.STATUS_PENDING,
            customer_email=dto.customer_info.email,
            customer_first_name=dto.customer_info.first_name,
            customer_last_name=dto.customer_info.last_name,
            customer_phone=dto.customer_info.phone,
            shipping_address_line1=dto.shipping_address.address_line1,
            shipping_address_line2=dto.shipping_address.address_line2 or '',
            shipping_city=dto.shipping_address.city,
            shipping_state=dto.shipping_address.state or '',
            shipping_postal_code=dto.shipping_address.postal_code,
            shipping_country=dto.shipping_address.country,
            shipping_method=dto.shipping_method,
            shipping_cost=dto.shipping_cost,
            subtotal=dto.subtotal,
            total=dto.total,
            notes=dto.notes or '',
        )

        for item_dto in dto.items:
            OrderItem.objects.create(
                order=order,
                product_name=item_dto.product_name,
                product_slug=item_dto.product_slug,
                product_price=item_dto.product_price,
                size=item_dto.size,
                quantity=item_dto.quantity,
                line_total=item_dto.product_price * item_dto.quantity,
                product_snapshot=item_dto.product_snapshot,
            )

        return OrderCreatedDTO(
            order_id=order.order_id,
            total=order.total,
            customer_email=order.customer_email,
        )

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        cart: Cart,
        customer_info: dict,
        shipping_address: dict,
        shipping_method: str,
        shipping_cost: Decimal,
        notes: str = ''
    ) -> OrderCreatedDTO:
        from apps.catalog.models import Product

        items = []
        for cart_item in cart.items.select_related('product').all():
            product = cart_item.product
            product_snapshot = {
                'name': product.name,
                'price': str(product.price),
                'material': product.material,
                'shape': product.shape,
                'color': product.color,
                'brand': product.brand,
            }

            items.append(OrderItemDTO(
                product_id=product.id,
                product_name=product.name,
                product_slug=product.slug,
                product_price=product.price,
                size=cart_item.size,
                quantity=cart_item.quantity,
                product_snapshot=product_snapshot,
            ))

        subtotal = cart.subtotal
        total = subtotal + shipping_cost

        from .order_dtos import CustomerInfoDTO, ShippingAddressDTO

        dto = CreateOrderDTO(
            customer_info=CustomerInfoDTO(**customer_info),
            shipping_address=ShippingAddressDTO(**shipping_address),
            items=items,
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            subtotal=subtotal,
            total=total,
            notes=notes,
        )

        order_created = OrderService.create_order_from_dto(dto)

        cart.items.all().delete()

        return order_created

    @staticmethod
    def get_order_by_id(order_id: str) -> Order:
        return Order.objects.select_related('payment').prefetch_related('items').get(order_id=order_id)

    @staticmethod
    @transaction.atomic
    def update_order_status(order_id: str, status: str) -> Order:
        order = Order.objects.get(order_id=order_id)
        order.status = status
        order.save(update_fields=['status', 'updated_at'])
        return order

    @staticmethod
    @transaction.atomic
    def mark_order_as_paid(order_id: str) -> Order:
        return OrderService.update_order_status(order_id, Order.STATUS_PAID)
