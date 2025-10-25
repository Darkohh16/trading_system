from django.db import models

from trading_system.choices import EstadoOrden, EstadoEntidades, AccionAuditoria


class HistorialPrecioArticulo(models.Model):
    historial_id = models.UUIDField(primary_key=True)
    articulo_id = models.ForeignKey('productos.Articulo', on_delete=models.RESTRICT, null=False, related_name='articulo_historial', db_column='articulo_id')
    lista_precio = models.ForeignKey('precios.ListaPrecio', on_delete=models.RESTRICT, null=False)
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    precio_nuevo = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    fecha_cambio = models.DateTimeField(auto_now_add=True, null=False)
    usuario = models.ForeignKey('accounts.Usuario', on_delete=models.RESTRICT, null=False)
    motivo = models.TextField(null=False)

    class Meta:
        db_table = 'historial_precios_articulos'
        ordering = ["-fecha_cambio"]

class DescuentoProveedorAutorizado(models.Model):
    descuento_id = models.UUIDField(primary_key=True)
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.RESTRICT, null=False)
    articulo = models.ForeignKey('productos.Articulo', on_delete=models.RESTRICT, null=True, blank=True)
    grupo = models.ForeignKey('productos.GrupoArticulo', on_delete=models.RESTRICT, null=True, blank=True)
    linea = models.ForeignKey('productos.LineaArticulo', on_delete=models.RESTRICT, null=True, blank=True)
    porcentaje_autorizado = models.DecimalField(max_digits=5, decimal_places=2, null=False)
    fecha_inicio = models.DateField(null=False)
    fecha_fin = models.DateField(null=False)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO, null=False)
    autorizado_por = models.ForeignKey('accounts.Usuario', on_delete=models.RESTRICT, null=False)
    fecha_autorizacion = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        db_table = 'descuentos_proveedores_autorizados'
        ordering = ["-fecha_autorizacion"]

class AuditoriaReglaPrecio(models.Model):
    auditoria_id = models.UUIDField(primary_key=True)
    regla_precio = models.ForeignKey('precios.ReglaPrecio', on_delete=models.RESTRICT, null=False)
    accion = models.IntegerField(choices=AccionAuditoria, null=False)
    valor_anterior = models.JSONField(null=True, blank=True)
    valor_nuevo = models.JSONField(null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True, null=False)
    usuario = models.ForeignKey('accounts.Usuario', on_delete=models.RESTRICT, null=False)

    class Meta:
        db_table = 'auditoria_reglas_precios'
        ordering = ["-fecha_cambio"]