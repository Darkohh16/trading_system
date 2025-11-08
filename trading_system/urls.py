from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
  
    # Endpoints principales de la API
    path('api/', include('precios.urls')),
    path('api/', include('core.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('clientes.urls')),
    path('api/', include('proveedores.urls')),
    path('api/', include('productos.urls')),
    path('api/', include('ventas.urls')),
    path('api/auditoria/', include('auditoria.urls')),

    # Endpoints de autenticación JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
