"""
Serializadores para el módulo de Ventas.
"""
from rest_framework import serializers
from .models import OrdenCompraCliente, DetalleOrdenCompraCliente
from .services import VentaService
from productos.serializers import ArticuloListSerializer
from clientes.serializers import ClienteSerializer


class DetalleOrdenCompraClienteSerializer(serializers.ModelSerializer):
    """Serializer para el detalle de una orden de compra."""
    articulo = ArticuloListSerializer(read_only=True)

    class Meta:
        model = DetalleOrdenCompraCliente
        fields = [
            'articulo',
            'cantidad',
            'precio_base',
            'precio_unitario',
            'descuento',
            'total_item',
            'reglas_aplicadas',
            'vendido_bajo_costo',
        ]


class OrdenCompraClienteListSerializer(serializers.ModelSerializer):
    """Serializer para listar órdenes de compra (vista simplificada)."""
    cliente_nombre = serializers.CharField(source='cliente.nombre_comercial', read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = OrdenCompraCliente
        fields = [
            'orden_compra_cliente_id',
            'numero_orden',
            'fecha_orden',
            'cliente_nombre',
            'vendedor_nombre',
            'total',
            'estado',
            'estado_display',
        ]


class OrdenCompraClienteSerializer(serializers.ModelSerializer):
    """Serializer completo para el detalle de una orden de compra."""
    cliente = ClienteSerializer(read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre_sucursal', read_only=True)
    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    detalles = DetalleOrdenCompraClienteSerializer(many=True, read_only=True, source='detalles_orden_compra_cliente')

    class Meta:
        model = OrdenCompraCliente
        fields = [
            'orden_compra_cliente_id',
            'numero_orden',
            'fecha_orden',
            'cliente',
            'vendedor_nombre',
            'sucursal_nombre',
            'lista_precio_nombre',
            'subtotal',
            'descuento_total',
            'total',
            'estado',
            'estado_display',
            'detalles',
        ]


class DetalleOrdenCreateSerializer(serializers.Serializer):
    """Serializer para los items al crear una cotización."""
    articulo_id = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)


class OrdenCompraClienteCreateSerializer(serializers.Serializer):
    """Serializer para crear una cotización (orden en estado borrador)."""
    cliente_id = serializers.UUIDField()
    sucursal_id = serializers.IntegerField()
    canal = serializers.IntegerField()
    vendedor_id = serializers.CharField() # Es un username
    detalles = DetalleOrdenCreateSerializer(many=True)

    def create(self, validated_data):
        # La lógica de creación está en la vista, que usa el VentaService.
        # Este serializer es solo para validación de la entrada.
        pass

    def update(self, instance, validated_data):
        pass


class CalcularPrecioArticuloSerializer(serializers.Serializer):
    """Serializer para calcular el precio de un solo artículo."""
    articulo_id = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)
    sucursal_id = serializers.IntegerField()
    canal = serializers.IntegerField()


class SimularPedidoSerializer(serializers.Serializer):
    """Serializer para simular un pedido completo."""
    cliente_id = serializers.UUIDField()
    sucursal_id = serializers.IntegerField()
    canal = serializers.IntegerField()
    detalles = DetalleOrdenCreateSerializer(many=True)

