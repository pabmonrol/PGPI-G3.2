from django import forms
from .models import Order, OrderProduct, Product, Account
from django.forms.widgets import DateInput
import re
from django.core.exceptions import ValidationError

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2', 'country', 'city', 'state', 'order_note']


    def clean(self):
        # Llama al método clean de la clase padre
        cleaned_data = super().clean()
        
        # Obtén valores de varios campos
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        phone = cleaned_data.get('phone')
        email = cleaned_data.get('email')
        country = cleaned_data.get('country')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        
        # Validación: Nombre y Apellido no pueden estar vacíos
        if not first_name:
            self.add_error('first_name', 'El nombre es obligatorio.')
        if not last_name:
            self.add_error('last_name', 'El apellido es obligatorio.')
        
        # Validación: El número de teléfono debe ser numérico y tener al menos 10 dígitos
        if phone and (len(phone) < 9):
            self.add_error('phone', 'El teléfono debe ser numérico y tener al menos 9 dígitos.')

        # Validación: Email debe ser válido
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValidationError('Debe ingresar un correo electrónico válido.')

        # Validación: El número de teléfono debe ser numérico y tener al menos 10 dígitos
        if state and (len(state) != 5):
            self.add_error('state', 'El código postal debe ser numérico y tener 5 dígitos.')
        
        # Validación: País y Ciudad no pueden estar vacíos
        if not country:
            self.add_error('country', 'El país es obligatorio.')
        if not city:
            self.add_error('city', 'La ciudad es obligatoria.')

        # Retorna los datos validados
        return cleaned_data

class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2', 'country', 'city', 'state', 'status']


    def clean(self):
        # Llama al método clean de la clase padre
        cleaned_data = super().clean()
        
        # Obtén valores de varios campos
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        phone = cleaned_data.get('phone')
        email = cleaned_data.get('email')
        country = cleaned_data.get('country')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        
        # Validación: Nombre y Apellido no pueden estar vacíos
        if not first_name:
            self.add_error('first_name', 'El nombre es obligatorio.')
        if not last_name:
            self.add_error('last_name', 'El apellido es obligatorio.')
        
        # Validación: El número de teléfono debe ser numérico y tener al menos 10 dígitos
        if phone and (len(phone) < 9):
            self.add_error('phone', 'El teléfono debe ser numérico y tener al menos 9 dígitos.')

        # Validación: Email debe ser válido
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValidationError('Debe ingresar un correo electrónico válido.')

        # Validación: El número de teléfono debe ser numérico y tener al menos 10 dígitos
        if state and (len(state) != 5):
            self.add_error('state', 'El código postal debe ser numérico y tener 5 dígitos.')
        
        # Validación: País y Ciudad no pueden estar vacíos
        if not country:
            self.add_error('country', 'El país es obligatorio.')
        if not city:
            self.add_error('city', 'La ciudad es obligatoria.')

        # Retorna los datos validados
        return cleaned_data