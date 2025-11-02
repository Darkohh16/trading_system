"""
Vistas para el módulo de Ventas
"""
import uuid
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Sucursal
from core.permissions import PuedeAprobarBajoCosto
from trading_system.choices import EstadoOrden

from .models import OrdenCompraCliente, DetalleOrdenCompraCliente
from .serializers import (
    OrdenCompraClienteSerializer,
    OrdenCompraClienteListSerializer,
    OrdenCompraClienteCreateSerializer,
    CalcularPrecioArticuloSerializer,
    SimularPedidoSerializer,
)
from .services import VentaService


class OrdenCompraClienteViawSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las Órdenes de Compra de Clientes.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrdenCompraCliente.objects.select_related(
            'cliente', 'vendedor', 'sucursal', 'lista_precio'
        ).prefetch_related(
            'detalles_orden_compra_cliente__articulo'
        ).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return OrdenCompraClienteListSerializer
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return OrdenCompraClienteCreateSerializer
        return OrdenCompraClienteSerializer

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Endpoint 12: Obtener estadísticas de ventas del día y del mes.
        """
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year

        # Considerar solo órdenes que no estén canceladas
        queryset = self.get_queryset().exclude(estado=EstadoOrden.CANCELADA)

        # Ventas del día
        ventas_dia = queryset.filter(fecha_orden=today).aggregate(
            total_dia=Coalesce(Sum('total'), Decimal('0.0'), output_field=DecimalField())
        )['total_dia']

        # Ventas del mes
        ventas_mes = queryset.filter(
            fecha_orden__year=current_year,
            fecha_orden__month=current_month
        ).aggregate(
            total_mes=Coalesce(Sum('total'), Decimal('0.0'), output_field=DecimalField())
        )['total_mes']

        return Response({
            'ventas_del_dia': ventas_dia,
            'ventas_del_mes': ventas_mes
        })

    def list(self, request, *args, **kwargs):
        """
        Endpoint 1: Listar órdenes.
        """
        queryset = self.get_queryset().order_by('-fecha_orden', '-numero_orden')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Endpoint 3: Obtener detalle completo de una orden.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Endpoint 2: Crear una cotización (Orden en estado Borrador).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = VentaService()

        try:
            # Usamos un bloque de transacción para asegurar la atomicidad
            with transaction.atomic():
                # 1. Calcular el pedido completo usando el servicio
                pedido_calculado = service.calcular_pedido(
                    cliente_id=data['cliente_id'],
                    sucursal_id=data['sucursal_id'],
                    canal=data['canal'],
                    lineas=data['detalles']
                )

                sucursal = Sucursal.objects.get(pk=data['sucursal_id'])

                # 2. Generar nuevo número de orden (solución temporal, no segura para concurrencia)
                last_order = OrdenCompraCliente.objects.order_by('-numero_orden').first()
                new_order_number = (last_order.numero_orden + 1) if last_order else 1

                # 3. Crear la Orden de Compra principal
                orden = OrdenCompraCliente.objects.create(
                    orden_compra_cliente_id=uuid.uuid4(),
                    numero_orden=new_order_number,
                    empresa_id=sucursal.empresa_id,
                    sucursal_id=data['sucursal_id'],
                    cliente=pedido_calculado.cliente,
                    vendedor_id=data['vendedor_id'],
                    canal=data['canal'],
                    lista_precio=pedido_calculado.lista_precio,
                    subtotal=pedido_calculado.subtotal,
                    descuento_total=pedido_calculado.descuento_total,
                    total=pedido_calculado.total,
                    estado=EstadoOrden.PENDIENTE
                )

                # 4. Crear los detalles de la orden
                detalles_a_crear = []
                for linea in pedido_calculado.lineas:
                    detalles_a_crear.append(
                        DetalleOrdenCompraCliente(
                            detalle_orden_compra_cliente_id=uuid.uuid4(),
                            orden_compra_cliente=orden,
                            articulo=linea.articulo,
                            cantidad=linea.cantidad,
                            precio_base=linea.precio_base,
                            precio_unitario=linea.precio_unitario,
                            descuento=linea.descuento,
                            total_item=linea.total_item,
                            reglas_aplicadas=linea.reglas_aplicadas,
                            vendido_bajo_costo=linea.vendido_bajo_costo
                        )
                    )
                DetalleOrdenCompraCliente.objects.bulk_create(detalles_a_crear)

            # 5. Serializar la respuesta completa
            response_serializer = OrdenCompraClienteSerializer(orden)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except (ValueError, AttributeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Consider logging the error here for production
            return Response({'error': 'Ocurrió un error inesperado al crear la cotización.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """
        Endpoint 4: Actualizar una cotización si está en estado PENDIENTE.
        """
        instance = self.get_object()
        if instance.estado != EstadoOrden.PENDIENTE:
            return Response({'error': 'Solo se pueden modificar órdenes en estado PENDIENTE.'}, status=status.HTTP_403_FORBIDDEN)

        # La lógica de actualización es similar a la de creación
        # Se recalcula todo el pedido
        serializer = OrdenCompraClienteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = VentaService()
        try:
            with transaction.atomic():
                pedido_calculado = service.calcular_pedido(
                    cliente_id=data['cliente_id'],
                    sucursal_id=data['sucursal_id'],
                    canal=data['canal'],
                    lineas=data['detalles']
                )

                # Actualizar la orden existente
                instance.subtotal = pedido_calculado.subtotal
                instance.descuento_total = pedido_calculado.descuento_total
                instance.total = pedido_calculado.total
                instance.save()

                # Eliminar detalles antiguos y crear los nuevos
                instance.detalles_orden_compra_cliente.all().delete()
                detalles_a_crear = []
                for linea in pedido_calculado.lineas:
                    detalles_a_crear.append(
                        DetalleOrdenCompraCliente(
                            detalle_orden_compra_cliente_id=uuid.uuid4(),
                            orden_compra_cliente=instance,
                            articulo=linea.articulo,
                            cantidad=linea.cantidad,
                            precio_base=linea.precio_base,
                            precio_unitario=linea.precio_unitario,
                            descuento=linea.descuento,
                            total_item=linea.total_item,
                            reglas_aplicadas=linea.reglas_aplicadas,
                            vendido_bajo_costo=linea.vendido_bajo_costo
                        )
                    )
                DetalleOrdenCompraCliente.objects.bulk_create(detalles_a_crear)

            response_serializer = OrdenCompraClienteSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except (ValueError, AttributeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Ocurrió un error inesperado al actualizar la cotización.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        # La actualización parcial es compleja, por ahora la delegamos a la completa.
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Endpoint 5: Anular una cotización (orden en estado PENDIENTE).
        """
        instance = self.get_object()
        if instance.estado != EstadoOrden.PENDIENTE:
            return Response({'error': 'Solo se pueden anular órdenes en estado PENDIENTE.'}, status=status.HTTP_403_FORBIDDEN)

        instance.estado = EstadoOrden.CANCELADA
        instance.save()
        return Response({'message': 'La cotización ha sido anulada.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Endpoint 6: Confirmar una orden (cambia de PENDIENTE a COMPLETADA).
        Valida stock y lo actualiza.
        """
        instance = self.get_object()

        if instance.estado != EstadoOrden.PENDIENTE:
            return Response({'error': 'Solo se pueden confirmar órdenes en estado PENDIENTE.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            with transaction.atomic():
                # 1. Validar y actualizar stock
                for detalle in instance.detalles_orden_compra_cliente.all():
                    articulo = detalle.articulo
                    if articulo.stock < detalle.cantidad:
                        return Response(
                            {'error': f'Stock insuficiente para el artículo {articulo.descripcion}. Disponible: {articulo.stock}, Requerido: {detalle.cantidad}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    articulo.stock -= detalle.cantidad
                    articulo.save()

                # 2. Cambiar estado de la orden
                instance.estado = EstadoOrden.COMPLETADA
                instance.save()

                # TODO: Auditoría - Registrar confirmación de orden

            response_serializer = OrdenCompraClienteSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Consider logging the error here for production
            return Response({'error': f'Ocurrió un error inesperado al confirmar la orden: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def marcar_facturada(self, request, pk=None):
        """
        Endpoint 7: Marcar una orden como FACTURADA.
        """
        instance = self.get_object()

        if instance.estado != EstadoOrden.COMPLETADA:
            return Response({'error': 'Solo se pueden marcar como facturadas órdenes en estado COMPLETADA.'}, status=status.HTTP_403_FORBIDDEN)

        instance.estado = EstadoOrden.FACTURADA
        instance.save()

        # TODO: Auditoría - Registrar orden facturada

        response_serializer = OrdenCompraClienteSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def anular_confirmada(self, request, pk=None):
        """
        Endpoint 8: Anular una orden confirmada (cambia de COMPLETADA a CANCELADA).
        Revierte el stock.
        """
        instance = self.get_object()

        if instance.estado != EstadoOrden.COMPLETADA:
            return Response({'error': 'Solo se pueden anular órdenes en estado COMPLETADA.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            with transaction.atomic():
                # 1. Revertir stock
                for detalle in instance.detalles_orden_compra_cliente.all():
                    articulo = detalle.articulo
                    articulo.stock += detalle.cantidad
                    articulo.save()

                # 2. Cambiar estado de la orden
                instance.estado = EstadoOrden.CANCELADA
                instance.save()

                # TODO: Auditoría - Registrar anulación de orden confirmada

            response_serializer = OrdenCompraClienteSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Ocurrió un error inesperado al anular la orden: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, PuedeAprobarBajoCosto])
    def aprobar_ventas_bajo_costo(self, request, pk=None):
        """
        Endpoint 9: Aprobar ventas bajo costo (cambia de PENDIENTE a COMPLETADA).
        Requiere permiso especial (puede_aprobar_bajo_costo).
        """
        instance = self.get_object()

        if instance.estado != EstadoOrden.PENDIENTE:
            return Response({'error': 'Solo se pueden aprobar ventas bajo costo en órdenes en estado PENDIENTE.'}, status=status.HTTP_403_FORBIDDEN)

        # Verificar si realmente hay artículos vendidos bajo costo
        if not any(detalle.vendido_bajo_costo for detalle in instance.detalles_orden_compra_cliente.all()):
            return Response({'error': 'La orden no contiene artículos vendidos bajo costo que requieran aprobación.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.estado = EstadoOrden.COMPLETADA
        instance.save()

        # TODO: Auditoría - Registrar aprobación de venta bajo costo

        response_serializer = OrdenCompraClienteSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CalcularPrecioArticuloView(generics.GenericAPIView):
    """
    Endpoint 10: Calcular precio de un artículo (sin crear orden).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CalcularPrecioArticuloSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = VentaService()
        try:
            linea_calculada = service.calcular_linea_articulo(
                articulo_id=data['articulo_id'],
                cantidad=data['cantidad'],
                sucursal_id=data['sucursal_id'],
                canal=data['canal']
            )
            # No podemos serializar directamente el dataclass, así que lo convertimos a dict
            response_data = {
                'articulo_id': linea_calculada.articulo.articulo_id,
                'descripcion': linea_calculada.articulo.descripcion,
                'cantidad': linea_calculada.cantidad,
                'precio_base': linea_calculada.precio_base,
                'precio_unitario': linea_calculada.precio_unitario,
                'descuento': linea_calculada.descuento,
                'total_item': linea_calculada.total_item,
                'reglas_aplicadas': linea_calculada.reglas_aplicadas,
                'vendido_bajo_costo': linea_calculada.vendido_bajo_costo
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except (ValueError, AttributeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Ocurrió un error inesperado al calcular el precio.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimularPedidoView(generics.GenericAPIView):
    """
    Endpoint 11: Simular un pedido completo (sin guardar).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SimularPedidoSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = VentaService()
        try:
            pedido_calculado = service.calcular_pedido(
                cliente_id=data['cliente_id'],
                sucursal_id=data['sucursal_id'],
                canal=data['canal'],
                lineas=data['detalles']
            )
            # El dataclass no es directamente serializable a JSON, así que lo convertimos a un dict
            response_data = {
                'cliente_id': pedido_calculado.cliente.cliente_id,
                'lista_precio': pedido_calculado.lista_precio.nombre,
                'subtotal': pedido_calculado.subtotal,
                'descuento_total': pedido_calculado.descuento_total,
                'total': pedido_calculado.total,
                'lineas': [
                    {
                        'articulo_id': linea.articulo.articulo_id,
                        'descripcion': linea.articulo.descripcion,
                        'cantidad': linea.cantidad,
                        'precio_base': linea.precio_base,
                        'precio_unitario': linea.precio_unitario,
                        'descuento': linea.descuento,
                        'total_item': linea.total_item,
                        'reglas_aplicadas': linea.reglas_aplicadas,
                        'vendido_bajo_costo': linea.vendido_bajo_costo
                    } for linea in pedido_calculado.lineas
                ]
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except (ValueError, AttributeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Ocurrió un error inesperado al simular el pedido.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
