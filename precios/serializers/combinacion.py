from rest_framework import serializers
from precios.models import CombinacionProducto, DetalleCombinacionProducto

class DetalleCombinacionSerializer(serializers.ModelSerializer):

    articulo_nombre = serializers.CharField(
        source='articulo.descripcion',
        read_only=True,
        allow_null=True
    )
    grupo_nombre = serializers.CharField(
        source='grupo.nombre_grupo',
        read_only=True,
        allow_null=True
    )
    linea_nombre = serializers.CharField(
        source='linea.nombre_linea',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = DetalleCombinacionProducto
        fields = [
            'detalle_combinacion_id',
            'tipo_item',
            'articulo',
            'articulo_nombre',
            'grupo',
            'grupo_nombre',
            'linea',
            'linea_nombre',
            'cantidad_requerida',
        ]

    def validate(self, data):
        #Validar que exactamente uno de (articulo, grupo, linea) tenga valor
        articulo = data.get('articulo')
        grupo = data.get('grupo')
        linea = data.get('linea')

        #contar presentes
        presentes = sum([bool(articulo), bool(grupo), bool(linea)])

        if presentes == 0:
            raise serializers.ValidationError(
                'Debe especificar un artículo, grupo o línea'
            )

        if presentes > 1:
            raise serializers.ValidationError(
                'Solo puede especificar UNO de: artículo, grupo o línea'
            )

        #validar coincidencia items
        tipo_item = data.get('tipo_item')

        if tipo_item == 1 and not articulo:
            raise serializers.ValidationError({
                'articulo': 'Debe especificar un artículo cuando tipo_item es "artículo"'
            })
        elif tipo_item == 2 and not grupo:
            raise serializers.ValidationError({
                'grupo': 'Debe especificar un grupo cuando tipo_item es "grupo"'
            })
        elif tipo_item == 3 and not linea:
            raise serializers.ValidationError({
                'linea': 'Debe especificar una línea cuando tipo_item es "línea"'
            })

        return data

class CombinacionProductoListaSerializer(serializers.ModelSerializer):
    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True)
    cantidad_items = serializers.SerializerMethodField()
    vigente = serializers.SerializerMethodField()

    class Meta:
        model = CombinacionProducto
        fields = [
            'combinacion_id',
            'nombre',
            'tipo_beneficio',
            'valor_beneficio',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'lista_precio',
            'lista_precio_nombre',
            'cantidad_items',
            'vigente',
        ]

    def get_cantidad_items(self, obj):
        return obj.detalles.count()

    def get_vigente(self, obj):
        from django.utils import timezone
        hoy = timezone.now().date()
        return (
                obj.estado == 1 and
                obj.fecha_inicio <= hoy <= obj.fecha_fin
        )


class CombinacionProductoDetalleSerializer(serializers.ModelSerializer):
    #Para detalle completo con items anidados

    detalles = DetalleCombinacionSerializer(many=True, read_only=True)
    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True)

    class Meta:
        model = CombinacionProducto
        fields = '__all__'


class CombinacionProductoCrearActualizarSerializer(serializers.ModelSerializer):
    """Para crear y actualizar combos con sus items"""

    detalles = DetalleCombinacionSerializer(many=True)

    class Meta:
        model = CombinacionProducto
        fields = [
            'nombre',
            'tipo_beneficio',
            'valor_beneficio',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'lista_precio',
            'detalles',
        ]

    def validate(self, data):
        #fechas
        if data['fecha_inicio'] > data['fecha_fin']:
            raise serializers.ValidationError({
                'fecha_fin': 'La fecha de fin debe ser mayor o igual a la fecha de inicio'
            })

        #beneficio
        tipo_beneficio = data.get('tipo_beneficio')
        valor_beneficio = data.get('valor_beneficio')

        if tipo_beneficio == 1 and valor_beneficio > 100:
            raise serializers.ValidationError({
                'valor_beneficio': 'El porcentaje no puede ser mayor a 100'
            })

        if valor_beneficio < 0:
            raise serializers.ValidationError({
                'valor_beneficio': 'El valor no puede ser negativo'
            })

        #detalle
        detalles = data.get('detalles', [])
        if not detalles:
            raise serializers.ValidationError({
                'detalles': 'Debe especificar al menos un item en la combinación'
            })

        return data

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')

        combinacion = CombinacionProducto.objects.create(**validated_data)

        # Crear detalles
        for detalle_data in detalles_data:
            DetalleCombinacionProducto.objects.create(
                combinacion_producto=combinacion,
                **detalle_data
            )

        return combinacion

    def update(self, instance, validated_data):
        detalles_data = validated_data.pop('detalles', None)

        #actualizar campos de la combinacion
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        #si hay detalles, reemplazar todos
        if detalles_data is not None:
            #detalles anteriores
            instance.detalles.all().delete()

            #nuevos detalles
            for detalle_data in detalles_data:
                DetalleCombinacionProducto.objects.create(
                    combinacion_producto=instance,
                    **detalle_data
                )

        return instance