from rest_framework import serializers
from auditoria.models import HistorialPrecioArticulo, AuditoriaReglaPrecio, DescuentoProveedorAutorizado


class HistorialPrecioArticuloSerializer(serializers.ModelSerializer):
    """Serializer para HistorialPrecioArticulo"""
    
    articulo_nombre = serializers.CharField(source='articulo_id.descripcion', read_only=True)
    articulo_codigo = serializers.CharField(source='articulo_id.codigo_articulo', read_only=True)
    lista_precio_nombre = serializers.CharField(source='lista_precio.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = HistorialPrecioArticulo
        fields = [
            'historial_id',
            'articulo_id',
            'articulo_nombre',
            'articulo_codigo',
            'lista_precio',
            'lista_precio_nombre',
            'precio_anterior',
            'precio_nuevo',
            'fecha_cambio',
            'usuario',
            'usuario_nombre',
            'motivo',
        ]
        read_only_fields = ['historial_id', 'fecha_cambio']


class AuditoriaReglaPrecioSerializer(serializers.ModelSerializer):
    """Serializer para AuditoriaReglaPrecio"""
    
    regla_precio_codigo = serializers.CharField(source='regla_precio.codigo', read_only=True, allow_null=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)
    
    class Meta:
        model = AuditoriaReglaPrecio
        fields = [
            'auditoria_id',
            'regla_precio',
            'regla_precio_codigo',
            'regla_precio_id_backup',
            'codigo_regla',
            'accion',
            'accion_display',
            'valor_anterior',
            'valor_nuevo',
            'fecha_cambio',
            'usuario',
            'usuario_nombre',
        ]
        read_only_fields = ['auditoria_id', 'fecha_cambio']


class DescuentoProveedorAutorizadoSerializer(serializers.ModelSerializer):
    """Serializer para DescuentoProveedorAutorizado"""
    
    proveedor_nombre = serializers.CharField(source='proveedor.nombre_comercial', read_only=True)
    articulo_nombre = serializers.CharField(source='articulo.descripcion', read_only=True, allow_null=True)
    grupo_nombre = serializers.CharField(source='grupo.nombre_grupo', read_only=True, allow_null=True)
    linea_nombre = serializers.CharField(source='linea.nombre_linea', read_only=True, allow_null=True)
    autorizado_por_nombre = serializers.CharField(source='autorizado_por.username', read_only=True)
    
    class Meta:
        model = DescuentoProveedorAutorizado
        fields = [
            'descuento_id',
            'proveedor',
            'proveedor_nombre',
            'articulo',
            'articulo_nombre',
            'grupo',
            'grupo_nombre',
            'linea',
            'linea_nombre',
            'porcentaje_autorizado',
            'fecha_inicio',
            'fecha_fin',
            'estado',
            'autorizado_por',
            'autorizado_por_nombre',
            'fecha_autorizacion',
        ]
        read_only_fields = ['descuento_id', 'fecha_autorizacion']
