from rest_framework import serializers
from ventas.models import OrdenCompraCliente, DetalleOrdenCompraCliente
from productos.models import Articulo
from clientes.models import Cliente
from precios.models import ListaPrecio
from accounts.models import Usuario
from core.models import Empresa, Sucursal
from trading_system.choices import EstadoOrden, CanalVenta

class ArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulo
        fields = ['articulo_id', 'codigo_articulo', 'descripcion', 'unidad_medida']

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['cliente_id', 'nro_documento', 'nombre_comercial', 'razon_social']

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email']

class ListaPrecioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListaPrecio
        fields = ['lista_precio_id', 'nombre', 'codigo']

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['empresa_id', 'nombre']

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['sucursal_id', 'nombre']

class OrdenDetalleReadSerializer(serializers.ModelSerializer):
    articulo = ArticuloSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = DetalleOrdenCompraCliente
        fields = [
            'detalle_orden_compra_cliente_id', 'articulo', 'cantidad',
            'precio_base', 'precio_unitario', 'descuento', 'reglas_aplicadas',
            'vendido_bajo_costo', 'total_item', 'estado_display'
        ]

class OrdenReadSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    vendedor = UsuarioSerializer(read_only=True)
    lista_precio = ListaPrecioSerializer(read_only=True)
    empresa = EmpresaSerializer(read_only=True)
    sucursal = SucursalSerializer(read_only=True)
    detalles_orden_compra_cliente = OrdenDetalleReadSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    canal_display = serializers.CharField(source='get_canal_display', read_only=True)

    class Meta:
        model = OrdenCompraCliente
        fields = [
            'orden_compra_cliente_id', 'numero_orden', 'fecha_orden', 'empresa', 'sucursal',
            'cliente', 'vendedor', 'canal', 'canal_display', 'lista_precio', 'subtotal',
            'descuento_total', 'total', 'estado', 'estado_display', 'detalles_orden_compra_cliente'
        ]

class DetalleOrdenWriteSerializer(serializers.Serializer):
    articulo_id = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)

class OrdenWriteSerializer(serializers.ModelSerializer):
    detalles = DetalleOrdenWriteSerializer(many=True, write_only=True)
    cliente_id = serializers.UUIDField(write_only=True)
    vendedor_id = serializers.CharField(max_length=25, write_only=True) # username is PK for Usuario
    lista_precio_id = serializers.UUIDField(write_only=True)
    empresa_id = serializers.UUIDField(write_only=True)
    sucursal_id = serializers.UUIDField(write_only=True)
    canal = serializers.ChoiceField(choices=CanalVenta.choices, write_only=True)

    class Meta:
        model = OrdenCompraCliente
        fields = [
            'cliente_id', 'vendedor_id', 'lista_precio_id', 'empresa_id', 'sucursal_id',
            'canal', 'detalles'
        ]
        read_only_fields = [
            'orden_compra_cliente_id', 'numero_orden', 'fecha_orden', 'subtotal',
            'descuento_total', 'total', 'estado'
        ]

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        cliente_id = validated_data.pop('cliente_id')
        vendedor_id = validated_data.pop('vendedor_id')
        lista_precio_id = validated_data.pop('lista_precio_id')
        empresa_id = validated_data.pop('empresa_id')
        sucursal_id = validated_data.pop('sucursal_id')

        try:
            cliente = Cliente.objects.get(cliente_id=cliente_id)
            vendedor = Usuario.objects.get(username=vendedor_id)
            lista_precio = ListaPrecio.objects.get(lista_precio_id=lista_precio_id)
            empresa = Empresa.objects.get(empresa_id=empresa_id)
            sucursal = Sucursal.objects.get(sucursal_id=sucursal_id)
        except (Cliente.DoesNotExist, Usuario.DoesNotExist, ListaPrecio.DoesNotExist, Empresa.DoesNotExist, Sucursal.DoesNotExist) as e:
            raise serializers.ValidationError(f"Error al encontrar una entidad relacionada: {e}")

        orden = OrdenCompraCliente.objects.create(
            cliente=cliente,
            vendedor=vendedor,
            lista_precio=lista_precio,
            empresa=empresa,
            sucursal=sucursal,
            estado=EstadoOrden.PENDIENTE, # Las cotizaciones inician como PENDIENTE
            **validated_data
        )

        # TODO: Implementar la lógica de cálculo de precios y creación de detalles
        # Por ahora, solo se crean los detalles con valores dummy
        for detalle_data in detalles_data:
            articulo_id = detalle_data['articulo_id']
            cantidad = detalle_data['cantidad']
            try:
                articulo = Articulo.objects.get(articulo_id=articulo_id)
            except Articulo.DoesNotExist:
                raise serializers.ValidationError(f"Artículo con ID {articulo_id} no encontrado.")

            # Valores dummy para precio y descuento, la lógica real de precios va aquí
            precio_base = articulo.precio_sugerido # Usar precio sugerido como base
            precio_unitario = precio_base # Asumir sin descuentos por ahora
            descuento = 0
            vendido_bajo_costo = False # Lógica para determinar si se vende bajo costo
            reglas_aplicadas = {} # Lógica para registrar reglas aplicadas

            DetalleOrdenCompraCliente.objects.create(
                orden_compra_cliente=orden,
                articulo=articulo,
                cantidad=cantidad,
                precio_base=precio_base,
                precio_unitario=precio_unitario,
                descuento=descuento,
                reglas_aplicadas=reglas_aplicadas,
                vendido_bajo_costo=vendido_bajo_costo,
                total_item=(cantidad * precio_unitario) - descuento
            )
        return orden

    def update(self, instance, validated_data):
        # La actualización de detalles se manejará en el ViewSet o en un serializer anidado específico
        # Por ahora, solo se actualizan los campos directos de la orden
        if instance.estado != EstadoOrden.PENDIENTE:
            raise serializers.ValidationError("Solo se pueden actualizar órdenes en estado PENDIENTE.")

        instance.cliente = validated_data.get('cliente', instance.cliente)
        instance.vendedor = validated_data.get('vendedor', instance.vendedor)
        instance.lista_precio = validated_data.get('lista_precio', instance.lista_precio)
        instance.empresa = validated_data.get('empresa', instance.empresa)
        instance.sucursal = validated_data.get('sucursal', instance.sucursal)
        instance.canal = validated_data.get('canal', instance.canal)
        instance.save()
        return instance

class ArticuloPrecioCalculateSerializer(serializers.Serializer):
    articulo_id = serializers.UUIDField()
    lista_precio_id = serializers.UUIDField()
    canal = serializers.ChoiceField(choices=CanalVenta.choices)
    cantidad = serializers.IntegerField(min_value=1)

