import uuid
from django.db import models
from trading_system.choices import *

class Cliente(models.Model):
    cliente_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nro_documento = models.CharField(max_length=20, null=False, unique=True)
    nombre_comercial = models.CharField(max_length=200, null=False)
    razon_social = models.CharField(max_length=200, null=False)
    direccion = models.CharField(max_length=300, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)
    canal = models.IntegerField(choices=CanalVenta, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return self.nombre_comercial

    class Meta:
        db_table = 'clientes'
        ordering = ["nombre_comercial"]


class HistorialCompra(models.Model):
    historial_id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='historial')
    fecha_compra = models.DateField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField()

    def __str__(self):
        return f"Compra de {self.cliente.nombre_comercial} el {self.fecha_compra}"

    class Meta:
        db_table = 'historial_compras'
        ordering = ['-fecha_compra']

