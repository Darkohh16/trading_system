from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count
from .models import Empresa, Sucursal
from .serializers import (
    EmpresaListSerializer,
    EmpresaDetailSerializer,
    EmpresaCreateUpdateSerializer,
    EmpresaConSucursalesSerializer,
    EmpresaStatsSerializer,
    SucursalListSerializer,
    SucursalDetailSerializer,
    SucursalCreateUpdateSerializer,
)
from .pagination import StandardResultsSetPagination
from .filters import EmpresaFilter, SucursalFilter
from .permissions import IsAdminOrReadOnly


# Empresa ViewSet

class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Empresas.
    
    list: Lista todas las empresas
    create: Crea una nueva empresa
    retrieve: Obtiene detalle de una empresa
    update: Actualiza completamente una empresa
    partial_update: Actualiza parcialmente una empresa
    destroy: Desactiva una empresa (soft delete)
    """
    queryset = Empresa.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_class = EmpresaFilter
    search_fields = ['ruc', 'razon_social']
    ordering_fields = ['empresa_id', 'razon_social', 'fecha_creacion']
    ordering = ['-fecha_creacion']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return EmpresaListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmpresaCreateUpdateSerializer
        elif self.action == 'retrieve':
            return EmpresaDetailSerializer
        elif self.action == 'con_sucursales':
            return EmpresaConSucursalesSerializer
        elif self.action == 'estadisticas':
            return EmpresaStatsSerializer
        return EmpresaDetailSerializer
    
    def get_queryset(self):
        """Optimiza queries con select_related y prefetch_related"""
        queryset = super().get_queryset()
        
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('sucursales_empresa')
        
        # Filtros adicionales
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Sobrescribe create para respuesta personalizada"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'success': True,
                'message': 'Empresa creada exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Sobrescribe update para respuesta personalizada"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Empresa actualizada exitosamente',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete: desactiva en lugar de eliminar"""
        instance = self.get_object()
        from trading_system.choices import EstadoEntidades
        instance.estado = EstadoEntidades.INACTIVO
        instance.save()
        
        return Response(
            {
                'success': True,
                'message': 'Empresa desactivada exitosamente'
            },
            status=status.HTTP_200_OK
        )
    
    # Personalizadas
    
    @action(detail=True, methods=['get'])
    def con_sucursales(self, request, pk=None):
        """
        Obtiene empresa con todas sus sucursales anidadas
        GET /api/empresas/{id}/con_sucursales/
        """
        empresa = self.get_object()
        serializer = self.get_serializer(empresa)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """
        Obtiene estadísticas de la empresa
        GET /api/empresas/{id}/estadisticas/
        """
        empresa = self.get_object()
        serializer = self.get_serializer(empresa)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sucursales(self, request, pk=None):
        """
        Lista todas las sucursales de una empresa
        GET /api/empresas/{id}/sucursales/
        """
        empresa = self.get_object()
        sucursales = empresa.sucursales_empresa.all()
        
        # Filtro por estado
        estado = request.query_params.get('estado', None)
        if estado:
            sucursales = sucursales.filter(estado=estado)
        
        # Paginación
        page = self.paginate_queryset(sucursales)
        if page is not None:
            serializer = SucursalListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = SucursalListSerializer(sucursales, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activar(self, request, pk=None):
        """
        Activa una empresa desactivada
        POST /api/empresas/{id}/activar/
        """
        empresa = self.get_object()
        from trading_system.choices import EstadoEntidades
        
        if empresa.estado == EstadoEntidades.ACTIVO:
            return Response(
                {'message': 'La empresa ya está activa'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        empresa.estado = EstadoEntidades.ACTIVO
        empresa.save()
        
        return Response({
            'success': True,
            'message': 'Empresa activada exitosamente'
        })
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Lista solo empresas activas
        GET /api/empresas/activas/
        """
        from trading_system.choices import EstadoEntidades
        queryset = self.filter_queryset(
            self.get_queryset().filter(estado=EstadoEntidades.ACTIVO)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Búsqueda avanzada de empresas
        GET /api/empresas/buscar/?q=termino&estado=1
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'message': 'Debe proporcionar un término de búsqueda'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(ruc__icontains=query) |
            Q(razon_social__icontains=query) |
            Q(direccion__icontains=query) |
            Q(email__icontains=query)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Sucursal ViewSet

class SucursalViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Sucursales.
    
    list: Lista todas las sucursales
    create: Crea una nueva sucursal
    retrieve: Obtiene detalle de una sucursal
    update: Actualiza completamente una sucursal
    partial_update: Actualiza parcialmente una sucursal
    destroy: Desactiva una sucursal (soft delete)
    """
    queryset = Sucursal.objects.select_related('empresa').all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_class = SucursalFilter
    search_fields = ['codigo_sucursal', 'nombre_sucursal', 'ciudad', 'pais']
    ordering_fields = ['sucursal_id', 'codigo_sucursal', 'nombre_sucursal', 'fecha_creacion']
    ordering = ['codigo_sucursal']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return SucursalListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SucursalCreateUpdateSerializer
        elif self.action == 'retrieve':
            return SucursalDetailSerializer
        return SucursalDetailSerializer
    
    def get_queryset(self):
        """Filtros y optimizaciones"""
        queryset = super().get_queryset()
        
        # Filtrar por empresa
        empresa_id = self.request.query_params.get('empresa_id', None)
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        # Filtrar por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtrar por ciudad
        ciudad = self.request.query_params.get('ciudad', None)
        if ciudad:
            queryset = queryset.filter(ciudad__icontains=ciudad)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Sobrescribe create para respuesta personalizada"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'success': True,
                'message': 'Sucursal creada exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Sobrescribe update para respuesta personalizada"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Sucursal actualizada exitosamente',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete: desactiva en lugar de eliminar"""
        instance = self.get_object()
        from trading_system.choices import EstadoEntidades
        instance.estado = EstadoEntidades.INACTIVO
        instance.save()
        
        return Response(
            {
                'success': True,
                'message': 'Sucursal desactivada exitosamente'
            },
            status=status.HTTP_200_OK
        )
    
    # Personalizadas
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa una sucursal desactivada
        POST /api/sucursales/{id}/activar/
        """
        sucursal = self.get_object()
        from trading_system.choices import EstadoEntidades
        
        if sucursal.estado == EstadoEntidades.ACTIVO:
            return Response(
                {'message': 'La sucursal ya está activa'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sucursal.estado = EstadoEntidades.ACTIVO
        sucursal.save()
        
        return Response({
            'success': True,
            'message': 'Sucursal activada exitosamente'
        })
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Lista solo sucursales activas
        GET /api/sucursales/activas/
        """
        from trading_system.choices import EstadoEntidades
        queryset = self.filter_queryset(
            self.get_queryset().filter(estado=EstadoEntidades.ACTIVO)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_ciudad(self, request):
        """
        Agrupa sucursales por ciudad
        GET /api/sucursales/por_ciudad/
        """
        from django.db.models import Count
        
        ciudades = self.get_queryset().values('ciudad').annotate(
            total=Count('sucursal_id')
        ).order_by('-total')
        
        return Response(ciudades)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_create(self, request):
        """
        Crea múltiples sucursales en lote
        POST /api/sucursales/bulk_create/
        Body: [{"codigo_sucursal": "...", ...}, {...}]
        """
        if not isinstance(request.data, list):
            return Response(
                {'message': 'Se espera una lista de sucursales'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'success': True,
                'message': f'{len(serializer.data)} sucursales creadas exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Búsqueda avanzada de sucursales
        GET /api/sucursales/buscar/?q=termino
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'message': 'Debe proporcionar un término de búsqueda'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(codigo_sucursal__icontains=query) |
            Q(nombre_sucursal__icontains=query) |
            Q(ciudad__icontains=query) |
            Q(direccion__icontains=query) |
            Q(empresa__razon_social__icontains=query)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)