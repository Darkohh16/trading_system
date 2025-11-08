import uuid
from django.db import models

from trading_system.choices import EstadoOrden, EstadoEntidades, AccionAuditoria


class HistorialPrecioArticulo(models.Model):
    historial_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        verbose_name = "Historial de Precio de Artículo"
        verbose_name_plural = "Historial de Precios de Artículos"

    def __str__(self):
        return f"Historial {self.articulo_id.descripcion} - {self.fecha_cambio}"

class DescuentoProveedorAutorizado(models.Model):
    descuento_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        verbose_name = "Descuento de Proveedor Autorizado"
        verbose_name_plural = "Descuentos de Proveedores Autorizados"

    def __str__(self):
        return f"Descuento {self.proveedor.nombre_comercial} - {self.porcentaje_autorizado}%"

class AuditoriaReglaPrecio(models.Model):
    auditoria_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    regla_precio = models.ForeignKey('precios.ReglaPrecio', on_delete=models.SET_NULL, null=True, blank=True, related_name='auditorias')
    regla_precio_id_backup = models.UUIDField(null=True, blank=True, help_text="ID de la regla eliminada")
    codigo_regla = models.CharField(max_length=10, null=True, blank=True, help_text="Código de la regla para referencia")
    accion = models.IntegerField(choices=AccionAuditoria, null=False)
    valor_anterior = models.JSONField(null=True, blank=True)
    valor_nuevo = models.JSONField(null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True, null=False)
    usuario = models.ForeignKey('accounts.Usuario', on_delete=models.RESTRICT, null=False)

    class Meta:
        db_table = 'auditoria_reglas_precios'
        ordering = ["-fecha_cambio"]
        verbose_name = "Auditoría de Regla de Precio"
        verbose_name_plural = "Auditorías de Reglas de Precios"

    def __str__(self):
        return f"Auditoría {self.regla_precio.codigo} - {self.get_accion_display()} - {self.fecha_cambio}"