from django.contrib import admin
from auditoria.models import (
    HistorialPrecioArticulo,
    AuditoriaReglaPrecio,
    DescuentoProveedorAutorizado
)


@admin.register(HistorialPrecioArticulo)
class HistorialPrecioArticuloAdmin(admin.ModelAdmin):
    list_display = (
        'historial_id',
        'articulo_id',
        'lista_precio',
        'precio_anterior',
        'precio_nuevo',
        'usuario',
        'fecha_cambio',
    )
    list_filter = ('fecha_cambio', 'lista_precio')
    search_fields = ('articulo_id__descripcion', 'articulo_id__codigo_articulo', 'motivo')
    readonly_fields = ('historial_id', 'fecha_cambio')
    date_hierarchy = 'fecha_cambio'
    ordering = ('-fecha_cambio',)


@admin.register(AuditoriaReglaPrecio)
class AuditoriaReglaPrecioAdmin(admin.ModelAdmin):
    list_display = (
        'auditoria_id',
        'regla_precio',
        'codigo_regla',
        'accion',
        'usuario',
        'fecha_cambio',
    )
    list_filter = ('accion', 'fecha_cambio')
    search_fields = ('codigo_regla', 'regla_precio__codigo', 'regla_precio__descripcion')
    readonly_fields = ('auditoria_id', 'fecha_cambio', 'valor_anterior', 'valor_nuevo')
    date_hierarchy = 'fecha_cambio'
    ordering = ('-fecha_cambio',)


@admin.register(DescuentoProveedorAutorizado)
class DescuentoProveedorAutorizadoAdmin(admin.ModelAdmin):
    list_display = (
        'descuento_id',
        'proveedor',
        'articulo',
        'grupo',
        'linea',
        'porcentaje_autorizado',
        'fecha_inicio',
        'fecha_fin',
        'estado',
        'autorizado_por',
        'fecha_autorizacion',
    )
    list_filter = ('estado', 'fecha_autorizacion', 'proveedor')
    search_fields = (
        'proveedor__nombre_comercial',
        'articulo__descripcion',
        'grupo__nombre_grupo',
        'linea__nombre_linea'
    )
    readonly_fields = ('descuento_id', 'fecha_autorizacion')
    date_hierarchy = 'fecha_autorizacion'
    ordering = ('-fecha_autorizacion',)
