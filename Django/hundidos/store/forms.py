from django import forms
from .models import ReviewRating
from .models import Product

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['images', 'product_name', 'description', 'price', 'capacidad', 'category', 'fabricante', 'puerto']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }