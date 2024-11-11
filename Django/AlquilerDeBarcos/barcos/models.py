from django.db import models

class CategoriaBarco(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()

class Barco(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(CategoriaBarco, on_delete=models.CASCADE)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='imagenes_barcos/')
    disponibilidad = models.BooleanField(default=True)
    tarifa_diaria = models.DecimalField(max_digits=10, decimal_places=2)
