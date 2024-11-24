from django import forms
from .models import Order, OrderProduct, Product, Account
from django.forms.widgets import DateInput

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2', 'country', 'city', 'state', 'order_note']



class OrderProductForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['product', 'user', 'fecha_inicio', 'fecha_fin']
    
    # Campo desplegable para los productos
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="Seleccione un Producto",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Campo desplegable para los usuarios
    user = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        empty_label="Seleccione un Usuario",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campos de fecha con calendario
    fecha_inicio = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )

    fecha_fin = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )