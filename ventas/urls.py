from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ventas.views import OrdenViewSet, CalcularPrecioArticuloAPIView, EstadisticasGeneralesAPIView # EstadisticasGeneralesAPIView will be added next

router = DefaultRouter()
router.register(r'ordenes', OrdenViewSet, basename='orden')

urlpatterns = [
    path('', include(router.urls)),
    path('calcular-precio-articulo/', CalcularPrecioArticuloAPIView.as_view(), name='calcular_precio_articulo'),
    path('estadisticas/', EstadisticasGeneralesAPIView.as_view(), name='estadisticas_ventas'), # Will be implemented next
]
