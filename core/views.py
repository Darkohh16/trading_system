from rest_framework import status, generics, mixins
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from .models import Empresa, Sucursal
from .serializers import (
    EmpresaListSerializer,
    EmpresaDetailSerializer,
    EmpresaCreateUpdateSerializer,
    SucursalListSerializer,
    SucursalDetailSerializer,
    SucursalCreateUpdateSerializer,
    EmpresaStatsSerializer
)
from .pagination import StandardResultsSetPagination
from .filters import EmpresaFilter, SucursalFilter


# ==================== VISTAS BASADAS EN FUNCIONES (FBV) ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def empresa_list_create(request):
    """
    GET: Lista todas las empresas con filtros opcionales
    POST: Crea una nueva empresa
    """
    if request.method == 'GET':
        # Filtrado
        queryset = Empresa.objects.all()
        
        # Búsqueda por query params
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(ruc__icontains=search) |
                Q(razon_social__icontains=search)
            )
        
        # Filtro por estado
        estado = request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Paginación
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = EmpresaListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        serializer = EmpresaListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = EmpresaCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Empresa creada exitosamente',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                'message': 'Error al crear empresa',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def empresa_detail(request, pk):
    """
    GET: Obtiene detalle de una empresa
    PUT/PATCH: Actualiza una empresa
    DELETE: Elimina (desactiva) una empresa
    """
    try:
        empresa = Empresa.objects.get(pk=pk)
    except Empresa.DoesNotExist:
        return Response(
            {'message': 'Empresa no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = EmpresaDetailSerializer(empresa, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = EmpresaCreateUpdateSerializer(
            empresa,
            data=request.data,
            partial=partial
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Empresa actualizada exitosamente',
                'data': serializer.data
            })
        return Response(
            {
                'message': 'Error al actualizar empresa',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    elif request.method == 'DELETE':
        # Soft delete: cambiar estado a inactivo
        from trading_system.choices import EstadoEntidades
        empresa.estado = EstadoEntidades.INACTIVO
        empresa.save()
        return Response(
            {'message': 'Empresa desactivada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def empresa_stats(request, pk):
    """Obtiene estadísticas de una empresa"""
    try:
        empresa = Empresa.objects.get(pk=pk)
    except Empresa.DoesNotExist:
        return Response(
            {'message': 'Empresa no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = EmpresaStatsSerializer(empresa)
    return Response(serializer.data)


# ==================== VISTAS BASADAS EN CLASES (CBV) ====================

class SucursalListCreateView(generics.ListCreateAPIView):
    """
    GET: Lista todas las sucursales
    POST: Crea una nueva sucursal
    """
    queryset = Sucursal.objects.select_related('empresa').all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_class = SucursalFilter
    search_fields = ['codigo_sucursal', 'nombre_sucursal', 'ciudad']
    ordering_fields = ['codigo_sucursal', 'nombre_sucursal', 'fecha_creacion']
    ordering = ['codigo_sucursal']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SucursalCreateUpdateSerializer
        return SucursalListSerializer
    
    def get_queryset(self):
        """Filtros adicionales"""
        queryset = super().get_queryset()
        
        # Filtrar por empresa
        empresa_id = self.request.query_params.get('empresa_id', None)
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        # Filtrar por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Sucursal creada exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class SucursalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Obtiene detalle de una sucursal
    PUT/PATCH: Actualiza una sucursal
    DELETE: Elimina (desactiva) una sucursal
    """
    queryset = Sucursal.objects.select_related('empresa').all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SucursalCreateUpdateSerializer
        return SucursalDetailSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Sucursal actualizada exitosamente',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete"""
        instance = self.get_object()
        from trading_system.choices import EstadoEntidades
        instance.estado = EstadoEntidades.INACTIVO
        instance.save()
        
        return Response(
            {'message': 'Sucursal desactivada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# ==================== VISTAS CON MIXINS ====================

class EmpresaListView(mixins.ListModelMixin, generics.GenericAPIView):
    """Vista usando Mixins para listar empresas"""
    queryset = Empresa.objects.all()
    serializer_class = EmpresaListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_class = EmpresaFilter
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class EmpresaCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    """Vista usando Mixins para crear empresas"""
    queryset = Empresa.objects.all()
    serializer_class = EmpresaCreateUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# ==================== VISTAS PERSONALIZADAS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sucursales_por_empresa(request, empresa_id):
    """Obtiene todas las sucursales de una empresa específica"""
    try:
        empresa = Empresa.objects.get(pk=empresa_id)
    except Empresa.DoesNotExist:
        return Response(
            {'message': 'Empresa no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    sucursales = empresa.sucursales_empresa.all()
    
    # Filtro por estado
    estado = request.query_params.get('estado', None)
    if estado:
        sucursales = sucursales.filter(estado=estado)
    
    serializer = SucursalListSerializer(sucursales, many=True, context={'request': request})
    return Response({
        'empresa': {
            'empresa_id': empresa.empresa_id,
            'ruc': empresa.ruc,
            'razon_social': empresa.razon_social
        },
        'total_sucursales': sucursales.count(),
        'sucursales': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_sucursales(request):
    """Crea múltiples sucursales en una sola petición"""
    if not isinstance(request.data, list):
        return Response(
            {'message': 'Se espera una lista de sucursales'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = SucursalCreateUpdateSerializer(data=request.data, many=True)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'message': f'{len(serializer.data)} sucursales creadas exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(
        {
            'message': 'Error al crear sucursales',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )