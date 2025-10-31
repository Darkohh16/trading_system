from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from . import views, viewsets

# Router completo con documentación automática
router = DefaultRouter()
router.register(r'empresas', viewsets.EmpresaViewSet, basename='empresa')
router.register(r'sucursales', viewsets.SucursalViewSet, basename='sucursal')



urlpatterns = [
    # Incluir rutas del router
    path('', include(router.urls)),
    
    # ==================== RUTAS CON FBV (Function-Based Views) ====================
    # Empresas
    path('fbv/empresas/', views.empresa_list_create, name='fbv-empresa-list-create'),
    path('fbv/empresas/<int:pk>/', views.empresa_detail, name='fbv-empresa-detail'),
    path('fbv/empresas/<int:pk>/stats/', views.empresa_stats, name='fbv-empresa-stats'),
    
    # ==================== RUTAS CON CBV (Class-Based Views) ====================
    # Sucursales
    path('cbv/sucursales/', views.SucursalListCreateView.as_view(), name='cbv-sucursal-list-create'),
    path('cbv/sucursales/<int:pk>/', views.SucursalDetailView.as_view(), name='cbv-sucursal-detail'),
    
    # Empresas con Mixins
    path('cbv/empresas/list/', views.EmpresaListView.as_view(), name='cbv-empresa-list'),
    path('cbv/empresas/create/', views.EmpresaCreateView.as_view(), name='cbv-empresa-create'),
    
    # ==================== RUTAS PERSONALIZADAS ====================
    # Sucursales por empresa
    path('empresas/<int:empresa_id>/sucursales/', views.sucursales_por_empresa, name='sucursales-por-empresa'),
    
    # Creación masiva
    path('sucursales/bulk-create/', views.bulk_create_sucursales, name='bulk-create-sucursales'),
]
