from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import Http404
from decimal import Decimal

from ventas.models import OrdenCompraCliente
from productos.models import Articulo
from precios.models import ListaPrecio
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
        orden = serializer.save()
        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_21_CREATED)

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

    @action(detail=True, methods=['post'], url_path='confirmar')
    def confirmar_orden(self, request, pk=None):
        orden = self.get_object()
        if orden.estado != EstadoOrden.PENDIENTE:
            return Response(
                {"detail": "Solo se pueden confirmar órdenes en estado PENDIENTE."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # 1. Validar stock
            for detalle in orden.detalles_orden_compra_cliente.all():
                if detalle.cantidad > detalle.articulo.stock:
                    return Response(
                        {"detail": f"Stock insuficiente para el artículo {detalle.articulo.descripcion}. Stock disponible: {detalle.articulo.stock}, solicitado: {detalle.cantidad}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # 2. Descontar stock
            for detalle in orden.detalles_orden_compra_cliente.all():
                articulo = detalle.articulo
                articulo.stock -= detalle.cantidad
                articulo.save(update_fields=['stock'])

            # 3. Cambiar estado de la orden
            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} confirmada"):
                orden.estado = EstadoOrden.PROCESANDO
                orden.save()

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
            # Si la orden estaba en PROCESANDO, reponer stock
            if estado_original == EstadoOrden.PROCESANDO:
                for detalle in orden.detalles_orden_compra_cliente.all():
                    articulo = detalle.articulo
                    articulo.stock += detalle.cantidad
                    articulo.save(update_fields=['stock'])

            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} anulada"):
                orden.estado = EstadoOrden.CANCELADA
                orden.save()

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
            # Reponer stock porque la orden estaba completada (stock ya descontado)
            for detalle in orden.detalles_orden_compra_cliente.all():
                articulo = detalle.articulo
                articulo.stock += detalle.cantidad
                articulo.save(update_fields=['stock'])

            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} confirmada anulada"):
                orden.estado = EstadoOrden.CANCELADA
                orden.save()

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
        
        with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} aprobada bajo costo"):
            pass
        
        read_serializer = OrdenReadSerializer(orden)
        return Response(
            {"detail": "Venta bajo costo aprobada.", "orden": read_serializer.data},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='simular-pedido')
    def simular_pedido(self, request):
        serializer = DetalleOrdenWriteSerializer(data=request.data.get('detalles', []), many=True)
        serializer.is_valid(raise_exception=True)
        
        lista_precio_id = request.data.get('lista_precio_id')
        canal = request.data.get('canal')
        if not lista_precio_id or not canal:
            return Response(
                {"detail": "Se requiere 'lista_precio_id' y 'canal' para la simulación."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lista_precio = get_object_or_404(ListaPrecio, lista_precio_id=lista_precio_id)
        except Http404:
            return Response({"detail": "Lista de Precio no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        simulated_total = Decimal('0.0')
        simulated_items = []

        for item_data in serializer.validated_data:
            articulo_id = item_data['articulo_id']
            cantidad = item_data['cantidad']
            try:
                articulo = get_object_or_404(Articulo, articulo_id=articulo_id)
            except Http404:
                return Response({"detail": f"Artículo con ID {articulo_id} no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            price_data = calculate_price(
                articulo=articulo,
                lista_precio=lista_precio,
                canal=canal,
                cantidad=cantidad
            )

            if "error" in price_data:
                return Response({"detail": price_data["error"]}, status=status.HTTP_400_BAD_REQUEST)

            total_item = price_data["precio_final"] * cantidad
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

        price_data = calculate_price(
            articulo=articulo,
            lista_precio=lista_precio,
            canal=canal,
            cantidad=cantidad
        )

        if "error" in price_data:
            return Response({"detail": price_data["error"]}, status=status.HTTP_400_BAD_REQUEST)

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
        # TODO: Implementar la lógica real para calcular estadísticas
        ventas_hoy = 1500.75
        ordenes_hoy = 15
        ventas_mes = 45000.50
        ordenes_mes = 350
        
        return Response({
            "ventas_hoy": ventas_hoy,
            "ordenes_hoy": ordenes_hoy,
            "ventas_mes": ventas_mes,
            "ordenes_mes": ordenes_mes,
            "detail": "Estadísticas generales de ventas (datos de ejemplo)."
        }, status=status.HTTP_200_OK)