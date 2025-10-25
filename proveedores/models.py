from django.db import models

from trading_system.choices import *

class Proveedor(models.Model):
    proveedor_id = models.UUIDField(primary_key=True)
    ruc = models.CharField(max_length=11, null=False, unique=True)
    nombre_comercial = models.CharField(max_length=200, null=False)
    razon_social = models.CharField(max_length=200, null=False)
    direccion = models.CharField(max_length=300, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)

    def __str__(self):
        return self.nombre_comercial

    class Meta:
        db_table = 'proveedores'
        ordering = ["nombre_comercial"]