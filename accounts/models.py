from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager
from core.models import Sucursal
from trading_system.choices import AccesoSistema

# Create your models here.
class Usuario(AbstractUser):
    username = models.CharField(max_length=25, blank=False, null=False,
                                unique=True, primary_key=True)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    email = models.EmailField(unique=True, null=False)
    celular = models.CharField(max_length=11, blank=False, null=False)
    #sucursal = models.ForeignKey(Sucursal, on_delete=models.RESTRICT, null=False, related_name='usuarios_sucursal')
    perfil = models.IntegerField(choices=AccesoSistema, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    puede_aprobar_bajo_costo = models.BooleanField(default=False)
    ultimo_acceso = models.DateTimeField(auto_now=True, null=False)

    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.last_name