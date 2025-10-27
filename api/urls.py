"""
URLs para la API REST del sistema de Trading
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.views import (
    LineaArticuloViewSet,
    GrupoArticuloViewSet,
    ArticuloViewSet
)

# Router de Django REST Framework
router = DefaultRouter()

# Registro de ViewSets del módulo Catálogo de Productos
router.register(r'catalogo/lineas', LineaArticuloViewSet, basename='linea-articulo')
router.register(r'catalogo/grupos', GrupoArticuloViewSet, basename='grupo-articulo')
router.register(r'catalogo/articulos', ArticuloViewSet, basename='articulo')

# Patrón de URLs
urlpatterns = [
    path('', include(router.urls)),
]
