from django.shortcuts import render
from store.models import Product, ReviewRating

def home(request):
    #products = Product.objects.all().filter(is_available=True).order_by('created_date')
    products = Product.objects.all().order_by('created_date')
    reviews_dict = {}

    # Obtener las reseñas asociadas a los productos
    for product in products:
        #reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
        reviews_dict[product.id] = ReviewRating.objects.filter(product_id=product.id, status=True)


    context = {
        'products': products,
        #'reviews': reviews,
        'reviews_dict': reviews_dict,  # Cambiado a un diccionario para que las reseñas estén organizadas por producto

    }

    return render(request, 'home.html', context)
