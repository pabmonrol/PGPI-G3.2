import datetime
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
    puertos = Product.objects.values_list('puerto', flat=True).distinct()
    fabricantes = Product.objects.values_list('fabricante', flat=True).distinct()
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
    selected_puerto = request.GET.get('puerto')
    if selected_puerto:
        products = products.filter(puerto=selected_puerto)

    #Filtrar por fabricante
    selected_fabricante = request.GET.get('fabricante')
    if selected_fabricante:
        products = products.filter(fabricante=selected_fabricante)

    # Filtrar por rango de precios
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)

    # Filtrar por capacidad
    selected_capacity = request.GET.get('capacidad')
    if selected_capacity:
        products = products.filter(capacidad__gte=selected_capacity)

    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'puertos': puertos,
        'fabricantes': fabricantes,
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
            'title': f'Baja disponibilidad',  # Texto que aparecerá en el calendario
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
        products = Product.objects.all()
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
            context = {
                'products': products,
                'product_count': product_count,
            }
            return render(request, 'store/store.html', context)
        
    # Búsqueda de pedidos por nota de reserva
    if 'reservation' in request.GET:
        reservation = request.GET.get('reservation')
        try:
            # Obtener el pedido que coincide con la nota y está ordenado
            order = Order.objects.get(order_note=reservation, is_ordered=True)
            ordered_products = OrderProduct.objects.filter(order_id=order.id)

            # Calcular el subtotal
            subtotal=0
            for i in ordered_products:
                subtotal += i.product_price*i.quantity*(i.fecha_fin-i.fecha_inicio).days
            payment = order.payment

            # Crea una lista de productos con los días restantes calculados
            products_with_days_left = []
            for item in ordered_products:
                fecha_fin = item.fecha_fin 
                if (datetime.date.today() >= item.fecha_inicio):  # Si la fecha de fin es anterior a la fecha actual
                    dias_restantes = (fecha_fin - datetime.date.today()).days  # Calcula los días restantes
                else:
                    dias_restantes = (fecha_fin - item.fecha_inicio).days  # Si no, establece los días restantes como la duración de la reserva
                # Si los días restantes son negativos, establece 0
                if dias_restantes < 0:
                    dias_restantes = 0
                
                # Crea un diccionario con el producto y los días restantes
                product_data = {
                    'item': item,  # El objeto 'OrderProduct'
                    'nombre': item.product.product_name,  # El nombre del producto
                    'dias_restantes': dias_restantes,  # Los días restantes calculados
                }
                
                # Añade el diccionario a la lista
                products_with_days_left.append(product_data)
    

            context = {
                'order': order,
                'ordered_products': ordered_products,
                'order_number': order.order_number,
                'transID': 0,  # Transacción por defecto
                'payment': payment,
                'subtotal': subtotal,
                'products_with_days_left': products_with_days_left,	
            }

            # Renderizar según el estado del pedido
            if order.status == 'Pendiente de pago':
                return render(request, 'orders/order_incomplete.html', context)
            else:
                return render(request, 'orders/order_complete.html', context)
        except Order.DoesNotExist:
            # Manejar el caso en que no se encuentra el pedido
            return render(request, 'orders/order_not_found.html', {'error_message': 'No se encontró la reserva.'})

    # Si no hay parámetros en la URL, redirigir a una página base o devolver un error
    return render(request, 'store/store.html', {'products': [], 'product_count': 0})

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
    if OrderProduct.objects.filter(product_id=ship.id).exists():
        # Si el usuario tiene al menos una reserva asociada, no permitimos la eliminación
        messages.error(request, "No puedes eliminar esta cuenta porque tiene una reserva activa.")
        # Redirigir a la lista de usuarios
        return redirect('product_list')  # O cualquier otra página a la que desees redirigir

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