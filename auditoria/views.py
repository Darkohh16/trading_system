from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone
from datetime import datetime, timedelta

from auditoria.models import HistorialPrecioArticulo, AuditoriaReglaPrecio, DescuentoProveedorAutorizado
from auditoria.serializers import (
    HistorialPrecioArticuloSerializer,
    AuditoriaReglaPrecioSerializer,
    DescuentoProveedorAutorizadoSerializer
)
from productos.models import Articulo
from precios.models import ReglaPrecio, ListaPrecio


class HistorialPrecioArticuloViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar el historial de cambios de precios
    """
    serializer_class = HistorialPrecioArticuloSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['fecha_cambio', 'precio_anterior', 'precio_nuevo']
    ordering = ['-fecha_cambio']

    def get_queryset(self):
        queryset = HistorialPrecioArticulo.objects.select_related(
            'articulo_id',
            'lista_precio',
            'usuario'
        ).all()
        
        # Filtros opcionales
        articulo_id = self.request.query_params.get('articulo_id')
        if articulo_id:
            queryset = queryset.filter(articulo_id=articulo_id)
        
        lista_precio_id = self.request.query_params.get('lista_precio_id')
        if lista_precio_id:
            queryset = queryset.filter(lista_precio_id=lista_precio_id)
        
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_cambio__gte=fecha)
            except ValueError:
                pass
        
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                # Incluir todo el día
                fecha = datetime.combine(fecha, datetime.max.time())
                queryset = queryset.filter(fecha_cambio__lte=fecha)
            except ValueError:
                pass
        
        return queryset

    @action(detail=False, methods=['get'], url_path='por-articulo/(?P<articulo_id>[^/.]+)')
    def por_articulo(self, request, articulo_id=None):
        """
        GET /api/auditoria/historial-precios/por-articulo/{articulo_id}/
        Obtiene el historial de precios para un artículo específico
        """
        try:
            articulo = Articulo.objects.get(pk=articulo_id)
        except Articulo.DoesNotExist:
            return Response(
                {'error': 'Artículo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = self.get_queryset().filter(articulo_id=articulo)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'articulo_id': str(articulo.articulo_id),
            'articulo_nombre': articulo.descripcion,
            'total_registros': queryset.count(),
            'historial': serializer.data
        })


class AuditoriaReglaPrecioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar la auditoría de reglas de precio
    """
    serializer_class = AuditoriaReglaPrecioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['fecha_cambio', 'accion']
    ordering = ['-fecha_cambio']

    def get_queryset(self):
        queryset = AuditoriaReglaPrecio.objects.select_related(
            'regla_precio',
            'usuario'
        ).all()
        
        # Filtros opcionales
        regla_precio_id = self.request.query_params.get('regla_precio_id')
        if regla_precio_id:
            queryset = queryset.filter(
                regla_precio_id=regla_precio_id
            ) | queryset.filter(
                regla_precio_id_backup=regla_precio_id
            )
        
        accion = self.request.query_params.get('accion')
        if accion:
            queryset = queryset.filter(accion=accion)
        
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_cambio__gte=fecha)
            except ValueError:
                pass
        
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                fecha = datetime.combine(fecha, datetime.max.time())
                queryset = queryset.filter(fecha_cambio__lte=fecha)
            except ValueError:
                pass
        
        return queryset

    @action(detail=False, methods=['get'], url_path='por-regla/(?P<regla_precio_id>[^/.]+)')
    def por_regla(self, request, regla_precio_id=None):
        """
        GET /api/auditoria/auditoria-reglas/por-regla/{regla_precio_id}/
        Obtiene la auditoría para una regla específica (incluye reglas eliminadas)
        """
        queryset = self.get_queryset().filter(
            regla_precio_id=regla_precio_id
        ) | self.get_queryset().filter(
            regla_precio_id_backup=regla_precio_id
        )
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Intentar obtener la regla si aún existe
        regla = None
        try:
            regla = ReglaPrecio.objects.get(pk=regla_precio_id)
            regla_nombre = regla.descripcion
            regla_codigo = regla.codigo
        except ReglaPrecio.DoesNotExist:
            # Si la regla fue eliminada, obtener info del primer registro de auditoría
            if queryset.exists():
                primer_registro = queryset.first()
                regla_nombre = primer_registro.codigo_regla or "Regla eliminada"
                regla_codigo = primer_registro.codigo_regla or "N/A"
            else:
                regla_nombre = "Regla no encontrada"
                regla_codigo = "N/A"
        
        return Response({
            'regla_precio_id': regla_precio_id,
            'regla_codigo': regla_codigo,
            'regla_nombre': regla_nombre,
            'regla_existe': regla is not None,
            'total_registros': queryset.count(),
            'auditoria': serializer.data
        })


class DescuentoProveedorAutorizadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar descuentos de proveedores autorizados
    """
    serializer_class = DescuentoProveedorAutorizadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['proveedor__nombre_comercial', 'proveedor__razon_social']
    ordering_fields = ['fecha_autorizacion', 'porcentaje_autorizado']
    ordering = ['-fecha_autorizacion']

    def get_queryset(self):
        queryset = DescuentoProveedorAutorizado.objects.select_related(
            'proveedor',
            'articulo',
            'grupo',
            'linea',
            'autorizado_por'
        ).all()
        
        # Filtros opcionales
        proveedor_id = self.request.query_params.get('proveedor_id')
        if proveedor_id:
            queryset = queryset.filter(proveedor_id=proveedor_id)
        
        articulo_id = self.request.query_params.get('articulo_id')
        if articulo_id:
            queryset = queryset.filter(articulo_id=articulo_id)
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtrar por vigencia
        vigente = self.request.query_params.get('vigente')
        if vigente and vigente.lower() == 'true':
            hoy = timezone.now().date()
            queryset = queryset.filter(
                estado=1,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            )
        
        return queryset

    def perform_create(self, serializer):
        """Establece el usuario que autoriza"""
        serializer.save(autorizado_por=self.request.user)

    @action(detail=False, methods=['get'], url_path='vigentes')
    def vigentes(self, request):
        """
        GET /api/auditoria/descuentos-proveedores/vigentes/
        Obtiene los descuentos vigentes en la fecha actual
        """
        hoy = timezone.now().date()
        queryset = self.get_queryset().filter(
            estado=1,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        )
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'fecha_consulta': hoy,
            'total_descuentos': queryset.count(),
            'descuentos': serializer.data
        })