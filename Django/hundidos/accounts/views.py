from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserProfileForm, UserForm
from .models import Account, UserProfile
from orders.models import Order
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from carts.views import _cart_id
from carts.models import Cart, CartItem
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth.password_validation import validate_password
import requests
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden

# Create your views here.
def register(request):
    form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Obtener datos del formulario
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]  
            
            # Crear usuario solo si la contraseña es válida
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            # Enviar el correo de activación
            current_site = get_current_site(request)
            mail_subject = 'Activa tu cuenta en Hundidos para continuar'
            body = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, body, to=[to_email])
            send_email.send()

            return redirect(f'/accounts/login/?command=verification&email={email}')


    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)   


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                # Manejo de carrito (tu lógica ya existente)
                cart = Cart.objects.get(cart_id=_cart_id(request))
                if CartItem.objects.filter(cart=cart).exists():
                    cart_items = CartItem.objects.filter(cart=cart)
                    for item in cart_items:
                        item.user = user
                        item.save()
            except Cart.DoesNotExist:
                pass

            auth.login(request, user)
            messages.success(request, 'Has iniciado sesión exitosamente')

            # Redirigir a la página de `next` si está definida
            next_url = request.POST.get('next') or request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, 'Los datos son incorrectos')
            return redirect('login')

    # Si es GET, renderizar la página con el parámetro `next`
    context = {
        'next': request.GET.get('next', ''),
    }
    return render(request, 'accounts/login.html', context)




@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'Has salido de sesión')

    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Felicidades, tu cuenta está activa!')
        return redirect('login')
    else:
        messages.error(request, 'No se pudo completar la activación de la cuenta')
        return redirect('register')


@login_required(login_url='login')
def dashboard(request):

    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.get(user_id=request.user.id)

    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }


    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            current_site = get_current_site(request)
            mail_subject = 'Recupera tu Contraseña'
            body = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, body, to=[to_email])
            send_email.send()

            messages.success(request, 'Un email fue enviado a tu bandeja de entrada para recuperar tu contraseña')
            return redirect('login')
        else:
            messages.error(request, 'La cuenta de usuario no existe o surgió un problema')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Por favor escribe tu nueva contraseña')
        return redirect('resetPassword')
    else:
        messages.error(request, 'El link ha caducado')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:            
            # Validar la contraseña usando los validadores de Django
            try:
                validate_password(password)  # Lanza una excepción si no es válida
            except ValidationError as e:
                # Mostrar los errores de validación al usuario
                for error in e.messages:
                     messages.error(request, error)
                return redirect('resetPassword')

        

            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'La contraseña se actualizó correctamente')
            return redirect('login')
        else:
            messages.error(request, 'La contraseña de confirmación no concuerda')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')


def my_orders(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
        context = {
            'orders': orders,
        }
        return render(request, 'accounts/my_orders.html', context)
    else:
        return redirect('home')


@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Su información fue guardada con exito')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }

    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            try:
                validate_password(new_password)  # Lanza una excepción si no es válida
            except ValidationError as e:
                # Mostrar los errores de validación al usuario
                for error in e.messages:
                     messages.error(request, error)
                return redirect('change_password')

            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()

                messages.success(request, 'La contraseña se actualizó correctamente')
                return redirect('change_password')
            else:
                messages.error(request, 'Los datos no son válidos, ingresa una contraseña correcta')
                return redirect('change_password')
        else:
            messages.error(request, 'La contraseña no coincide con la confirmación')
            return redirect('change_password')

    return render(request, 'accounts/change_password.html')

@login_required
@user_passes_test(lambda u: u.is_admin)
def list_users(request):
    user_list = Account.objects.all()
    paginator = Paginator(user_list, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    return render(request, 'list_users.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_admin)
def create_users(request):
    form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Obtener datos del formulario
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]  
            
            # Crear usuario solo si la contraseña es válida
            if form.cleaned_data.get('is_admin'):
                user = Account.objects.create_superuser(
                    first_name=first_name, 
                    last_name=last_name, 
                    email=email, 
                    username=username, 
                    password=password
                )
            else:
                user = Account.objects.create_user(
                    first_name=first_name, 
                    last_name=last_name, 
                    email=email, 
                    username=username, 
                    password=password
                )
            user.phone_number = phone_number
            user.save()

            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            # Enviar el correo de activación
            current_site = get_current_site(request)
            mail_subject = 'Activa tu cuenta en Hundidos para continuar'
            body = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, body, to=[to_email])
            send_email.send()

            # Agregar mensaje de éxito
            messages.success(request, f'Usuario {email} creado con éxito. Correo de confirmación enviado.')
            return redirect('list_users')  # Usa el nombre de tu vista o URL correspondiente

    context = {
        'form': form
    }
    return render(request, 'accounts/create_users.html', context)



@login_required
@user_passes_test(lambda u: u.is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(Account, id=user_id)  # Obtén el usuario por su ID
    
    if request.method == 'POST':
        # Carga el formulario con los datos enviados y el usuario actual
        form = RegistrationForm(request.POST, instance=user)
        form.confirm_password = user.password
        if form.is_valid():
            # Guarda los datos actualizados, pero sin tocar la contraseña
            updated_user = form.save(commit=False)
            updated_user.password = user.password  # Mantén la contraseña actual
            updated_user.save()
            messages.success(request, "Usuario editado con éxito.")
            return redirect('list_users')  # Redirige a alguna página (ajusta según tu necesidad)
    else:
        # Carga los datos del usuario en el formulario
        form = RegistrationForm(instance=user)

    return render(request, 'accounts/edit_user.html', {'form': form})



def delete_user(request, user_id):
    # Obtener el usuario que queremos eliminar
    user = get_object_or_404(Account, id=user_id)

    # Verificar si el usuario tiene alguna reserva asociada
    if Order.objects.filter(user_id=user.id).exists():
        # Si el usuario tiene al menos una reserva asociada, no permitimos la eliminación
        messages.error(request, "No puedes eliminar esta cuenta porque tiene una reserva activa.")
        # Redirigir a la lista de usuarios
        return redirect('list_users')  # O cualquier otra página a la que desees redirigir

    # Si no tiene reservas, se elimina la cuenta
    user.delete()
    first_name =user.first_name
    messages.success(request, "'Usuario eliminado con éxito.")
    # Redirigir a la lista de usuarios
    return redirect('list_users')  # O cualquier otra página a la que desees redirigir
