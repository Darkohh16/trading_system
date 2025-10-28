from rest_framework import serializers
from precios.models import ReglaPrecio


class ReglaPrecioSerializer(serializers.ModelSerializer):

    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True)
    aplica_linea_nombre = serializers.CharField(source='aplica_linea.nombre_linea', read_only=True, allow_null=True)
    aplica_grupo_nombre = serializers.CharField(source='aplica_grupo.nombre_grupo', read_only=True, allow_null=True)
    aplica_articulo_nombre = serializers.CharField(source='aplica_articulo.descripcion', read_only=True, allow_null=True)

    class Meta:
        model = ReglaPrecio
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']

    def validate(self, data):
        tipo_regla = data.get('tipo_regla')

        #"aplique a" exista
        if not any([
            data.get('aplica_canal'),
            data.get('aplica_linea'),
            data.get('aplica_grupo'),
            data.get('aplica_articulo')
        ]):
            raise serializers.ValidationError(
                'Debe especificar al menos un criterio de aplicación (canal, línea, grupo o artículo)'
            )

        #segun regla - faltan las demas
        if tipo_regla == 2:  #escala cantidad
            if not data.get('cantidad_minima'):
                raise serializers.ValidationError({
                    'cantidad_minima': 'Este campo es obligatorio para reglas de tipo escala de cantidad'
                })

        elif tipo_regla == 3:  #escala monto
            if not data.get('monto_minimo'):
                raise serializers.ValidationError({
                    'monto_minimo': 'Este campo es obligatorio para reglas de tipo escala de monto'
                })

        #fechas validar
        if data['fecha_inicio'] > data['fecha_fin']:
            raise serializers.ValidationError({
                'fecha_fin': 'La fecha de fin debe ser mayor o igual a la fecha de inicio'
            })

        tipo_descuento = data.get('tipo_descuento')
        valor_descuento = data.get('valor_descuento')

        if tipo_descuento == 1 and valor_descuento > 100:
            raise serializers.ValidationError({
                'valor_descuento': 'El porcentaje de descuento no puede ser mayor a 100'
            })

        if valor_descuento < 0:
            raise serializers.ValidationError({
                'valor_descuento': 'El valor de descuento no puede ser negativo'
            })

        return data