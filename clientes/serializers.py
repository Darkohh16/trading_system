from rest_framework import serializers
from .models import Cliente, HistorialCompra

class HistorialCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialCompra
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    historial = HistorialCompraSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['cliente_id', 'fecha_creacion', 'fecha_modificacion']
