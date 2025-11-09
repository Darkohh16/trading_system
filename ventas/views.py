from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404, Http404
from django.http import Http404
from django.utils import timezone
from django.db.models import Sum, Count
from decimal import Decimal

from ventas.models import OrdenCompraCliente, DetalleOrdenCompraCliente
from productos.models import *
from precios.models import *
from ventas.serializers import (
    OrdenReadSerializer, OrdenWriteSerializer,
    DetalleOrdenWriteSerializer, ArticuloPrecioCalculateSerializer
)
from trading_system.choices import EstadoOrden
from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdminOrReadOnly
from ventas.permissions import CanApproveLowCostSale
from auditoria.utils import auditoria_context
from .utils import calculate_price

# from precios.utils import calcular_precio_articulo_con_reglas

class OrdenViewSet(viewsets.ModelViewSet):
    queryset = OrdenCompraCliente.objects.all().order_by('-fecha_orden')
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrdenWriteSerializer
        return OrdenReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            orden = serializer.save()

        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.estado != EstadoOrden.PENDIENTE:
            return Response(
                {"detail": "Solo se pueden actualizar órdenes en estado PENDIENTE."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        orden = serializer.save()
        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


    @action(detail=True, methods=['post'], url_path='confirmar')
    def confirmar_orden(self, request, pk=None):
        orden = self.get_object()
        if orden.estado != EstadoOrden.PENDIENTE:
            return Response(
                {"detail": "Solo se pueden confirmar órdenes en estado PENDIENTE."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            for detalle in orden.detalles_orden_compra_cliente.all():
                if detalle.cantidad > detalle.articulo.stock:
                    return Response(
                        {"detail": f"Stock insuficiente para el artículo {detalle.articulo.descripcion}. Stock disponible: {detalle.articulo.stock}, solicitado: {detalle.cantidad}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            for detalle in orden.detalles_orden_compra_cliente.all():
                articulo = detalle.articulo
                articulo.stock -= detalle.cantidad
                articulo.save(update_fields=['stock'])

            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} confirmada"):
                orden.estado = EstadoOrden.PROCESANDO
                orden.save()
                print(f"AUDIT: User {request.user.username} confirmed order {orden.orden_compra_cliente_id}. New state: {orden.get_estado_display()}")

        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='anular')
    def anular_orden(self, request, pk=None):
        orden = self.get_object()
        estado_original = orden.estado

        if estado_original not in [EstadoOrden.PENDIENTE, EstadoOrden.PROCESANDO]:
            return Response(
                {"detail": "Solo se pueden anular órdenes en estado PENDIENTE o PROCESANDO."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            if estado_original == EstadoOrden.PROCESANDO:
                for detalle in orden.detalles_orden_compra_cliente.all():
                    articulo = detalle.articulo
                    articulo.stock += detalle.cantidad
                    articulo.save(update_fields=['stock'])

            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} anulada"):
                orden.estado = EstadoOrden.CANCELADA
                orden.save()
                print(f"AUDIT: User {request.user.username} cancelled order {orden.orden_compra_cliente_id}. New state: {orden.get_estado_display()}")

        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='marcar-como-facturada')
    def marcar_como_facturada(self, request, pk=None):
        orden = self.get_object()
        if orden.estado != EstadoOrden.PROCESANDO:
            return Response(
                {"detail": "Solo se pueden marcar como facturadas órdenes en estado PROCESANDO."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} marcada como facturada"):
                orden.estado = EstadoOrden.COMPLETADA
                orden.save()
                print(f"AUDIT: User {request.user.username} marked order {orden.orden_compra_cliente_id} as invoiced. New state: {orden.get_estado_display()}")

        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='anular-confirmada')
    def anular_orden_confirmada(self, request, pk=None):
        orden = self.get_object()
        if orden.estado != EstadoOrden.COMPLETADA:
            return Response(
                {"detail": "Solo se pueden anular órdenes confirmadas/completadas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        with transaction.atomic():
            for detalle in orden.detalles_orden_compra_cliente.all():
                articulo = detalle.articulo
                articulo.stock += detalle.cantidad
                articulo.save(update_fields=['stock'])

            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} confirmada anulada"):

                orden.estado = EstadoOrden.CANCELADA

                orden.save()

                print(f"AUDIT: User {request.user.username} cancelled confirmed order {orden.orden_compra_cliente_id}. New state: {orden.get_estado_display()}")

        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='aprobar-venta-bajo-costo', permission_classes=[IsAuthenticated, CanApproveLowCostSale])
    def aprobar_venta_bajo_costo(self, request, pk=None):
        orden = self.get_object()

        if not any(detalle.vendido_bajo_costo for detalle in orden.detalles_orden_compra_cliente.all()):
            return Response(
                {"detail": "La orden no contiene ítems vendidos bajo costo que requieran aprobación."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} aprobada bajo costo"):
                print(f"AUDIT: User {request.user.username} approved low-cost sale for order {orden.orden_compra_cliente_id}.")
        
        read_serializer = OrdenReadSerializer(orden)
        return Response(
            {"detail": "Venta bajo costo aprobada.", "orden": read_serializer.data},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='simular-pedido')
    def simular_pedido(self, request):
        serializer = DetalleOrdenWriteSerializer(data=request.data.get('detalles', []), many=True)
        serializer.is_valid(raise_exception=True)
        detalles_data = serializer.validated_data

        simulated_total = 0
        simulated_items = []

        for item_data in serializer.validated_data:
            articulo_id = item_data['articulo_id']
            cantidad = item_data['cantidad']
            try:
                articulo = get_object_or_404(Articulo, articulo_id=articulo_id)
            except:
                return Response(
                    {"detail": f"Artículo con ID {articulo_id} no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )

            precio_unitario = articulo.precio_sugerido # Placeholder
            descuento = 0 # Placeholder
            total_item = (cantidad * precio_unitario) - descuento
            simulated_total += total_item

            simulated_items.append({
                "articulo_id": str(articulo.articulo_id),
                "descripcion": articulo.descripcion,
                "cantidad": cantidad,
                "precio_base": price_data["precio_base"],
                "precio_unitario_calculado": price_data["precio_final"],
                "descuento_aplicado": price_data["descuento_total"],
                "total_item": total_item,
                "reglas_aplicadas": price_data["reglas_aplicadas"]
            })

        return Response({
            "detail": "Simulación de pedido exitosa.",
            "simulated_total": simulated_total,
            "simulated_items": simulated_items
        }, status=status.HTTP_200_OK)


class CalcularPrecioArticuloAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ArticuloPrecioCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        articulo_id = validated_data['articulo_id']
        lista_precio_id = validated_data['lista_precio_id']
        canal = validated_data['canal']
        cantidad = validated_data['cantidad']

        try:
            articulo = get_object_or_404(Articulo, articulo_id=articulo_id)
            lista_precio = get_object_or_404(ListaPrecio, lista_precio_id=lista_precio_id)
        except Http404:
            return Response({"detail": "Artículo o Lista de Precio no encontrados."}, status=status.HTTP_404_NOT_FOUND)

        precio_calculado = float(articulo.precio_sugerido) * cantidad
        descuento_aplicado = 0.0
        reglas_aplicadas = []

        return Response({
            "articulo_id": str(articulo_id),
            "descripcion_articulo": articulo.descripcion,
            "cantidad": cantidad,
            "precio_base_unitario": price_data["precio_base"],
            "precio_unitario_calculado": price_data["precio_final"],
            "descuento_aplicado": price_data["descuento_total"],
            "total_calculado": price_data["precio_final"] * cantidad,
            "reglas_aplicadas": price_data["reglas_aplicadas"],
            "vendido_bajo_costo": price_data["vendido_bajo_costo"]
        }, status=status.HTTP_200_OK)


class EstadisticasGeneralesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ventas_hoy = 1500.75
        ordenes_hoy = 15
        ventas_mes = 45000.50
        ordenes_mes = 350
        
        # Estados que se consideran una venta real
        estados_validos = [EstadoOrden.PROCESANDO, EstadoOrden.COMPLETADA]

        # QuerySet base para ventas válidas
        ventas_validas = OrdenCompraCliente.objects.filter(estado__in=estados_validos)

        # Estadísticas de hoy
        ventas_hoy_qs = ventas_validas.filter(fecha_orden=today)
        stats_hoy = ventas_hoy_qs.aggregate(
            total_ventas=Sum('total'),
            cantidad_ordenes=Count('orden_compra_cliente_id')
        )

        # Estadísticas del mes
        ventas_mes_qs = ventas_validas.filter(
            fecha_orden__year=today.year,
            fecha_orden__month=today.month
        )
        stats_mes = ventas_mes_qs.aggregate(
            total_ventas=Sum('total'),
            cantidad_ordenes=Count('orden_compra_cliente_id')
        )

        return Response({
            "ventas_hoy": stats_hoy['total_ventas'] or 0,
            "ordenes_hoy": stats_hoy['cantidad_ordenes'] or 0,
            "ventas_mes": stats_mes['total_ventas'] or 0,
            "ordenes_mes": stats_mes['cantidad_ordenes'] or 0,
        }, status=status.HTTP_200_OK)