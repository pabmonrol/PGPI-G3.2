from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.catalogo_barcos, name='catalogo_barcos'),  # Ruta para el catálogo de barcos
]
