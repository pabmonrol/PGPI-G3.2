import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from carts.models import CartItem
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from store.models import Product, Variation
from carts.models import CartItem, Cart
from accounts.models import UserProfile
from .forms import OrderForm, OrderAdminForm
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse


from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages

# Generar un codigo aleatorio de 7 letras y que empieza con RES
def generate_random_code():
    prefix = "RES-"
    random_part = ''.join(random.choices(string.digits + string.ascii_letters, k=20))
    return prefix + random_part

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def payments(request, order_id):
    # Verifica que la orden existe
    order = Order.objects.get(is_ordered=False, order_number=order_id)
    body = json.loads(request.body)
    if request.user.is_authenticated:
        payment = Payment(
            user = request.user if request.user.is_authenticated else None,
            payment_id = body['transID'],
            payment_method = body['payment_method'],
            amount_id = order.order_total,
            status = body['status'],
        )

        payment.save()
        order.payment = payment
        order.is_ordered = True
        order.status = 'Pagado'
        order.save()
    else:
        order.is_ordered = True
        order.status = 'Pagado'
        order.save()

    # Manejar carrito basado en usuario o sesión
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart)

    for item in cart_items:
        # Crear un nuevo OrderProduct
        order_product = OrderProduct()
        order_product.order = order
        order_product.user = request.user if request.user.is_authenticated else None
        order_product.product = item.product
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.fecha_inicio = item.fecha_inicio
        order_product.fecha_fin = item.fecha_fin
        order_product.ordered = False  # Mantén esto como False si aún no está confirmado
        order_product.save()

        #Copiar las variaciones
        product_variation = item.variation.all()
        order_product.variation.set(product_variation)
        order_product.save()

    # Enviar correo al usuario con los detalles de la orden
    mail_subject = "Detalles de tu reserva - Codigo de Seguimiento"
    body = render_to_string('orders/order_paid_email.html', {
        'order': order,
        'nombre': order.first_name,
        'cart_items': cart_items,
    })

    to_email = order.email
    send_email = EmailMessage(mail_subject, body, to=[to_email])
    send_email.send()

    # Limpiar el carrito
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user).delete()
    else:
        CartItem.objects.filter(cart=cart).delete()

    data = {
        'order_number': order.order_number,
        'order_note': order.order_note,
    }


    return JsonResponse(data)


# Create your views here.


def place_order(request, total=0, duracion=0):
    if request.user.is_authenticated:
        current_user = request.user
        cart_items = CartItem.objects.filter(user=current_user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart)

    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    extra_combustible = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.duracion() * cart_item.quantity) 
        if not cart_item.product.category.slug == 'veleros': 
            extra_combustible += 50


    tax = round((21/100) * (total + extra_combustible), 2)
    grand_total = total + extra_combustible + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            data = Order()
            if request.user.is_authenticated:
                data.user = current_user
            else:
                data.user = None  # Usuario no registrado

            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            random_code = generate_random_code()
            data.order_note = random_code
            data.order_total = grand_total
            data.tax = tax
            data.extra_combustible = extra_combustible
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generar número de pedido
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # 20231121
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(is_ordered=False, order_number=order_number)
            order_products = [
                {
                    'product': item.product,
                    'quantity': duracion,
                    'price': item.product.price,
                    'total': item.product.price * item.quantity
                }
                for item in cart_items
            ]

            context = {
                'order': order,
                'cart_items': cart_items,
                'order_products': order_products,
                'total': total,
                'tax': tax,
                'extra_combustible': extra_combustible,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
            return redirect('checkout')

    context = {
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'orders/place_order.html', context)

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price*i.quantity*(i.fecha_fin-i.fecha_inicio).days

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'today': datetime.date.today(),
        }

        return render(request, 'orders/order_complete.html', context)

    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    
# Marca como PENDIENTE DE PAGO si la reserva no se ha pagado (opcion contra reembolso) 
# y redirige a la pagina de lista de ordenes
def mark_pending(request, order_id):
    # Verifica que la orden existe
    order = get_object_or_404(Order, id=order_id, is_ordered=False)
    
    # Cambiar el estado a 'Pendiente de pago'
    order.status = 'Pendiente de pago'
    order.is_ordered = True  # Opcional: Marca la orden como procesada
    order.save()

    # Manejar carrito basado en usuario o sesión
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart)

    for item in cart_items:
        # Crear un nuevo OrderProduct
        order_product = OrderProduct()
        order_product.order = order
        order_product.user = request.user if request.user.is_authenticated else None
        order_product.product = item.product
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.fecha_inicio = item.fecha_inicio
        order_product.fecha_fin = item.fecha_fin
        order_product.ordered = False  # Mantén esto como False si aún no está confirmado
        order_product.save()

        #Copiar las variaciones
        product_variation = item.variation.all()
        order_product.variation.set(product_variation)
        order_product.save()


    # Enviar correo al usuario con los detalles de la orden
    mail_subject = "Detalles de tu reserva - Codigo de Seguimiento"
    body = render_to_string('orders/order_recieved_email.html', {
        'order': order,
        'nombre': order.first_name,
        'cart_items': cart_items,
    })

    to_email = order.email
    send_email = EmailMessage(mail_subject, body, to=[to_email])
    send_email.send()

    # Limpiar el carrito
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user).delete()
    else:
        CartItem.objects.filter(cart=cart).delete()

    # Redirige a la vista de órdenes del usuario si está autenticado, de lo contrario redirige a la página de inicio
    if request.user.is_authenticated:
        return redirect('my_orders')
    else:
        return redirect('home')

@login_required
@user_passes_test(lambda u: u.is_admin)
def order_list(request):
    paginator = Paginator(order_list, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    orders = Order.objects.filter(is_ordered=1)  # Obtiene todos los pedidos
    return render(request, 'order_list.html', {'orders': orders})

@login_required
@user_passes_test(lambda u: u.is_admin)
def edit_order(request, order_id):
    # Obtener el OrderProduct por su ID
    order = get_object_or_404(Order, id=order_id)

    # Si el formulario fue enviado
    if request.method == 'POST':
        form = OrderAdminForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'La reserva se ha actualizado correctamente.')
            return redirect('order_list')  # Redirigir a la lista de reservas
    else:
        form = OrderAdminForm(instance=order)
    
    return render(request, 'orders/edit_order.html', {'form': form, 'order_product': order})

@login_required
@user_passes_test(lambda u: u.is_admin)
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    order.delete()
    messages.success(request, "Reserva eliminada con éxito.")
    return redirect('order_list')  # O cualquier otra página a la que desees redirigir
