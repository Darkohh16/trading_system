from django.urls import path, include
from rest_framework.routers import DefaultRouter

from auditoria.views import (
    HistorialPrecioArticuloViewSet,
    AuditoriaReglaPrecioViewSet,
    DescuentoProveedorAutorizadoViewSet
)

router = DefaultRouter()
router.register(r'historial-precios', HistorialPrecioArticuloViewSet, basename='historial-precio')
router.register(r'auditoria-reglas', AuditoriaReglaPrecioViewSet, basename='auditoria-regla')
router.register(r'descuentos-proveedores', DescuentoProveedorAutorizadoViewSet, basename='descuento-proveedor')

urlpatterns = [
    path('', include(router.urls)),
]
