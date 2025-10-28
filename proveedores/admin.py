from django.contrib import admin
from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor_id', 'ruc', 'nombre_comercial', 'razon_social', 'email', 'telefono', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('ruc', 'nombre_comercial', 'razon_social', 'email')
    readonly_fields = ('proveedor_id', 'fecha_creacion', 'fecha_modificacion')
    ordering = ('nombre_comercial',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('proveedor_id', 'ruc', 'nombre_comercial', 'razon_social')
        }),
        ('Datos de Contacto', {
            'fields': ('direccion', 'telefono', 'email')
        }),
        ('Estado y Fechas', {
            'fields': ('estado', 'fecha_creacion', 'fecha_modificacion')
        }),
    )