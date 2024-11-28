from django.shortcuts import render, redirect
from django.http import JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_id = order.order_total,
        status = body['status'],
    )

    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    CartItem.objects.filter(user=request.user).delete()

    mail_subject = 'Tu compra fue realizada!'
    body = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })

    to_email = request.user.email
    send_email = EmailMessage(mail_subject, body, to=[to_email])
    send_email.send()

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }


    return JsonResponse(data)


# Create your views here.
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = round((16/100) * total, 2)
    grand_total = total + tax


    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            yr=int(datetime.date.today().strftime('%Y'))
            mt=int(datetime.date.today().strftime('%m'))
            dt=int(datetime.date.today().strftime('%d'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }

            return render(request, 'orders/payments.html', context)

    else:
        return redirect('checkout')



def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price*i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }

        return render(request, 'orders/order_complete.html', context)

    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
<<<<<<< Updated upstream
=======
    
# Marca como PAGADO si el pago se ha realizado online 
# y redirige a la pagina de lista de ordenes
def mark_paid(request, order_id):
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
    order_list = OrderProduct.objects.all()
    paginator = Paginator(order_list, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    return render(request, 'order_list.html', {'orders': orders})

@login_required
@user_passes_test(lambda u: u.is_admin)
def edit_order(request, order_id):
    # Obtener el OrderProduct por su ID
    order_product = get_object_or_404(OrderProduct, id=order_id)

    # Si el formulario fue enviado
    if request.method == 'POST':
        form = OrderProductForm(request.POST, instance=order_product)
        if form.is_valid():
            form.save()
            messages.success(request, 'La reserva se ha actualizado correctamente.')
            return redirect('order_list')  # Redirigir a la lista de reservas
    else:
        form = OrderProductForm(instance=order_product)
    
    return render(request, 'orders/edit_order.html', {'form': form, 'order_product': order_product})

@login_required
@user_passes_test(lambda u: u.is_admin)
def delete_order(request, order_id):
    order = get_object_or_404(OrderProduct, id=order_id)

    order.delete()
    messages.success(request, "Reserva eliminada con éxito.")
    return redirect('order_list')  # O cualquier otra página a la que desees redirigir
>>>>>>> Stashed changes
