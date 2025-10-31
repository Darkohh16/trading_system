from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone
from datetime import datetime

from precios.models import ListaPrecio
from precios.serializers.lista_precio import *
from precios.filters import ListaPrecioFilter

class ListaPrecioViewSet(viewsets.ModelViewSet):
    """
        ViewSet para gestionar listas de precios

        Endpoints generados automáticamente:
        - GET    /api/listas/          -> list()
        - POST   /api/listas/          -> create()
        - GET    /api/listas/{id}/     -> retrieve()
        - PUT    /api/listas/{id}/     -> update()
        - PATCH  /api/listas/{id}/     -> partial_update()
        - DELETE /api/listas/{id}/     -> destroy()
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ListaPrecioFilter
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['fecha_vigencia_inicio', 'fecha_creacion', 'nombre']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        return ListaPrecio.objects.select_related(
            'empresa',
            'sucursal',
            'modificado_por'
        ).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ListaPrecioSerializer
        elif self.action == 'retrieve':
            return ListaPrecioDetalleSerializer
        else:
            return ListaPrecioCrearActualizarSerializer

    @action(detail=False, methods=['get'], url_path='vigentes')
    def vigentes(self, request):
        """
            GET /api/listas/vigentes/
            Retorna las listas de precios vigentes

            - empresa id
            - sucursal id (opcional)
            - canal de venta (opcional)
            - fecha (opcional, por defecto hoy)
        """

        empresa_id = request.query_params.get('empresa')
        sucursal_id = request.query_params.get('sucursal')
        canal = request.query_params.get('canal')
        fecha_str = request.query_params.get('fecha')

        #empresa necesaria
        if not empresa_id:
            return Response({'error': 'empresa id required'}, status=status.HTTP_400_BAD_REQUEST)

        #fechas a validar
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha invalido, usa YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            fecha = timezone.now().date()

        #listas vigentes
        queryset = self.get_queryset().filter(
            empresa_id=empresa_id,
            estado=1,
            fecha_vigencia_inicio__lte=fecha,
            fecha_vigencia_fin__gte=fecha
        )

        #opcionales
        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)
        if canal:
            queryset = queryset.filter(canal=canal)

        serializer = ListaPrecioSerializer(queryset, many=True)

        return Response({
            'fecha_consulta': fecha,
            'cantidad': queryset.count(),
            'listas': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """
            DELETE /api/listas/{id}/
            En realidad es un soft delete, no borramos historico, solo se cambia a inactiva
        """
        instancia = self.get_object()
        instancia.estado = 0
        instancia.save()

        return Response(
            {'message': 'Lista desactivada correctamente.'},
            status=status.HTTP_200_OK
        )