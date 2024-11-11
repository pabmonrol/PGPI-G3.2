from django import forms
from .models import Alquiler

class FormularioAlquiler(forms.ModelForm):
    class Meta:
        model = Alquiler
        fields = ['barco', 'fecha_inicio', 'fecha_fin', 'fianza']
