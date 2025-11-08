from rest_framework import serializers
from precios.models import PrecioArticulo
#from productos.serializers import ArticuloSerializer
from auditoria.models import DescuentoProveedorAutorizado
from django.utils import timezone

class PrecioArticuloListSerializer(serializers.ModelSerializer):

    articulo_nombre = serializers.CharField(source='articulo.descripcion', read_only=True)
    articulo_codigo = serializers.CharField(source='articulo.codigo_articulo', read_only=True)
    costo_actual = serializers.DecimalField(
        source='articulo.costo_actual',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    margen = serializers.SerializerMethodField()

    class Meta:
        model = PrecioArticulo
        fields = [
            'precio_articulo_id',
            'articulo',
            'articulo_codigo',
            'articulo_nombre',
            'precio_base',
            'precio_minimo',
            'costo_actual',
            'margen',
            'estado',
        ]

    def get_margen(self, obj):
        if obj.articulo.costo_actual > 0:
            margen = ((obj.precio_base - obj.articulo.costo_actual) / obj.articulo.costo_actual) * 100
            return round(margen, 2)
        return 0

class PrecioArticuloDetalleSerializer(serializers.ModelSerializer):

    #articulo = ArticuloSerializer(read_only=True)

    class Meta:
        model = PrecioArticulo
        fields = '__all__'

class PrecioArticuloCrearActualizarSerializer(serializers.ModelSerializer):
    motivo = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Motivo del cambio de precio (opcional)"
    )

    class Meta:
        model = PrecioArticulo
        fields = [
            'lista_precio',
            'articulo',
            'precio_base',
            'precio_minimo',
            'estado',
            'motivo',
        ]

    def validate(self, data):
        articulo = data.get('articulo')
        precio_base = data.get('precio_base')
        precio_minimo = data.get('precio_minimo')

        # Validar que precio_base no sea menor que costo_actual (salvo autorización)
        if precio_base and articulo and precio_base < articulo.costo_actual:
            # Verificar autorización del proveedor
            hoy = timezone.now().date()

            autorizacion = DescuentoProveedorAutorizado.objects.filter(
                articulo=articulo,
                estado=1,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).exists()

            if not autorizacion:
                raise serializers.ValidationError({
                    'precio_base': f'El precio base ({precio_base}) no puede ser menor que el costo actual ({articulo.costo_actual}) sin autorización de descuento de proveedor.'
                })

        #precio minimo <= precio base
        if precio_minimo and precio_minimo > precio_base:
            raise serializers.ValidationError({
                'precio_minimo': 'El precio minimo no puede ser mayor que el precio base.'
            })

        #unicidad de articulo en lista
        lista_precio = data.get('lista_precio')

        existe = PrecioArticulo.objects.filter(
            lista_precio=lista_precio,
            articulo=articulo
        )

        if self.instance:
            existe = existe.exclude(precio_articulo_id=self.instance.precio_articulo_id)

        if existe.exists():
            raise serializers.ValidationError({
                'articulo': 'El articulo ya tiene un precio asignado en esta lista de precios.'
            })

        if 'motivo' in data:
            data.pop('motivo')

        return data