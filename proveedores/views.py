from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Proveedor
from .serializers import ProveedorSerializer


class ProveedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar todas las operaciones CRUD de Proveedores.
    
    Endpoints disponibles:
    - GET    /api/proveedores/          → Listar todos los proveedores
    - POST   /api/proveedores/          → Crear un nuevo proveedor
    - GET    /api/proveedores/{id}/     → Obtener detalle de un proveedor
    - PUT    /api/proveedores/{id}/     → Actualizar completamente un proveedor
    - PATCH  /api/proveedores/{id}/     → Actualizar parcialmente un proveedor
    - DELETE /api/proveedores/{id}/     → Eliminar un proveedor
    """
    
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    lookup_field = 'proveedor_id'  # Usamos proveedor_id en lugar de pk en las URLs
    
    
    def list(self, request, *args, **kwargs):
        """
        GET /api/proveedores/
        Lista todos los proveedores activos (opcionalmente puedes filtrar por estado)
        """
        # Obtener parámetros de query (opcional)
        estado = request.query_params.get('estado', None)
        
        # Filtrar por estado si se proporciona
        queryset = self.get_queryset()
        if estado is not None:
            queryset = queryset.filter(estado=estado)
        
        # Serializar los datos
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    
    def create(self, request, *args, **kwargs):
        """
        POST /api/proveedores/
        Crea un nuevo proveedor
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Proveedor creado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Error al crear el proveedor',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    
    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/proveedores/{id}/
        Obtiene el detalle de un proveedor específico
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    
    def update(self, request, *args, **kwargs):
        """
        PUT /api/proveedores/{id}/
        Actualiza completamente un proveedor (requiere todos los campos)
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Proveedor actualizado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Error al actualizar el proveedor',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/proveedores/{id}/
        Actualiza parcialmente un proveedor (solo los campos enviados)
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/proveedores/{id}/
        Elimina un proveedor
        """
        instance = self.get_object()
        nombre = instance.nombre_comercial
        instance.delete()
        
        return Response({
            'success': True,
            'message': f'Proveedor "{nombre}" eliminado exitosamente'
        }, status=status.HTTP_200_OK)
    
    
    # ===== ENDPOINTS PERSONALIZADOS (OPCIONAL) =====
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        GET /api/proveedores/activos/
        Lista solo los proveedores activos
        """
        proveedores = self.get_queryset().filter(estado=1)
        serializer = self.get_serializer(proveedores, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=['post'])
    def activar(self, request, proveedor_id=None):
        """
        POST /api/proveedores/{id}/activar/
        Activa un proveedor inactivo
        """
        proveedor = self.get_object()
        proveedor.estado = 1
        proveedor.save()
        
        serializer = self.get_serializer(proveedor)
        
        return Response({
            'success': True,
            'message': f'Proveedor "{proveedor.nombre_comercial}" activado',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=['post'])
    def desactivar(self, request, proveedor_id=None):
        """
        POST /api/proveedores/{id}/desactivar/
        Desactiva un proveedor (soft delete)
        """
        proveedor = self.get_object()
        proveedor.estado = 0
        proveedor.save()
        
        serializer = self.get_serializer(proveedor)
        
        return Response({
            'success': True,
            'message': f'Proveedor "{proveedor.nombre_comercial}" desactivado',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
