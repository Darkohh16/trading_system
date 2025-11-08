"""
Serializadores para el módulo de Catálogo de Productos
"""
import uuid
from rest_framework import serializers
from productos.models import LineaArticulo, GrupoArticulo, Articulo


class LineaArticuloSerializer(serializers.ModelSerializer):
    """
    Serializador para LineaArticulo
    Incluye todos los campos del modelo
    """
    class Meta:
        model = LineaArticulo
        fields = [
            'linea_id',
            'codigo_linea',
            'nombre_linea',
            'estado',
            'fecha_creacion',
            'fecha_modificacion'
        ]
        read_only_fields = ['linea_id', 'fecha_creacion', 'fecha_modificacion']
    
    def create(self, validated_data):
        """Genera automáticamente el UUID"""
        validated_data['linea_id'] = uuid.uuid4()
        return super().create(validated_data)


class GrupoArticuloSerializer(serializers.ModelSerializer):
    """
    Serializador para GrupoArticulo
    Muestra la línea anidada en lectura
    Permite escritura con linea_id
    """
    # Campo anidado de solo lectura para mostrar detalles de la línea
    linea_detalle = LineaArticuloSerializer(source='linea', read_only=True)

    class Meta:
        model = GrupoArticulo
        fields = [
            'grupo_id',
            'codigo_grupo',
            'nombre_grupo',
            'estado',
            'linea',  # Para escritura
            'linea_detalle',  # Para lectura
            'fecha_creacion',
            'fecha_modificacion'
        ]
        read_only_fields = ['grupo_id', 'fecha_creacion', 'fecha_modificacion']
    
    def create(self, validated_data):
        """Genera automáticamente el UUID"""
        validated_data['grupo_id'] = uuid.uuid4()
        return super().create(validated_data)


class ArticuloSerializer(serializers.ModelSerializer):
    """
    Serializador para Articulo
    Muestra grupo y línea anidados en lectura
    Permite escritura con grupo_id
    """
    # Campos anidados de solo lectura
    grupo_detalle = GrupoArticuloSerializer(source='grupo_id', read_only=True)
    linea_detalle = serializers.SerializerMethodField()
    
    # Campo para escritura (recibe el ID del grupo)
    grupo = serializers.PrimaryKeyRelatedField(
        queryset=GrupoArticulo.objects.all(),
        source='grupo_id',
        write_only=True
    )
    
    class Meta:
        model = Articulo
        fields = [
            'articulo_id',
            'codigo_articulo',
            'codigo_barras',
            'descripcion',
            'stock',
            'unidad_medida',
            'costo_actual',
            'precio_sugerido',
            'grupo',  # Para escritura
            'grupo_detalle',  # Para lectura (incluye grupo y línea)
            'linea_detalle',  # Para lectura (línea del grupo)
            'estado',
            'fecha_creacion',
            'fecha_modificacion'
        ]
        read_only_fields = ['articulo_id', 'fecha_creacion', 'fecha_modificacion']
    
    def create(self, validated_data):
        """Genera automáticamente el UUID"""
        validated_data['articulo_id'] = uuid.uuid4()
        return super().create(validated_data)
    
    def get_linea_detalle(self, obj):
        """
        Método para obtener los detalles de la línea a través del grupo
        """
        if obj.grupo_id and obj.grupo_id.linea:
            return LineaArticuloSerializer(obj.grupo_id.linea).data
        return None


class ArticuloListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar artículos
    Optimizado para rendimiento en listados
    """
    grupo_nombre = serializers.CharField(source='grupo_id.nombre_grupo', read_only=True)
    linea_nombre = serializers.CharField(source='grupo_id.linea.nombre_linea', read_only=True)
    
    class Meta:
        model = Articulo
        fields = [
            'articulo_id',
            'codigo_articulo',
            'descripcion',
            'stock',
            'unidad_medida',
            'precio_sugerido',
            'grupo_nombre',
            'linea_nombre',
            'estado'
        ]


class JerarquiaSerializer(serializers.Serializer):
    """
    Serializador para el endpoint de jerarquía completa
    Estructura: Líneas -> Grupos -> Artículos
    """
    linea_id = serializers.UUIDField()
    codigo_linea = serializers.CharField()
    nombre_linea = serializers.CharField()
    estado = serializers.IntegerField()
    grupos = serializers.SerializerMethodField()
    
    def get_grupos(self, obj):
        """
        Obtiene los grupos de la línea con sus artículos
        """
        grupos = []
        for grupo in obj.grupo_linea.all():
            articulos = []
            for articulo in grupo.grupo_articulo.all():
                articulos.append({
                    'articulo_id': str(articulo.articulo_id),
                    'codigo_articulo': articulo.codigo_articulo,
                    'descripcion': articulo.descripcion,
                    'stock': articulo.stock,
                    'unidad_medida': articulo.unidad_medida,
                    'precio_sugerido': str(articulo.precio_sugerido),
                    'estado': articulo.estado
                })
            
            grupos.append({
                'grupo_id': str(grupo.grupo_id),
                'codigo_grupo': grupo.codigo_grupo,
                'nombre_grupo': grupo.nombre_grupo,
                'estado': grupo.estado,
                'articulos': articulos
            })
        
        return grupos
