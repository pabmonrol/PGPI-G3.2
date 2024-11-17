from django import forms
from .models import Account, UserProfile
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Ingrese Contraseña',
        'class': 'form-control',
    }))
    
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirmar Contraseña',
        'class': 'form-control',
    }))

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Ingrese su nombre'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Ingrese sus apellidos'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Ingrese su número'
        self.fields['email'].widget.attrs['placeholder'] = 'Ingrese su email'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email_validator = EmailValidator(message='Por favor, ingrese un correo electrónico válido.')
        username = email.split("@")[0]   
        try:
            email_validator(email)
        except ValidationError:
            raise ValidationError('Por favor, ingrese un correo electrónico válido. ###@####.#')
        
        if Account.objects.filter(email=email).exists():
            raise ValidationError('Ya existe una cuenta con este correo electrónico')
        elif Account.objects.filter(username=username).exists():
            raise ValidationError(f"El nombre de usuario '{username}' ya está en uso. Por favor, elija otro.")
        return email

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Verificar si las contraseñas coinciden
        if password != confirm_password:
            raise forms.ValidationError(
                'Parece que la contraseña no coincide, verifique su información'
            )
        if password == confirm_password:
            
            # Validar la contraseña usando los validadores de Django
            try:
                validate_password(password)  # Lanza una excepción si no es válida
            except ValidationError as e:
                # Mostrar los errores de validación al usuario
                for error in e.messages:
                    raise forms.ValidationError(e)

        return cleaned_data

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class']='form-control'


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages = {'invalid': ('Solo archivos de imagen')}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ('address_line_1', 'address_line_2', 'city', 'state', 'country', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class']='form-control'
