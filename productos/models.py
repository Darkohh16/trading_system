from django.db import models
from trading_system.choices import EstadoEntidades, EstadoOrden


class LineaArticulo(models.Model):
    linea_id = models.UUIDField(primary_key=True)
    codigo_linea = models.CharField(max_length=10, null=False, blank=False)
    nombre_linea = models.CharField(max_length=150, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return self.nombre_linea

    class Meta:
        db_table = 'lineas_articulos'
        ordering = ["nombre_linea"]

class GrupoArticulo(models.Model):
    grupo_id = models.UUIDField(primary_key=True)
    codigo_grupo = models.CharField(max_length=5, null=False)
    nombre_grupo = models.CharField(max_length=150, null=False)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)
    linea = models.ForeignKey(LineaArticulo, on_delete=models.RESTRICT, null=False, related_name='grupo_linea')
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return self.nombre_grupo

    class Meta:
        db_table = 'grupos_articulos'
        ordering = ["codigo_grupo"]

class Articulo(models.Model):
    articulo_id = models.UUIDField(primary_key=True)
    codigo_articulo = models.CharField(max_length=10, null=False, blank=False)
    codigo_barras = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=200, null=False)
    stock = models.IntegerField(default=0)
    unidad_medida = models.CharField(max_length=20, null=False)
    costo_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_sugerido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grupo_id = models.ForeignKey(GrupoArticulo, on_delete=models.RESTRICT,null=False,related_name='grupo_articulo', db_column='grupo_id')
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)


    class Meta:
        db_table = 'articulos'
        ordering = ["codigo_articulo"]