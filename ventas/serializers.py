from rest_framework import serializers
from django.db import transaction
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce

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
    id = serializers.UUIDField(required=False, allow_null=True)
    articulo_id = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)


class OrdenWriteSerializer(serializers.ModelSerializer):
    detalles = DetalleOrdenWriteSerializer(many=True, write_only=True, required=True)
    cliente_id = serializers.UUIDField(write_only=True)
    vendedor_id = serializers.CharField(max_length=25, write_only=True)
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

    def _recalculate_and_save_totals(self, orden):
        """
        Recalcula los totales de la orden desde cero basándose en sus detalles.
        Este método es crucial para sobrescribir la lógica problemática en el save() del modelo
        y garantizar la consistencia de los datos, especialmente después de operaciones en lote.
        """
        aggregates = orden.detalles_orden_compra_cliente.aggregate(
            total_subtotal=Coalesce(Sum(F('cantidad') * F('precio_unitario')), 0, output_field=DecimalField()),
            total_descuento=Coalesce(Sum('descuento'), 0, output_field=DecimalField())
        )

        orden.subtotal = aggregates['total_subtotal']
        orden.descuento_total = aggregates['total_descuento']
        orden.total = orden.subtotal - orden.descuento_total
        
        orden.save(update_fields=['subtotal', 'descuento_total', 'total'])

    @transaction.atomic
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
            estado=EstadoOrden.PENDIENTE,
            **validated_data
        )

        for detalle_data in detalles_data:
            articulo_id = detalle_data['articulo_id']
            cantidad = detalle_data['cantidad']
            try:
                articulo = Articulo.objects.get(articulo_id=articulo_id)
            except Articulo.DoesNotExist:
                raise serializers.ValidationError(f"Artículo con ID {articulo_id} no encontrado.")

            precio_base = articulo.precio_sugerido
            precio_unitario = precio_base
            descuento = 0
            vendido_bajo_costo = False
            reglas_aplicadas = {}

            DetalleOrdenCompraCliente.objects.create(
                orden_compra_cliente=orden,
                articulo=articulo,
                cantidad=cantidad,
                precio_base=precio_base,
                precio_unitario=precio_unitario,
                descuento=descuento,
                reglas_aplicadas=reglas_aplicadas,
                vendido_bajo_costo=vendido_bajo_costo,
            )
        
        self._recalculate_and_save_totals(orden)
        return orden

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.estado != EstadoOrden.PENDIENTE:
            raise serializers.ValidationError("Solo se pueden actualizar órdenes en estado PENDIENTE.")

        detalles_data = validated_data.pop('detalles', None)

        # Actualizar campos directos de la orden
        instance.cliente_id = validated_data.get('cliente_id', instance.cliente_id)
        instance.vendedor_id = validated_data.get('vendedor_id', instance.vendedor_id)
        instance.lista_precio_id = validated_data.get('lista_precio_id', instance.lista_precio_id)
        instance.empresa_id = validated_data.get('empresa_id', instance.empresa_id)
        instance.sucursal_id = validated_data.get('sucursal_id', instance.sucursal_id)
        instance.canal = validated_data.get('canal', instance.canal)
        instance.save()

        if detalles_data is not None:
            existing_details = {str(d.detalle_orden_compra_cliente_id): d for d in instance.detalles_orden_compra_cliente.all()}
            incoming_ids = {str(item.get('id')) for item in detalles_data if item.get('id')}

            ids_to_delete = set(existing_details.keys()) - incoming_ids
            if ids_to_delete:
                DetalleOrdenCompraCliente.objects.filter(detalle_orden_compra_cliente_id__in=ids_to_delete).delete()

            for item_data in detalles_data:
                item_id = item_data.get('id')
                articulo_id = item_data['articulo_id']
                cantidad = item_data['cantidad']

                try:
                    articulo = Articulo.objects.get(articulo_id=articulo_id)
                except Articulo.DoesNotExist:
                    raise serializers.ValidationError(f"Artículo con ID {articulo_id} no encontrado.")

                precio_base = articulo.precio_sugerido
                precio_unitario = precio_base
                descuento = 0

                if item_id:
                    detail = existing_details.get(str(item_id))
                    if detail:
                        detail.cantidad = cantidad
                        detail.precio_base = precio_base
                        detail.precio_unitario = precio_unitario
                        detail.descuento = descuento
                        detail.save()
                else:
                    DetalleOrdenCompraCliente.objects.create(
                        orden_compra_cliente=instance,
                        articulo=articulo,
                        cantidad=cantidad,
                        precio_base=precio_base,
                        precio_unitario=precio_unitario,
                        descuento=descuento,
                    )
        
        self._recalculate_and_save_totals(instance)
        return instance


class ArticuloPrecioCalculateSerializer(serializers.Serializer):
    articulo_id = serializers.UUIDField()
    lista_precio_id = serializers.UUIDField()
    canal = serializers.ChoiceField(choices=CanalVenta.choices)
    cantidad = serializers.IntegerField(min_value=1)

