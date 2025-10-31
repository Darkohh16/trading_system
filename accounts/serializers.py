from rest_framework import serializers
from .models import Usuario
from core.models import Sucursal
from django.contrib.auth.password_validation import validate_password


class SucursalSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para mostrar sucursal en usuario"""
    empresa_razon_social = serializers.CharField(source='empresa.razon_social', read_only=True)
    
    class Meta:
        model = Sucursal
        fields = ['sucursal_id', 'codigo_sucursal', 'nombre_sucursal', 'empresa_razon_social']


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer completo para información de usuario"""
    sucursal_info = SucursalSimpleSerializer(source='sucursal', read_only=True)
    perfil_display = serializers.CharField(source='get_perfil_display', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'celular',
            'sucursal', 'sucursal_info', 'perfil', 'perfil_display',
            'puede_aprobar_bajo_costo', 'fecha_creacion', 'ultimo_acceso',
            'is_active', 'is_staff'
        ]
        read_only_fields = ['fecha_creacion', 'ultimo_acceso']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios (solo admin)"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'password', 'password2', 'first_name', 'last_name',
            'email', 'celular', 'sucursal', 'perfil', 'puede_aprobar_bajo_costo'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs
    
    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya existe")
        return value.lower()
    
    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value.lower()
    
    def validate_celular(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El celular debe contener solo números")
        if len(value) != 9:
            raise serializers.ValidationError("El celular debe tener 9 dígitos")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = Usuario.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar usuarios"""
    
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'email', 'celular',
            'sucursal', 'perfil', 'puede_aprobar_bajo_costo', 'is_active'
        ]
    
    def validate_email(self, value):
        if Usuario.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value.lower()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Las contraseñas no coinciden"})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta")
        return value


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para el perfil del usuario autenticado"""
    sucursal_info = SucursalSimpleSerializer(source='sucursal', read_only=True)
    perfil_display = serializers.CharField(source='get_perfil_display', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'celular',
            'sucursal_info', 'perfil', 'perfil_display',
            'puede_aprobar_bajo_costo', 'fecha_creacion', 'ultimo_acceso'
        ]
        read_only_fields = ['username', 'fecha_creacion', 'ultimo_acceso']