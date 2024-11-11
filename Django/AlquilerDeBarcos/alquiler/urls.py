from django.urls import path, include
from . import views

urlpatterns = [
    path('reservar/<int:barco_id>/', views.reservar_barco, name='reservar_barco'),
    path('confirmacion_reserva/', views.confirmacion_reserva, name='confirmacion_reserva'),
]
