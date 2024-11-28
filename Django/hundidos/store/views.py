from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct, Order
from datetime import timedelta
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ProductForm


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories).order_by('id')
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().order_by('id')
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    # Filtrar por puerto
    puertos = request.GET.getlist('puerto')
    if puertos:
        products = products.filter(puerto__in=puertos)

    #Filtrar por fabricante
    fabricantes = request.GET.getlist('fabricante')
    if fabricantes:
        products = products.filter(fabricante__in=fabricantes)

    # Filtrar por rango de precios
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)

    # Filtrar por capacidad
    capacidades = request.GET.getlist('capacidad')
    if capacidades:
        products = products.filter(capacidad__in=capacidades)

    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'request': request,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    reservas = OrderProduct.objects.filter(product=single_product)
    eventos = []
    for reserva in reservas:
        eventos.append({
            'title': f'Ocupado',  # Texto que aparecerá en el calendario
            'start': reserva.fecha_inicio.strftime('%Y-%m-%d'),  # Fecha inicio
            'end': (reserva.fecha_fin + timedelta(days=1)).strftime('%Y-%m-%d'),  # Fecha fin + 1 día
            'backgroundColor': 'red',  # Color del evento
            'borderColor': 'darkred',
        })

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'eventos_json': eventos,  # Enviamos los eventos en formato JSON
    }

    return render(request, 'store/product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
            context = {
                'products': products,
                'product_count': product_count,
                'reservations': reservations
            }
            return render(request, 'store/store.html', context)
        
    if 'reservation' in request.GET:    
        reservation = request.GET.get('reservation')
        order = Order.objects.get(order_note=reservation, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price*i.quantity
        payment = order.payment

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': 0,
            'payment': payment,
            'subtotal': subtotal,
        }
        if order.status == 'Pendiente de pago':
            return render(request, 'orders/order_incomplete.html', context)
        else:
            return render(request, 'orders/order_complete.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Muchas gracias!, tu comentario ha sido actualizado.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Muchas gracias!, tu comentario ha sido publicado.')
                return redirect(url)

@login_required
@user_passes_test(lambda u: u.is_admin)
def product_list(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    return render(request, 'product_list.html', {'products': products})

@login_required
@user_passes_test(lambda u: u.is_admin)
def edit_ship(request, ship_id):
    # Obtener el barco a editar
    ship = get_object_or_404(Product, id=ship_id)
    
    # Verificar si el formulario fue enviado
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=ship)
        
        if form.is_valid():
            form.save()  # Guardar el barco editado
            # Redirigir a la lista de barcos con un mensaje de éxito
            return redirect('product_list')  # O la URL donde deseas redirigir después de la edición
    else:
        # Si no es un POST, llenar el formulario con los datos actuales del barco
        form = ProductForm(instance=ship)
    
    return render(request, 'store/edit_ship.html', {'form': form, 'ship': ship})

@login_required
@user_passes_test(lambda u: u.is_admin)
def delete_ship(request, ship_id):
   # Obtener el usuario que queremos eliminar
    ship = get_object_or_404(Product, id=ship_id)

    # Si no tiene reservas, se elimina la cuenta
    ship.delete()
    messages.success(request, "Barco eliminado con éxito.")
    # Redirigir a la lista de usuarios
    return redirect('product_list')  # O cualquier otra página a la que desees redirigir


@login_required
@user_passes_test(lambda u: u.is_admin)
def create_ship(request):
    form = ProductForm()

    # Agregar clases CSS a los campos del formulario
    form.fields['product_name'].widget.attrs['class'] = 'form-control'
    form.fields['description'].widget.attrs['class'] = 'form-control'
    form.fields['price'].widget.attrs['class'] = 'form-control'
    form.fields['capacidad'].widget.attrs['class'] = 'form-control'
    form.fields['category'].widget.attrs['class'] = 'form-control'

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Redirigir a la lista de productos

    return render(request, 'store/create_ship.html', {'form': form})