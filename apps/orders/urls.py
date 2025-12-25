from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('create/', views.create_order_view, name='create'),
    path('<str:order_id>/', views.order_detail_view, name='detail'),
    path('<str:order_id>/awaiting/', views.awaiting_payment_view, name='awaiting_payment'),
]
