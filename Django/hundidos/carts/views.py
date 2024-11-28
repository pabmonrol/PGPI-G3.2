from django.shortcuts import render, redirect, get_object_or_404
from orders.models import OrderProduct
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.decorators import login_required
from datetime import datetime, date, timedelta
from django.contrib import messages

# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    current_user = request.user

    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

    if current_user.is_authenticated:
        # Usuario autenticado
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # Incrementar la cantidad del artículo del carrito
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                # Crear un nuevo artículo del carrito
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variation.clear()
                    item.variation.add(*product_variation)
                item.save()
        else:
            # Crear un nuevo artículo del carrito
            cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
            if len(product_variation) > 0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()
    else:
        # Usuario no autenticado
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # Incrementar la cantidad del artículo del carrito
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                # Crear un nuevo artículo del carrito
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variation.clear()
                    item.variation.add(*product_variation)
                item.save()
        else:
            # Crear un nuevo artículo del carrito
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variation) > 0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()

    return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, duracion=0, cart_items=None):
    tax = 0
    grand_total = 0
    extra_combustible = 0  # Nueva tasa extra
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            duracion += (cart_item.fecha_fin - cart_item.fecha_inicio).days
            total += (cart_item.product.price * duracion)
            if not cart_item.product.category.slug == 'veleros': 
                extra_combustible += 50  # Aplica una tasa extra de 50 a todos los barcos menos a los veleros

        total += extra_combustible
        tax = round((21/100) * total, 2)
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'duracion': duracion,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'extra_combustible': extra_combustible,  # Incluye la tasa extra en el contexto
    }

    return render(request, 'store/cart.html', context)


def checkout(request, total=0, duracion=0, cart_items=None):
    tax = 0
    grand_total = 0
    extra_combustible = 0  # Nueva tasa extra

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            # Verificar solapamiento
            conflicto = fechas_solapadas(cart_item.product, cart_item.fecha_inicio, cart_item.fecha_fin, excluido_id=cart_item.id)
            if conflicto:
                messages.error(
                    request,
                    f'El producto {conflicto.product.product_name} ya está reservado entre {conflicto.fecha_inicio} y {conflicto.fecha_fin}.'
                )
                return redirect('cart')

            duracion = (cart_item.fecha_fin - cart_item.fecha_inicio).days
            total += (cart_item.product.price * duracion)
            if cart_item.product.category.slug != 'veleros':
                extra_combustible += 50  # Aplica una tasa extra de 50 a todos los barcos menos a los veleros

        tax = round((21/100) * total, 2)
        grand_total = total + tax + extra_combustible

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'duracion': duracion,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'extra_combustible': extra_combustible,  # Incluye la tasa extra en el contexto
    }

    return render(request, 'store/checkout.html', context)

def update_cart(request):
    if request.method == 'POST':
        for item_id in request.POST.getlist('item_ids'):
            start_date = request.POST.get(f'start_date_{item_id}')
            end_date = request.POST.get(f'end_date_{item_id}')
            cart_item = CartItem.objects.get(id=item_id)
            
            # Validar que la fecha de inicio sea posterior al día de hoy
            if datetime.strptime(start_date, '%Y-%m-%d').date() <= date.today():
                messages.error(request, 'La fecha de inicio debe ser posterior al día de hoy.')
                return redirect('cart')
            
            # Validar que la fecha de inicio sea anterior a la fecha de fin
            if datetime.strptime(start_date, '%Y-%m-%d') >= datetime.strptime(end_date, '%Y-%m-%d'):
                messages.error(request, 'La fecha de inicio debe ser anterior a la fecha de fin.')
                return redirect('cart')
            

            # Verificar solapamiento
            conflicto = fechas_solapadas(cart_item.product, datetime.strptime(start_date, '%Y-%m-%d').date(), datetime.strptime(end_date, '%Y-%m-%d').date(), excluido_id=cart_item.id)
            if conflicto:
                messages.error(
                    request,
                    f'El producto {conflicto.product.product_name} ya está reservado entre {conflicto.fecha_inicio} y {conflicto.fecha_fin}.'
                )
                continue
            
            cart_item.fecha_inicio = datetime.strptime(start_date, '%Y-%m-%d')
            cart_item.fecha_fin = datetime.strptime(end_date, '%Y-%m-%d')
            cart_item.save()
    return redirect('cart')


def fechas_solapadas(producto, nueva_fecha_inicio, nueva_fecha_fin, excluido_id=None):
    """
    Verifica si hay solapamiento de fechas con las reservas existentes para el producto.
    """
    reservas = OrderProduct.objects.filter(product=producto)
    if excluido_id:
        reservas = reservas.exclude(id=excluido_id)

    for reserva in reservas:
        if (
            nueva_fecha_inicio <= reserva.fecha_fin and
            nueva_fecha_fin >= reserva.fecha_inicio
        ):
            return reserva  # Conflicto detectado
    return None
