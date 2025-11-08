"""
Vistas API REST para el módulo de Catálogo de Productos
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Prefetch

from productos.models import LineaArticulo, GrupoArticulo, Articulo
from productos.serializers import (
    LineaArticuloSerializer,
    GrupoArticuloSerializer,
    ArticuloSerializer,
    ArticuloListSerializer,
    JerarquiaSerializer
)
from trading_system.choices import EstadoEntidades


class LineaArticuloViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Líneas de Artículos
    
    Endpoints:
    - GET /api/catalogo/lineas/ - Listar líneas
    - POST /api/catalogo/lineas/ - Crear línea
    - GET /api/catalogo/lineas/{id}/ - Obtener detalle
    - PUT/PATCH /api/catalogo/lineas/{id}/ - Actualizar línea
    - DELETE /api/catalogo/lineas/{id}/ - Soft delete (cambia estado a DE_BAJA)
    
    Filtros:
    - ?estado=1 (1=ACTIVO, 0=DE_BAJA)
    - ?search=bebidas (busca en nombre_linea y codigo_linea)
    """
    queryset = LineaArticulo.objects.all()
    serializer_class = LineaArticuloSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado']
    search_fields = ['nombre_linea', 'codigo_linea']
    ordering_fields = ['nombre_linea', 'codigo_linea', 'fecha_creacion']
    ordering = ['nombre_linea']
    lookup_field = 'linea_id'
    
    def list(self, request, *args, **kwargs):
        """Listar todas las líneas con respuesta estructurada"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Crear nueva línea de artículos"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Línea de artículo creada exitosamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Error al crear línea de artículo',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de una línea"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Actualizar línea de artículo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Línea de artículo actualizada exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Error al actualizar línea de artículo',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: cambia el estado a DE_BAJA en lugar de eliminar
        """
        instance = self.get_object()
        instance.estado = EstadoEntidades.DE_BAJA
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Línea de artículo desactivada exitosamente',
            'data': {
                'linea_id': str(instance.linea_id),
                'nombre_linea': instance.nombre_linea,
                'estado': instance.estado
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='activas')
    def activas(self, request):
        """Listar solo líneas activas"""
        lineas = self.get_queryset().filter(estado=EstadoEntidades.ACTIVO)
        serializer = self.get_serializer(lineas, many=True)
        return Response({
            'success': True,
            'count': lineas.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class GrupoArticuloViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Grupos de Artículos
    
    Endpoints:
    - GET /api/catalogo/grupos/ - Listar grupos
    - POST /api/catalogo/grupos/ - Crear grupo
    - GET /api/catalogo/grupos/{id}/ - Obtener detalle
    - PUT/PATCH /api/catalogo/grupos/{id}/ - Actualizar grupo
    - DELETE /api/catalogo/grupos/{id}/ - Soft delete
    
    Filtros:
    - ?linea={linea_id} (filtra por línea)
    - ?estado=1 (1=ACTIVO, 0=DE_BAJA)
    - ?search=lacteos (busca en nombre_grupo y codigo_grupo)
    """
    queryset = GrupoArticulo.objects.select_related('linea').all()
    serializer_class = GrupoArticuloSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'linea']
    search_fields = ['nombre_grupo', 'codigo_grupo']
    ordering_fields = ['nombre_grupo', 'codigo_grupo', 'fecha_creacion']
    ordering = ['codigo_grupo']
    lookup_field = 'grupo_id'
    
    def list(self, request, *args, **kwargs):
        """Listar todos los grupos con respuesta estructurada"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo grupo de artículos"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Grupo de artículo creado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Error al crear grupo de artículo',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de un grupo"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Actualizar grupo de artículo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Grupo de artículo actualizado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Error al actualizar grupo de artículo',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: cambia el estado a DE_BAJA en lugar de eliminar
        """
        instance = self.get_object()
        instance.estado = EstadoEntidades.DE_BAJA
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Grupo de artículo desactivado exitosamente',
            'data': {
                'grupo_id': str(instance.grupo_id),
                'nombre_grupo': instance.nombre_grupo,
                'estado': instance.estado
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='activos')
    def activos(self, request):
        """Listar solo grupos activos"""
        grupos = self.get_queryset().filter(estado=EstadoEntidades.ACTIVO)
        serializer = self.get_serializer(grupos, many=True)
        return Response({
            'success': True,
            'count': grupos.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='por-linea/(?P<linea_id>[^/.]+)')
    def por_linea(self, request, linea_id=None):
        """Obtener grupos por línea específica"""
        grupos = self.get_queryset().filter(linea_id=linea_id, estado=EstadoEntidades.ACTIVO)
        serializer = self.get_serializer(grupos, many=True)
        return Response({
            'success': True,
            'linea_id': linea_id,
            'count': grupos.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ArticuloViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Artículos
    
    Endpoints:
    - GET /api/catalogo/articulos/ - Listar artículos
    - POST /api/catalogo/articulos/ - Crear artículo
    - GET /api/catalogo/articulos/{id}/ - Obtener detalle
    - PUT/PATCH /api/catalogo/articulos/{id}/ - Actualizar artículo
    - DELETE /api/catalogo/articulos/{id}/ - Soft delete
    
    Filtros:
    - ?grupo={grupo_id} (filtra por grupo)
    - ?grupo_id__linea={linea_id} (filtra por línea a través del grupo)
    - ?search=coca (busca en descripcion y codigo_articulo)
    """
    queryset = Articulo.objects.select_related(
        'grupo_id',
        'grupo_id__linea'
    ).all()
    serializer_class = ArticuloSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'grupo_id', 'grupo_id__linea']
    search_fields = ['descripcion', 'codigo_articulo', 'codigo_barras']
    ordering_fields = ['descripcion', 'codigo_articulo', 'precio_sugerido', 'stock', 'fecha_creacion']
    ordering = ['codigo_articulo']
    lookup_field = 'articulo_id'
    
    def get_serializer_class(self):
        """
        Usa un serializador simplificado para listados
        """
        if self.action == 'list':
            return ArticuloListSerializer
        return ArticuloSerializer
    
    def list(self, request, *args, **kwargs):
        """Listar todos los artículos con respuesta estructurada"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo artículo"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Artículo creado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Error al crear artículo',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de un artículo"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Actualizar artículo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Artículo actualizado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Error al actualizar artículo',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: cambia el estado a DE_BAJA en lugar de eliminar
        """
        instance = self.get_object()
        instance.estado = EstadoEntidades.DE_BAJA
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Artículo desactivado exitosamente',
            'data': {
                'articulo_id': str(instance.articulo_id),
                'descripcion': instance.descripcion,
                'estado': instance.estado
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='activos')
    def activos(self, request):
        """Listar solo artículos activos"""
        articulos = self.get_queryset().filter(estado=EstadoEntidades.ACTIVO)
        serializer = ArticuloListSerializer(articulos, many=True)
        return Response({
            'success': True,
            'count': articulos.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='por-grupo/(?P<grupo_id>[^/.]+)')
    def por_grupo(self, request, grupo_id=None):
        """Obtener artículos por grupo específico"""
        articulos = self.get_queryset().filter(
            grupo_id=grupo_id,
            estado=EstadoEntidades.ACTIVO
        )
        serializer = ArticuloListSerializer(articulos, many=True)
        return Response({
            'success': True,
            'grupo_id': grupo_id,
            'count': articulos.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='jerarquia')
    def jerarquia(self, request):
        """
        Endpoint especial: GET /api/catalogo/articulos/jerarquia/
        
        Devuelve la estructura jerárquica completa:
        Líneas -> Grupos -> Artículos
        
        Optimizado con select_related y prefetch_related
        """
        # Optimización: prefetch de grupos y artículos
        grupos_prefetch = Prefetch(
            'grupo_linea',
            queryset=GrupoArticulo.objects.prefetch_related(
                Prefetch(
                    'grupo_articulo',
                    queryset=Articulo.objects.all()
                )
            )
        )
        
        # Obtener todas las líneas con sus grupos y artículos
        lineas = LineaArticulo.objects.prefetch_related(grupos_prefetch).all()
        
        # Serializar la jerarquía
        serializer = JerarquiaSerializer(lineas, many=True)
        
        return Response({
            'success': True,
            'message': 'Jerarquía completa del catálogo de productos',
            'total_lineas': lineas.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
