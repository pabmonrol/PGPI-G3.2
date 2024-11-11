from django.db import models
from barcos.models import Barco
from usuarios.models import PerfilUsuario

class Alquiler(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de pago'),
        ('PAGADO', 'Pagado'),
    ]
    barco = models.ForeignKey(Barco, on_delete=models.CASCADE)
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    fianza = models.DecimalField(max_digits=10, decimal_places=2)
    tarifa_combustible = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
