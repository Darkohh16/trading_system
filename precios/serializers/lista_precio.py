from rest_framework import serializers
from precios.models import ListaPrecio, PrecioArticulo, ReglaPrecio
from django.utils import timezone
#from core.serializers import Empresa, Sucursal
#from catalogos.serializers import Articulo

class ListaPrecioSerializer(serializers.ModelSerializer):
    #GET /api/listas/

    empresa_nombre = serializers.CharField(source='empresa.razon_social', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    cantidad_articulos = serializers.SerializerMethodField()

    class Meta:
        model = ListaPrecio
        fields = [
            'lista_precio_id',
            'empresa',
            'empresa_nombre',
            'sucursal',
            'sucursal_nombre',
            'codigo',
            'nombre',
            'tipo',
            'canal',
            'tipo_moneda',
            'estado',
            'fecha_vigencia_inicio',
            'fecha_vigencia_fin',
            'fecha_creacion',
            'fecha_modificacion',
            'cantidad_articulos',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'cantidad_articulos']

    def get_cantidad_articulos(self, obj):
        return obj.precios_articulos.filter(estado=1).count()

class ListaPrecioDetalleSerializer(serializers.ModelSerializer):
    #GET /api/listas/{id}/

    empresa_nombre = serializers.CharField(source='empresa.razon_social', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    modificado_por = serializers.StringRelatedField(read_only=True)

    cantidad_articulos = serializers.SerializerMethodField()
    cantidad_reglas = serializers.SerializerMethodField()
    vigente = serializers.SerializerMethodField()

    class Meta:
        model = ListaPrecio
        fields = '__all__'

    def get_cantidad_articulos(self, obj):
        return obj.precios_articulos.filter(estado=1).count()

    def get_cantidad_reglas(self, obj):
        return obj.precios_articulos.filter(estado=1).count()

    def get_vigente(self, obj):
        dia_hoy = timezone.now().date()
        return (obj.estado == 1) and (obj.fecha_vigencia_inicio <= dia_hoy <= obj.fecha_vigencia_fin)

class ListaPrecioCrearActualizarSerializer(serializers.ModelSerializer):
    #POST /api/listas/
    #PUT /api/listas/{id}/

    class Meta:
        model = ListaPrecio
        fields = [
            'empresa',
            'sucursal',
            'codigo',
            'nombre',
            'tipo',
            'canal',
            'tipo_moneda',
            'estado',
            'fecha_vigencia_inicio',
            'fecha_vigencia_fin',
        ]

    def validate(self, data):
        #para fechas de vigencia
        if data['fecha_vigencia_fin'] < data['fecha_vigencia_inicio']:
            raise serializers.ValidationError({
                'fecha_vigencia_fin': 'La fecha de vigencia fin no puede ser anterior a la fecha de vigencia inicio.'
            })

        #para que no se cubran en listas del mismo tipo
        empresa = data.get('empresa')
        sucursal = data.get('sucursal')
        tipo = data.get('tipo')
        fecha_inicio = data['fecha_vigencia_inicio']
        fecha_fin = data['fecha_vigencia_fin']

        listas = ListaPrecio.objects.filter(
            empresa=empresa,
            sucursal=sucursal,
            tipo=tipo,
            estado=1,
        ).filter(
            fecha_vigencia_inicio__lte=fecha_fin,
            fecha_vigencia_fin__gte=fecha_inicio,
        )

        if self.instance:
            listas = listas.exclude(lista_precio_id=self.instance.lista_precio_id)

        if listas.exists():
            raise serializers.ValidationError('Ya existe una lista de precios vigente para el mismo tipo en el rango de fechas especificado.')

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['modificado_por'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['modificado_por'] = request.user
        return super().update(instance, validated_data)