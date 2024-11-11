from django.shortcuts import render, get_object_or_404, redirect
from .forms import FormularioAlquiler
from barcos.models import Barco

def reservar_barco(request, barco_id):
    barco = get_object_or_404(Barco, id=barco_id)
    if request.method == 'POST':
        form = FormularioAlquiler(request.POST)
        if form.is_valid():
            alquiler = form.save(commit=False)
            alquiler.usuario = request.user.perfilusuario
            alquiler.barco = barco
            alquiler.save()
            return redirect('confirmacion_reserva')
    else:
        form = FormularioAlquiler()
    return render(request, 'alquiler/reservar.html', {'form': form, 'barco': barco})

def confirmacion_reserva(request):
    return render(request, 'alquiler/confirmacion_reserva.html')

def home(request):
    return render(request, 'home.html')