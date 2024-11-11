from django.contrib.auth.models import User
from django.db import models

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    correo = models.EmailField()
    es_cliente = models.BooleanField(default=True)

