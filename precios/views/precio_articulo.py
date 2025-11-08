from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from precios.models import ListaPrecio, PrecioArticulo
from precios.serializers.lista_precio import ListaPrecioSerializer, ListaPrecioCrearActualizarSerializer
from precios.serializers.precio_articulo import *
from auditoria.signals import set_current_user, set_audit_motivo

class PrecioArticuloViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PrecioArticulo.objects.select_related(
            'lista_precio',
            'articulo',
            'articulo__grupo',
        ).all()

        lista_precio_id = self.request.query_params.get('lista_precio')
        if lista_precio_id:
            queryset = queryset.filter(lista_precio_id=lista_precio_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return PrecioArticuloListSerializer
        elif self.action == 'retrieve':
            return PrecioArticuloDetalleSerializer
        else:
            return PrecioArticuloCrearActualizarSerializer

    def perform_create(self, serializer):
        """Establece el contexto de auditoría antes de crear"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        
        motivo = self.request.data.get('motivo', None)
        if motivo:
            set_audit_motivo(motivo)
        
        serializer.save()

    def perform_update(self, serializer):
        """Establece el contexto de auditoría antes de actualizar"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        
        motivo = self.request.data.get('motivo', None)
        if motivo:
            set_audit_motivo(motivo)
        
        serializer.save()


#precios en la lista
class ListaPrecioArticuloViewSet(viewsets.ModelViewSet):
    """
    - GET    /api/listas/{lista_id}/precios/
    - POST   /api/listas/{lista_id}/precios/
    - GET    /api/listas/{lista_id}/precios/{id}/
    - PUT    /api/listas/{lista_id}/precios/{id}/
    - DELETE /api/listas/{lista_id}/precios/{id}/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ListaPrecioCrearActualizarSerializer

    def get_queryset(self):
        #Filtrar solo precios de esta lista
        lista_id = self.kwargs.get('lista_id')
        return PrecioArticulo.objects.filter(lista_precio_id=lista_id).select_related('articulo')

    def get_serializer_class(self):
        if self.action == 'list':
            return PrecioArticuloListSerializer
        elif self.action == 'retrieve':
            return PrecioArticuloDetalleSerializer
        else:
            return PrecioArticuloCrearActualizarSerializer

    def perform_create(self, serializer):
        """Establece el contexto de auditoría antes de crear"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        
        motivo = self.request.data.get('motivo', None)
        if motivo:
            set_audit_motivo(motivo)
        
        serializer.save()

    def perform_update(self, serializer):
        """Establece el contexto de auditoría antes de actualizar"""
        if self.request.user.is_authenticated:
            set_current_user(self.request.user)
        
        motivo = self.request.data.get('motivo', None)
        if motivo:
            set_audit_motivo(motivo)
        
        serializer.save()

    def create(self, request, *args, **kwargs):
        lista_id = self.kwargs.get('lista_id')

        #existe
        try:
            lista = ListaPrecio.objects.get(lista_precio_id=lista_id)
        except ListaPrecio.DoesNotExist:
            return Response({'error': 'Lista de precios no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        #agregar listaprecio al data
        data = request.data.copy()
        data['lista_precio'] = lista_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)