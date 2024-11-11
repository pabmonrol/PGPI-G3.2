from django.shortcuts import render
from .models import Barco

def catalogo_barcos(request):
    barcos = Barco.objects.all()
    return render(request, 'barcos/catalogo.html', {'barcos': barcos})
