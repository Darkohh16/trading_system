from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProveedorViewSet

# Crear el router
router = DefaultRouter()
router.register(r'proveedores', ProveedorViewSet, basename='proveedor')

# URLs
urlpatterns = [
    path('', include(router.urls)),
]