from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrdenCompraClienteViawSet, CalcularPrecioArticuloView, SimularPedidoView

router = DefaultRouter()
router.register(r'ordenes', OrdenCompraClienteViawSet, basename='orden-compra')

urlpatterns = [
    path('', include(router.urls)),
    path('calcular-precio-articulo/', CalcularPrecioArticuloView.as_view(), name='calcular-precio-articulo'),
    path('simular-pedido/', SimularPedidoView.as_view(), name='simular-pedido'),
]
