from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Router para ViewSet de usuarios
router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')

urlpatterns = [
    # Autenticación y Gestión de Tokens
    # Login - Obtener tokens
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Refresh - Obtener nuevo access token
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Logout - Blacklist del token
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Perfil del usuario autenticado
    path('auth/perfil/', views.perfil_view, name='perfil'),
    
    # Gestión de usuarios
    # Incluir rutas del ViewSet
    # GET    /api/usuarios/           -> Listar usuarios
    # POST   /api/usuarios/           -> Crear usuario
    # GET    /api/usuarios/{username}/-> Detalle usuario
    # PUT    /api/usuarios/{username}/-> Actualizar usuario
    # PATCH  /api/usuarios/{username}/-> Actualizar parcial
    # DELETE /api/usuarios/{username}/-> Desactivar usuario
    path('', include(router.urls)),
]