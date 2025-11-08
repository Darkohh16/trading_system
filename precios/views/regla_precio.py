from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from precios.models import ReglaPrecio
from precios.serializers.regla_precio import ReglaPrecioSerializer
from auditoria.signals import set_current_user


class ReglaPrecioViewSet(viewsets.ModelViewSet):
    serializer_class = ReglaPrecioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ReglaPrecio.objects.select_related(
            'lista_precio',
            'aplica_linea',
            'aplica_grupo',
            'aplica_articulo'
        ).all()

        lista_id = self.request.query_params.get('lista_precio')
        if lista_id:
            queryset = queryset.filter(lista_precio_id=lista_id)

        tipo_regla = self.request.query_params.get('tipo_regla')
        if tipo_regla:
            queryset = queryset.filter(tipo_regla=tipo_regla)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.order_by('prioridad', '-fecha_creacion')

    def perform_create(self, serializer):
        """Establece el contexto de auditoría antes de crear"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        """Establece el contexto de auditoría antes de actualizar"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        """Establece el contexto de auditoría antes de eliminar"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        instance.delete()

    @action(detail=False, methods=['get'], url_path='activas')
    def activas(self, request):
        """
        GET /api/reglas/activas/

        - lista_precio: ID de lista (requerido)
        - fecha: Fecha a validar (default: hoy) formato YYYY-MM-DD

        Retorna reglas activas y vigentes en la fecha especificada
        """
        lista_id = request.query_params.get('lista_precio')
        fecha_str = request.query_params.get('fecha')

        if not lista_id:
            return Response(
                {'error': 'El parámetro lista_precio es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #fecha a validar
        if fecha_str:
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            fecha = timezone.now().date()

        #reglas activas
        queryset = self.get_queryset().filter(
            lista_precio_id=lista_id,
            estado=1,
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha
        ).order_by('prioridad')

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'fecha_consulta': fecha,
            'cantidad': queryset.count(),
            'reglas': serializer.data
        })

    #activar regla
    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        """POST /api/reglas/{id}/activar/"""
        if request.user.is_authenticated:
            set_current_user(request.user)
        regla = self.get_object()
        regla.estado = 1
        regla.save()

        serializer = self.get_serializer(regla)
        return Response(serializer.data)

    #desactivar regla
    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, pk=None):
        """POST /api/reglas/{id}/desactivar/"""
        if request.user.is_authenticated:
            set_current_user(request.user)
        regla = self.get_object()
        regla.estado = 0
        regla.save()

        serializer = self.get_serializer(regla)
        return Response(serializer.data)