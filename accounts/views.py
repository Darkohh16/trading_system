from rest_framework import status, generics, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    ChangePasswordSerializer,
    PerfilUsuarioSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para login con JWT"""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {
                    'success': False,
                    'message': 'Username y password son requeridos'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {
                    'success': False,
                    'message': 'Credenciales inválidas'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {
                    'success': False,
                    'message': 'Usuario inactivo'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        # Serializar información del usuario
        user_data = PerfilUsuarioSerializer(user).data
        
        return Response(
            {
                'success': True,
                'message': 'Login exitoso',
                'data': {
                    'user': user_data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }
            },
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout - Blacklist del refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response(
            {
                'success': True,
                'message': 'Logout exitoso'
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'message': 'Error al hacer logout',
                'error': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_view(request):
    """Obtener datos del usuario autenticado"""
    serializer = PerfilUsuarioSerializer(request.user)
    return Response(
        {
            'success': True,
            'data': serializer.data
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Cambiar contraseña del usuario autenticado"""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        # Cambiar contraseña
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {
                'success': True,
                'message': 'Contraseña actualizada exitosamente'
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {
            'success': False,
            'message': 'Error al cambiar contraseña',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios (solo admin)"""
    queryset = Usuario.objects.all().select_related('sucursal', 'sucursal__empresa')
    permission_classes = [IsAdminUser]
    lookup_field = 'username'
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        return UsuarioSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        sucursal_id = self.request.query_params.get('sucursal', None)
        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)
        
        perfil = self.request.query_params.get('perfil', None)
        if perfil:
            queryset = queryset.filter(perfil=perfil)
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'success': True,
                'message': 'Usuario creado exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(
            {
                'success': True,
                'message': 'Usuario actualizado exitosamente',
                'data': serializer.data
            }
        )
    
    def destroy(self, request, *args, **kwargs):
        """Desactivar usuario en lugar de eliminar"""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response(
            {
                'success': True,
                'message': 'Usuario desactivado exitosamente'
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def activar(self, request, username=None):
        """Activar un usuario desactivado"""
        usuario = self.get_object()
        usuario.is_active = True
        usuario.save()
        
        return Response(
            {
                'success': True,
                'message': 'Usuario activado exitosamente'
            }
        )
    
    @action(detail=False, methods=['get'])
    def vendedores(self, request):
        """Listar solo vendedores"""
        from trading_system.choices import AccesoSistema
        vendedores = self.get_queryset().filter(perfil=AccesoSistema.VENDEDOR)
        serializer = self.get_serializer(vendedores, many=True)
        return Response(serializer.data)
