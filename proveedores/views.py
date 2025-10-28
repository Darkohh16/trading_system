from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Proveedor
from .serializers import ProveedorSerializer


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

    # /api/proveedores/listar/
    @action(detail=False, methods=['get'])
    def listar(self, request):
        proveedores = Proveedor.objects.filter(estado=1)

        serializer = self.get_serializer(proveedores, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    # /api/proveedores/crear/
    @action(detail=False, methods=['get', 'post'], url_path='crear')
    def crear(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer()
            return Response(serializer.data)

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
            
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # /api/proveedores/detalle/<proveedor_id>/
    @action(detail=True, methods=['get'])
    def detalle(self, request, pk=None):
        try:
            proveedor = Proveedor.objects.get(proveedor_id=pk)
        except Proveedor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Proveedor no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(proveedor)
        
        return Response({
            'success': True,
            
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='actualizar')
    def actualizar(self, request, pk=None):
        try:
            proveedor = Proveedor.objects.get(proveedor_id=pk)
        except Proveedor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Proveedor no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            # Mostrar formulario con datos del proveedor
            serializer = ProveedorSerializer(proveedor)
            return Response(serializer.data)

        # PUT o PATCH → actualizar datos
        serializer = ProveedorSerializer(proveedor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Proveedor actualizado correctamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['delete'], url_path='eliminar')
    def eliminar(self, request, pk=None):
        try:
            proveedor = Proveedor.objects.get(proveedor_id=pk)
        except Proveedor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Proveedor no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Soft delete → cambiar estado a 2 o "INACTIVO"
        proveedor.estado = 2
        proveedor.save()

        return Response({
            'success': True,
            'message': 'Proveedor desactivado correctamente'
        }, status=status.HTTP_200_OK)