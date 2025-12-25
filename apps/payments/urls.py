from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create/<str:order_id>/', views.create_invoice_view, name='create_invoice'),
    path('webhook/', views.webhook_view, name='webhook'),
    path('success/<str:order_id>/', views.success_view, name='success'),
    path('failed/<str:order_id>/', views.failed_view, name='failed'),
]
