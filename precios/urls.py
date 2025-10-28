from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from precios.views.lista_precio import *
from precios.views.regla_precio import *
from precios.views.combinacion import *
from precios.views.precio_articulo import *

# Router principal
router = DefaultRouter()

# Registrar ViewSets
router.register(r'listas', ListaPrecioViewSet, basename='lista-precio')
router.register(r'reglas', ReglaPrecioViewSet, basename='regla-precio')
router.register(r'combinaciones', CombinacionProductoViewSet, basename='combinacion')
router.register(r'precios-articulos', PrecioArticuloViewSet, basename='precio-articulo')

# Router anidado: /api/listas/{lista_pk}/precios/
listas_router = routers.NestedDefaultRouter(router, r'listas', lookup='lista')
listas_router.register(r'precios', ListaPrecioArticuloViewSet, basename='lista-precios')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(listas_router.urls)),
]
