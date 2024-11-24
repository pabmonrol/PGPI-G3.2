from datetime import date, timedelta
from django.db import models
from store.models import Product, Variation
from accounts.models import Account
from django.utils import timezone


# Create your models here.
class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    
def get_default_start_date():
    return timezone.now().date() + timedelta(days=1)

def get_default_end_date():
    return timezone.now().date() + timedelta(days=2)

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    fecha_inicio = models.DateField(default= get_default_start_date)  # Fecha de inicio de reserva
    fecha_fin = models.DateField(default= get_default_end_date)  # Fecha de fin de reserva
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.product.product_name

    def duracion(self):
        return (self.fecha_fin - self.fecha_inicio).days

    def sub_total(self):
        return self.product.price * (self.fecha_fin - self.fecha_inicio).days


    def __unicode__(self):
        return self.product
    