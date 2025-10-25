from django.db import models
from trading_system.choices import EstadoOrden, EstadoEntidades


class Empresa(models.Model):
    empresa_id = models.AutoField(primary_key=True)
    ruc = models.CharField(max_length=11, null=False, unique=True)
    razon_social = models.CharField(max_length=200, null=False)
    direccion = models.CharField(max_length=300, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    sitio_web = models.URLField(max_length=200, null=True, blank=True)
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return self.nombre_empresa

    class Meta:
        db_table = 'empresas'
        ordering = ["razon_social"]

class Sucursal(models.Model):
    sucursal_id = models.AutoField(primary_key=True)
    codigo_sucursal = models.CharField(max_length=10, null=False, unique=True)
    nombre_sucursal = models.CharField(max_length=150, null=False)
    direccion = models.CharField(max_length=300, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    pais = models.CharField(max_length=100, null=True, blank=True)
    codigo_postal = models.CharField(max_length=20, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, null=False, related_name='sucursales_empresa')
    estado = models.IntegerField(choices=EstadoEntidades, default=EstadoEntidades.ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return self.nombre_sucursal

    class Meta:
        db_table = 'sucursales'
        ordering = ["codigo_sucursal"]