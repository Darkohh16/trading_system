from django.urls import path
from .views import ProveedorViewSet

proveedor_list = ProveedorViewSet.as_view({'get': 'listar'})
proveedor_create = ProveedorViewSet.as_view({'post': 'crear'})
proveedor_detail = ProveedorViewSet.as_view({'get': 'detalle'})
proveedor_update = ProveedorViewSet.as_view({'put': 'actualizar', 'patch': 'actualizar'})
proveedor_delete = ProveedorViewSet.as_view({'delete': 'eliminar'})


urlpatterns = [
    path('proveedores/listar/', proveedor_list, name='proveedor-listar'),
    path('proveedores/crear/', proveedor_create, name='proveedor-crear'),
    path('proveedores/detalle/<uuid:pk>/', proveedor_detail, name='proveedor-detalle'),
    path('proveedores/actualizar/<uuid:pk>/', proveedor_update, name='proveedor-actualizar'),
    path('proveedores/eliminar/<uuid:pk>/', proveedor_delete, name='proveedor-eliminar'),
]
