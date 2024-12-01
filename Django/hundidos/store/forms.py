from django import forms
from .models import ReviewRating
from .models import Product
from django.core.exceptions import ValidationError

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['images', 'product_name', 'description', 'price', 'capacidad', 'stock', 'category', 'fabricante', 'puerto']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        capacidad = cleaned_data.get('capacidad')
        price = cleaned_data.get('price')
        stock = cleaned_data.get('stock')

        if capacidad is not None and capacidad <= 0:
            self.add_error('capacidad', 'La capacidad debe ser mayor que 0.')

        if price is not None and price <= 0:
            self.add_error('price', 'El precio debe ser mayor que 0.')
        
        if stock is not None and stock <= 0:
            self.add_error('stock', 'La cantidad debe ser mayor que 0.')

        return cleaned_data