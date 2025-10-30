from rest_framework import serializers
from .models import Proveedor


class ProveedorSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Proveedor.
    Convierte el modelo a JSON y valida los datos recibidos.
    """
    
    class Meta:
        model = Proveedor
        fields = '__all__'  # Incluye todos los campos del modelo
        read_only_fields = ('proveedor_id', 'fecha_creacion', 'fecha_modificacion')  # Estos campos NO se pueden modificar desde la API
    
    
    # ===== VALIDACIONES PERSONALIZADAS =====
    
    def validate_ruc(self, value):
        """
        Valida que el RUC sea correcto:
        - Solo números
        - Exactamente 11 dígitos
        """
        if not value:
            raise serializers.ValidationError("El RUC es obligatorio")
        
        if not value.isdigit():
            raise serializers.ValidationError("El RUC debe contener solo números")
        
        if len(value) != 11:
            raise serializers.ValidationError("El RUC debe tener exactamente 11 dígitos")
        
        return value
    
    
    def validate_email(self, value):
        """
        Valida el formato del email (Django ya hace esto, pero podemos agregar validaciones extra)
        """
        if value:  # Si el email no es obligatorio pero se proporciona
            value = value.lower()  # Convertir a minúsculas
        return value
    
    
    def validate(self, data):
        """
        Validaciones a nivel de objeto (cuando se necesitan validar múltiples campos juntos)
        """
        # Validar que nombre_comercial y razon_social no sean iguales (opcional)
        nombre_comercial = data.get('nombre_comercial', '').strip()
        razon_social = data.get('razon_social', '').strip()
        
        if nombre_comercial and razon_social:
            if nombre_comercial == razon_social:
                # Esto es solo una advertencia, no un error
                # Puedes quitarlo si no lo necesitas
                pass
        
        return data
    
    
    def to_representation(self, instance):
        """
        Personaliza cómo se representa el objeto en JSON
        (Opcional: útil para formatear fechas, agregar campos calculados, etc.)
        """
        representation = super().to_representation(instance)
        
        # Formatear las fechas en un formato más legible
        if instance.fecha_creacion:
            representation['fecha_creacion'] = instance.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        
        if instance.fecha_modificacion:
            representation['fecha_modificacion'] = instance.fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S')
        
        # Agregar el estado en texto (no solo el número)
        estado_dict = {
            1: 'ACTIVO',
            0: 'INACTIVO'
        }
        representation['estado_texto'] = estado_dict.get(instance.estado, 'DESCONOCIDO')
        
        return representation