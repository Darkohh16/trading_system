from django.contrib import admin
from .models import Cliente, HistorialCompra

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_comercial', 'razon_social', 'nro_documento', 'telefono', 'canal', 'fecha_creacion')
    search_fields = ('nombre_comercial', 'nro_documento', 'razon_social')
    list_filter = ('canal',)

@admin.register(HistorialCompra)
class HistorialCompraAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_compra', 'total')
    list_filter = ('fecha_compra',)
