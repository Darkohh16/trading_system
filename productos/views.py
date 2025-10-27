"""
Vistas API REST para el módulo de Catálogo de Productos
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Prefetch

from productos.models import LineaArticulo, GrupoArticulo, Articulo
from api.serializers import (
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado']
    search_fields = ['nombre_linea', 'codigo_linea']
    ordering_fields = ['nombre_linea', 'codigo_linea', 'fecha_creacion']
    ordering = ['nombre_linea']
    lookup_field = 'linea_id'
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: cambia el estado a DE_BAJA en lugar de eliminar
        """
        instance = self.get_object()
        instance.estado = EstadoEntidades.DE_BAJA
        instance.save()
        
        return Response(
            {
                'message': 'Línea de artículo desactivada exitosamente',
                'linea_id': str(instance.linea_id),
                'nombre_linea': instance.nombre_linea,
                'estado': instance.estado
            },
            status=status.HTTP_200_OK
        )


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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'linea']
    search_fields = ['nombre_grupo', 'codigo_grupo']
    ordering_fields = ['nombre_grupo', 'codigo_grupo', 'fecha_creacion']
    ordering = ['codigo_grupo']
    lookup_field = 'grupo_id'
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: cambia el estado a DE_BAJA en lugar de eliminar
        """
        instance = self.get_object()
        instance.estado = EstadoEntidades.DE_BAJA
        instance.save()
        
        return Response(
            {
                'message': 'Grupo de artículo desactivado exitosamente',
                'grupo_id': str(instance.grupo_id),
                'nombre_grupo': instance.nombre_grupo,
                'estado': instance.estado
            },
            status=status.HTTP_200_OK
        )


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
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: cambia el estado a DE_BAJA en lugar de eliminar
        """
        instance = self.get_object()
        instance.estado = EstadoEntidades.DE_BAJA
        instance.save()
        
        return Response(
            {
                'message': 'Artículo desactivado exitosamente',
                'articulo_id': str(instance.articulo_id),
                'descripcion': instance.descripcion,
                'estado': instance.estado
            },
            status=status.HTTP_200_OK
        )
    
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
            'message': 'Jerarquía completa del catálogo de productos',
            'total_lineas': lineas.count(),
            'jerarquia': serializer.data
        }, status=status.HTTP_200_OK)
