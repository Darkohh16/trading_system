from rest_framework import serializers
from .models import Empresa, Sucursal


# Serializer con campos dinámicos

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    Serializer base con capacidad de campos dinámicos.
    Uso: 
        -?fields=empresa_id,ruc,razon_social 
        -?exclude=fecha_creacion,fecha_modificacion
    """
    def __init__(self, *args, **kwargs):
        # Obtener campos dinámicos del contexto
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)
        
        # Si vienen en el request
        request = kwargs.get('context', {}).get('request')
                # Permite controlar campos desde la URL (?fields= o ?exclude=)
        if request:
            query_fields = request.query_params.get('fields')
            query_exclude = request.query_params.get('exclude')
            if query_fields:
                fields = query_fields.split(',')
            if query_exclude:
                exclude = query_exclude.split(',')

        super().__init__(*args, **kwargs)

        # Evita conflicto simultáneo
        if fields and exclude:
            raise ValueError("No puedes usar 'fields' y 'exclude' al mismo tiempo.")

        # Filtrado de campos
        if fields is not None:
            allowed = set(fields)
            for field_name in set(self.fields.keys()) - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name, None)



# Serializers para Sucursal

class SucursalListSerializer(DynamicFieldsModelSerializer):
    """Serializer ligero para listado de sucursales"""
    empresa_razon_social = serializers.CharField(source='empresa.razon_social', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Sucursal
        fields = [
            'sucursal_id', 'codigo_sucursal', 'nombre_sucursal',
            'ciudad', 'pais', 'telefono', 'email',
            'empresa', 'empresa_razon_social',
            'estado', 'estado_display'
        ]
        read_only_fields = ['sucursal_id', 'empresa_razon_social', 'estado_display']


class SucursalDetailSerializer(DynamicFieldsModelSerializer):
    """Serializer completo para detalle de sucursal"""
    empresa_razon_social = serializers.CharField(source='empresa.razon_social', read_only=True)
    empresa_ruc = serializers.CharField(source='empresa.ruc', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Sucursal
        fields = '__all__'
        read_only_fields = ['sucursal_id', 'fecha_creacion', 'fecha_modificacion']
    
    def validate(self, data):
        """Validaciones personalizadas"""
        # Validar que la empresa esté activa
        if 'empresa' in data:
            from trading_system.choices import EstadoEntidades
            if data['empresa'].estado != EstadoEntidades.ACTIVO:
                raise serializers.ValidationError({
                    "empresa": "No se puede asignar una empresa inactiva"
                })
        
        return data


class SucursalCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para creación y actualización"""
    
    class Meta:
        model = Sucursal
        fields = [
            'codigo_sucursal', 'nombre_sucursal', 'direccion',
            'telefono', 'email', 'ciudad', 'pais', 'codigo_postal',
            'empresa', 'estado'
        ]
    
    def validate_codigo_sucursal(self, value):
        """Validar código único"""
        if self.instance:  # Actualizar
            if Sucursal.objects.exclude(pk=self.instance.pk).filter(codigo_sucursal=value).exists():
                raise serializers.ValidationError("Este código de sucursal ya existe")
        else:  # Create
            if Sucursal.objects.filter(codigo_sucursal=value).exists():
                raise serializers.ValidationError("Este código de sucursal ya existe")
        return value.upper()
    
    def validate_nombre_sucursal(self, value):
        """Validar nombre"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres")
        return value.strip()


# Serializers para Empresa

class EmpresaListSerializer(DynamicFieldsModelSerializer):
    """Serializer ligero para listado de empresas"""
    cantidad_sucursales = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Empresa
        fields = [
            'empresa_id', 'ruc', 'razon_social',
            'telefono', 'email', 'sitio_web',
            'estado', 'estado_display', 'cantidad_sucursales'
        ]
        read_only_fields = ['empresa_id', 'estado_display', 'cantidad_sucursales']
    
    def get_cantidad_sucursales(self, obj):
        """Contar sucursales activas"""
        from trading_system.choices import EstadoEntidades
        return obj.sucursales_empresa.filter(estado=EstadoEntidades.ACTIVO).count()


class EmpresaDetailSerializer(DynamicFieldsModelSerializer):
    """Serializer completo con sucursales anidadas"""
    sucursales = SucursalListSerializer(source='sucursales_empresa', many=True, read_only=True)
    cantidad_sucursales = serializers.SerializerMethodField()
    sucursales_activas = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Empresa
        fields = '__all__'
        read_only_fields = ['empresa_id', 'fecha_creacion', 'fecha_modificacion']
    
    def get_cantidad_sucursales(self, obj):
        """Total de sucursales"""
        return obj.sucursales_empresa.count()
    
    def get_sucursales_activas(self, obj):
        """Sucursales activas"""
        from trading_system.choices import EstadoEntidades
        return obj.sucursales_empresa.filter(estado=EstadoEntidades.ACTIVO).count()
    
    def to_representation(self, instance):
        """Personalizar representación según contexto"""
        representation = super().to_representation(instance)
        
        # Incluir sucursales solo si se solicita explícitamente
        request = self.context.get('request')
        if request:
            include_sucursales = request.query_params.get('include_sucursales', 'false')
            if include_sucursales.lower() != 'true':
                representation.pop('sucursales', None)
        
        return representation


class EmpresaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para creación y actualización de empresas"""
    
    class Meta:
        model = Empresa
        fields = [
            'ruc', 'razon_social', 'direccion',
            'telefono', 'email', 'sitio_web', 'estado'
        ]
    
    def validate_ruc(self, value):
        """Validar RUC único y formato"""
        # Limpiar espacios
        value = value.strip()
        
        if not value.isdigit():
            raise serializers.ValidationError("El RUC debe contener solo números")
        
        if len(value) != 11:
            raise serializers.ValidationError("El RUC debe tener exactamente 11 dígitos")
        
        # Validar que sea único
        if self.instance:  # Actualizar
            if Empresa.objects.exclude(pk=self.instance.pk).filter(ruc=value).exists():
                raise serializers.ValidationError("Este RUC ya está registrado")
        else:  # Crear
            if Empresa.objects.filter(ruc=value).exists():
                raise serializers.ValidationError("Este RUC ya está registrado")
        
        return value
    
    def validate_razon_social(self, value):
        """Validar razón social"""
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("La razón social debe tener al menos 3 caracteres")
        return value.upper()
    
    def validate_email(self, value):
        """Validar email si se proporciona"""
        if value:
            value = value.strip().lower()
        return value


# Serializer con sucursales completamente anidadas (detalle completo)

class EmpresaConSucursalesSerializer(DynamicFieldsModelSerializer):
    """Serializer con sucursales completamente anidadas (detalle completo)"""
    sucursales = SucursalDetailSerializer(source='sucursales_empresa', many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Empresa
        fields = '__all__'
        read_only_fields = ['empresa_id', 'fecha_creacion', 'fecha_modificacion']


# Serializer para estadísticas de empresa

class EmpresaStatsSerializer(serializers.ModelSerializer):
    """Serializer para estadísticas de empresa"""
    total_sucursales = serializers.SerializerMethodField()
    sucursales_activas = serializers.SerializerMethodField()
    sucursales_inactivas = serializers.SerializerMethodField()
    sucursales_por_ciudad = serializers.SerializerMethodField()
    
    class Meta:
        model = Empresa
        fields = [
            'empresa_id', 'ruc', 'razon_social',
            'total_sucursales', 'sucursales_activas', 'sucursales_inactivas',
            'sucursales_por_ciudad'
        ]
    
    def get_total_sucursales(self, obj):
        return obj.sucursales_empresa.count()
    
    def get_sucursales_activas(self, obj):
        from trading_system.choices import EstadoEntidades
        return obj.sucursales_empresa.filter(estado=EstadoEntidades.ACTIVO).count()
    
    def get_sucursales_inactivas(self, obj):
        from trading_system.choices import EstadoEntidades
        return obj.sucursales_empresa.filter(estado=EstadoEntidades.INACTIVO).count()
    
    def get_sucursales_por_ciudad(self, obj):
        """Contar sucursales por ciudad"""
        from django.db.models import Count
        ciudades = obj.sucursales_empresa.values('ciudad').annotate(
            cantidad=Count('sucursal_id')
        ).order_by('-cantidad')
        return {item['ciudad'] or 'Sin ciudad': item['cantidad'] for item in ciudades}


# Serializers para bulk de operaciones

class BulkSucursalSerializer(serializers.ListSerializer):
    """Serializer para operaciones en lote de sucursales"""
    
    def create(self, validated_data):
        """Crear múltiples sucursales en una transacción"""
        sucursales = [Sucursal(**item) for item in validated_data]
        return Sucursal.objects.bulk_create(sucursales)
    
    def update(self, instance, validated_data):
        """Actualizar múltiples sucursales"""
        # Mapear instancias por ID
        sucursal_mapping = {sucursal.sucursal_id: sucursal for sucursal in instance}
        data_mapping = {item['sucursal_id']: item for item in validated_data}
        
        # Actualizar
        ret = []
        for sucursal_id, data in data_mapping.items():
            sucursal = sucursal_mapping.get(sucursal_id, None)
            if sucursal:
                ret.append(self.child.update(sucursal, data))
        
        return ret


class SucursalBulkCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación masiva de sucursales"""
    
    class Meta:
        model = Sucursal
        fields = [
            'codigo_sucursal', 'nombre_sucursal', 'direccion',
            'telefono', 'email', 'ciudad', 'pais', 'codigo_postal',
            'empresa', 'estado'
        ]
        list_serializer_class = BulkSucursalSerializer

