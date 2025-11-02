from django.db import models

from trading_system.choices import *


class OrdenCompraCliente(models.Model):
    orden_compra_cliente_id = models.UUIDField(primary_key=True)
    numero_orden = models.BigIntegerField(unique=True, null=False, auto_created=True)
    fecha_orden = models.DateField(auto_now_add=True, null=False)
    empresa = models.ForeignKey('core.Empresa', on_delete=models.RESTRICT, null=False, related_name='ordenes_compra_cliente_empresa')
    sucursal = models.ForeignKey('core.Sucursal', on_delete=models.RESTRICT, null=False, related_name='ordenes_compra_cliente_sucursal')
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.RESTRICT, null=False)
    vendedor = models.ForeignKey('accounts.Usuario', on_delete=models.RESTRICT, null=False)
    canal = models.IntegerField(choices=CanalVenta, null=False)
    lista_precio = models.ForeignKey('precios.ListaPrecio', on_delete=models.RESTRICT, null=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    descuento_total = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    estado = models.IntegerField(choices=EstadoOrden, default=EstadoOrden.PENDIENTE, null=False)

    def _str_(self):
        return f"Orden {self.numero_orden} - Cliente: {self.cliente.nombre_completo}"

    class Meta:
        db_table = 'ordenes_compra_cliente'
        ordering = ['-fecha_orden']

class DetalleOrdenCompraCliente(models.Model):
    detalle_orden_compra_cliente_id = models.UUIDField(primary_key=True)
    orden_compra_cliente = models.ForeignKey(OrdenCompraCliente, on_delete=models.RESTRICT, null=False, related_name='detalles_orden_compra_cliente')
    articulo = models.ForeignKey('productos.Articulo', on_delete=models.RESTRICT, null=False)
    cantidad = models.IntegerField(null=False)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    reglas_aplicadas = models.JSONField(null=True, blank=True)
    vendido_bajo_costo = models.BooleanField(default=False)
    total_item = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    def save(self, *args, **kwargs):
        # Calcular el total del item
        self.total_item = (self.cantidad * self.precio_unitario) - self.descuento
        super().save(*args, **kwargs)

        # Actualizar el total de la orden
        self.orden_compra_cliente.subtotal += self.cantidad * self.precio_unitario
        self.orden_compra_cliente.descuento_total += self.descuento
        self.orden_compra_cliente.total = self.orden_compra_cliente.subtotal - self.orden_compra_cliente.descuento_total
        self.orden_compra_cliente.save()

    def _str_(self):
        return f"{self.cantidad} x {self.articulo.descripcion}"

    class Meta:
        db_table = "detalles_ordenes_compra_cliente"
        ordering = ['-detalle_orden_compra_cliente_id']
