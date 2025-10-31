from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from productos.models import Articulo
from precios.models import CombinacionProducto
from precios.serializers.combinacion import *


class CombinacionProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = CombinacionProducto.objects.select_related(
            'lista_precio'
        ).prefetch_related(
            'detalles',
            'detalles__articulo',
            'detalles__grupo',
            'detalles__linea'
        ).all()

        #filtros
        lista_id = self.request.query_params.get('lista_precio')
        if lista_id:
            queryset = queryset.filter(lista_precio_id=lista_id)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.order_by('-fecha_creacion')

    def get_serializer_class(self):
        if self.action == 'list':
            return CombinacionProductoListaSerializer
        elif self.action == 'retrieve':
            return CombinacionProductoDetalleSerializer
        else:
            return CombinacionProductoCrearActualizarSerializer

    #combos activos
    @action(detail=False, methods=['get'], url_path='vigentes')
    def vigentes(self, request):
        """
        GET /api/combinaciones/vigentes/

        - lista_precio: ID de lista (opcional)
        - fecha: Fecha a validar (default: hoy)
        """
        lista_id = request.query_params.get('lista_precio')
        fecha_str = request.query_params.get('fecha')

        #fecha
        if fecha_str:
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            fecha = timezone.now().date()

        #filtrar
        queryset = self.get_queryset().filter(
            estado=1,
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha
        )

        if lista_id:
            queryset = queryset.filter(lista_precio_id=lista_id)

        serializer = CombinacionProductoListaSerializer(queryset, many=True)

        return Response({
            'fecha_consulta': fecha,
            'cantidad': queryset.count(),
            'combos': serializer.data
        })

    #validar items para combo
    @action(detail=True, methods=['post'], url_path='validar-items')
    def validar_items(self, request, pk=None):
        """
        POST /api/combinaciones/{id}/validar-items/

        Body:
        {
            "items": [
                {"articulo_id": "uuid-1", "cantidad": 2},
                {"articulo_id": "uuid-2", "cantidad": 1}
            ]
        }

        Valida si los items enviados cumplen el combo
        """
        combo = self.get_object()
        items_pedido = request.data.get('items', [])

        if not items_pedido:
            return Response(
                {'error': 'Debe enviar items para validar'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #detalles del combo
        detalles_combo = combo.detalles.all()

        cumple = True
        detalles_validacion = []

        for detalle in detalles_combo:
            #cuantos items del pedido cumplen
            cantidad_cumplida = 0

            for item in items_pedido:
                articulo_id = item.get('articulo_id')
                cantidad = item.get('cantidad', 0)

                #sgun tipo de item
                if detalle.tipo_item == 1:  #artículo específico
                    if str(detalle.articulo.articulo_id) == str(articulo_id):
                        cantidad_cumplida += cantidad

                elif detalle.tipo_item == 2:  #grupo
                    try:
                        articulo = Articulo.objects.get(pk=articulo_id)
                        if articulo.grupo == detalle.grupo:
                            cantidad_cumplida += cantidad
                    except Articulo.DoesNotExist:
                        pass

                elif detalle.tipo_item == 3:  #linea
                    try:
                        articulo = Articulo.objects.get(pk=articulo_id)
                        if articulo.grupo.linea == detalle.linea:
                            cantidad_cumplida += cantidad
                    except Articulo.DoesNotExist:
                        pass

            #cumple
            cumple_detalle = cantidad_cumplida >= detalle.cantidad_requerida

            if not cumple_detalle:
                cumple = False

            detalles_validacion.append({
                'detalle_id': str(detalle.detalle_combinacion_id),
                'tipo_item': detalle.get_tipo_item_display(),
                'cantidad_requerida': detalle.cantidad_requerida,
                'cantidad_cumplida': cantidad_cumplida,
                'cumple': cumple_detalle
            })

        return Response({
            'combo_id': str(combo.combinacion_id),
            'combo_nombre': combo.nombre,
            'cumple_combo': cumple,
            'tipo_beneficio': combo.get_tipo_beneficio_display(),
            'valor_beneficio': combo.valor_beneficio,
            'detalles': detalles_validacion
        })