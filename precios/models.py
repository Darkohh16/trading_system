from django.db import models

from trading_system.choices import Tipo, CanalVenta, Moneda, EstadoOrden, EstadoEntidades, TipoRegla, TipoDescuento, \
    TipoBeneficio, TipoItem


class ListaPrecio(models.Model):
    lista_precio_id = models.UUIDField(primary_key=True)
    empresa = models.ForeignKey('core.Empresa', on_delete=models.RESTRICT, null=False, related_name='listas_precios_empresa')
    sucursal = models.ForeignKey('core.Sucursal', on_delete=models.RESTRICT, null=False, related_name='listas_precios_sucursal')
    codigo = models.CharField(max_length=10, null=False, unique=True)
    nombre = models.CharField(max_length=150, null=False)
    tipo = models.IntegerField(choices=Tipo, null=False)
    canal = models.IntegerField(choices=CanalVenta, null=False)
    tipo_moneda = models.IntegerField(choices=Moneda, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO, null=False)
    modificado_por = models.ForeignKey('accounts.Usuario', on_delete=models.RESTRICT, null=False)
    fecha_vigencia_inicio = models.DateField(null=False)
    fecha_vigencia_fin = models.DateField(null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'listas_precios'
        ordering = ['codigo']

class PrecioArticulo(models.Model):
    precio_articulo_id = models.UUIDField(primary_key=True)
    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.RESTRICT, null=False, related_name='precios_articulos_lista')
    articulo = models.ForeignKey('productos.Articulo', on_delete=models.RESTRICT, null=False, related_name='precios_articulos_articulo')
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    precio_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.articulo.descripcion} - {self.precio_unitario}"

    class Meta:
        db_table = 'precios_articulos'
        unique_together = ('lista_precio', 'articulo')
        ordering = ['articulo__codigo_articulo']

class ReglaPrecio(models.Model):
    regla_precio_id = models.UUIDField(primary_key=True)
    codigo = models.CharField(max_length=10, null=False, unique=True)
    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.RESTRICT, null=False, related_name='reglas_precios_lista')
    tipo_regla = models.IntegerField(choices=TipoRegla, null=False)
    #----------------------------------------------------------
    prioridad = models.IntegerField(null=False, default=1)
    aplica_canal = models.CharField(max_length=50, null=True, blank=True)
    aplica_linea = models.ForeignKey('productos.LineaArticulo', on_delete=models.RESTRICT, null=True, blank=True, related_name='regla_precio_linea')
    aplica_grupo = models.ForeignKey('productos.GrupoArticulo', on_delete=models.RESTRICT, null=True, blank=True, related_name='regla_precio_grupo')
    aplica_articulo = models.ForeignKey('productos.Articulo', on_delete=models.RESTRICT, null=True, blank=True, related_name='regla_precio_articulo')
    #----------------------------------------------------------
    cantidad_minima = models.IntegerField(null=True, blank=True)
    monto_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_descuento = models.IntegerField(choices=TipoDescuento, null=False)
    valor_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    fecha_inicio = models.DateField(null=False)
    fecha_fin = models.DateField(null=False)
    descripcion = models.CharField(max_length=200, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.descripcion

    class Meta:
        db_table = 'reglas_precios'
        ordering = ['descripcion']

class CombinacionProducto(models.Model):
    combinacion_id = models.UUIDField(primary_key=True)
    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.RESTRICT, null=False, related_name='combinaciones_productos_lista')
    nombre = models.CharField(max_length=150, null=False)
    tipo_beneficio = models.IntegerField(choices=TipoBeneficio, null=False)
    valor_beneficio = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    fecha_inicio = models.DateField(null=False)
    fecha_fin = models.DateField(null=False)
    estado = models.IntegerField(choices=EstadoEntidades, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'combinaciones_productos'
        unique_together = ('lista_precio', 'nombre')
        ordering = ['nombre']

class DetalleCombinacionProducto(models.Model):
    detalle_combinacion_id = models.UUIDField(primary_key=True)
    combinacion_producto = models.ForeignKey(CombinacionProducto, on_delete=models.RESTRICT, null=False, related_name='detalles_combinacion_producto')
    tipo_item = models.IntegerField(choices=TipoItem, null=False)
    articulo = models.ForeignKey('productos.Articulo', on_delete=models.RESTRICT, null=True, blank=True, related_name='detalle_combinacion_articulo')
    grupo = models.ForeignKey('productos.GrupoArticulo', on_delete=models.RESTRICT, null=True, blank=True, related_name='detalle_combinacion_grupo')
    linea = models.ForeignKey('productos.LineaArticulo', on_delete=models.RESTRICT, null=True, blank=True, related_name='detalle_combinacion_linea')
    cantidad_requerida = models.IntegerField(default=1)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Detalle de {self.combinacion_producto.nombre} - Item: {self.articulo.descripcion if self.articulo else 'N/A'}"

    class Meta:
        db_table = 'detalles_combinaciones_productos'
        unique_together = ('combinacion_producto', 'articulo', 'grupo', 'linea')
        ordering = ['combinacion_producto__nombre']