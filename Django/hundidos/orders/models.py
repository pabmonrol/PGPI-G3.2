from datetime import date, timedelta
from django.db import models
from django.forms import ValidationError
# from jsonschema import ValidationError
from accounts.models import Account
from store.models import Product, Variation
from django.utils import timezone


# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_id = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id

# Estados de una reserva
class Order(models.Model):
    STATUS = (
        ('Pagado', 'Pagado'),
        ('Pendiente de pago', 'Pendiente de pago'),
        ('En uso', 'En uso'),
        ('Devuelto', 'Devuelto'),
    )


    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100)
    country = models.CharField(max_length=50)  # Agregado mio
    city = models.CharField(max_length=50)  # Agregado mio
    state = models.CharField(max_length=5)  # QUE ES CODIGO POSTAL EN CHECKOUT.HTML
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    extra_combustible = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'


    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'


    def __str__(self):
        return self.first_name

def get_default_start_date():
    return timezone.now().date() + timedelta(days=1)

def get_default_end_date():
    return timezone.now().date() + timedelta(days=2)

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    fecha_inicio = models.DateField(default= get_default_start_date)  # Fecha de inicio de reserva
    fecha_fin = models.DateField(default= get_default_end_date)  # Fecha de fin de reserva

    def __str__(self):
        return self.product.product_name

    def clean(self):
        """
        Valida que las fechas no se solapen para el mismo producto.
        """
        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")

        reservas_solapadas = OrderProduct.objects.filter(
            product=self.product,
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio,
            ordered=True
        ).exclude(pk=self.pk)

        if reservas_solapadas.exists():
            raise ValidationError(f"El producto {self.product.product_name} ya está reservado en las fechas seleccionadas.")

    def duracion(self):
        """
        Retorna la duración de la reserva en días.
        """
        return (self.fecha_fin - self.fecha_inicio).days