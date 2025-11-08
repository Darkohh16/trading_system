from rest_framework import serializers
from .models import Cliente, HistorialCompra

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['cliente_id', 'fecha_creacion', 'fecha_modificacion']

class HistorialCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialCompra
        fields = '__all__'
