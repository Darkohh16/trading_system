from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView # Added
from django.db import transaction
from django.shortcuts import get_object_or_404, Http404 # Added Http404

from ventas.models import OrdenCompraCliente, DetalleOrdenCompraCliente
from productos.models import *
from precios.models import *
from ventas.serializers import (
    OrdenReadSerializer, OrdenWriteSerializer,
    DetalleOrdenWriteSerializer, ArticuloSerializer,
)
from trading_system.choices import EstadoOrden
from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdminOrReadOnly # Assuming this is the base permission
from ventas.permissions import CanApproveLowCostSale
from auditoria.utils import auditoria_context # Added # Added

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
        
        with transaction.atomic():
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
            with auditoria_context(request.user, motivo=f"Orden {orden.orden_compra_cliente_id} confirmada"):
                orden.estado = EstadoOrden.PROCESANDO # Or COMPLETED, depending on workflow
                orden.save()
                print(f"AUDIT: User {request.user.username} confirmed order {orden.orden_compra_cliente_id}. New state: {orden.get_estado_display()}")

        read_serializer = OrdenReadSerializer(orden)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='anular')
    def anular_orden(self, request, pk=None):
        orden = self.get_object()
        # Asumiendo que solo se pueden anular órdenes en PENDIENTE o PROCESANDO
        if orden.estado not in [EstadoOrden.PENDIENTE, EstadoOrden.PROCESANDO]:
            return Response(
                {"detail": "Solo se pueden anular órdenes en estado PENDIENTE o PROCESANDO."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
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

        for item_data in detalles_data:
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
                "precio_unitario": float(precio_unitario),
                "descuento": float(descuento),
                "total_item": float(total_item)
            })

        return Response({
            "detail": "Simulación de pedido exitosa.",
            "simulated_total": float(simulated_total),
            "simulated_items": simulated_items
        }, status=status.HTTP_200_OK)


class CalcularPrecioArticuloAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ArticuloPrecioCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        articulo_id = serializer.validated_data['articulo_id']
        lista_precio_id = serializer.validated_data['lista_precio_id']
        canal = serializer.validated_data['canal']
        cantidad = serializer.validated_data['cantidad']

        try:
            articulo = get_object_or_404(Articulo, articulo_id=articulo_id)
            lista_precio = get_object_or_404(ListaPrecio, lista_precio_id=lista_precio_id)
        except Http404:
            return Response(
                {"detail": "Artículo o Lista de Precio no encontrados."},
                status=status.HTTP_404_NOT_FOUND
            )

        precio_calculado = float(articulo.precio_sugerido) * cantidad
        descuento_aplicado = 0.0
        reglas_aplicadas = []

        return Response({
            "articulo_id": str(articulo_id),
            "descripcion_articulo": articulo.descripcion,
            "cantidad": cantidad,
            "precio_base_unitario": float(articulo.precio_sugerido),
            "precio_unitario_calculado": float(articulo.precio_sugerido), # Placeholder
            "descuento_aplicado": descuento_aplicado,
            "total_calculado": precio_calculado - descuento_aplicado,
            "reglas_aplicadas": reglas_aplicadas
        }, status=status.HTTP_200_OK)

class EstadisticasGeneralesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
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