from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    API para gestionar clientes:
    - Listar, crear, actualizar, eliminar
    - Buscar clientes por nombre, documento o razón social
    - Ver historial y estadísticas de compras
    """
    permission_classes = [IsAuthenticated]
    queryset = Cliente.objects.all().order_by('nombre_comercial')
    serializer_class = ClienteSerializer

    # Filtros de búsqueda integrados (aparecen en la interfaz DRF)
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre_comercial', 'nro_documento', 'razon_social']

    # -------------------------
    #   MÉTODOS PERSONALIZADOS
    # -------------------------

    @action(detail=True, methods=['get'], url_path='historial')
    def historial_compras(self, request, pk=None):
        """
        Obtiene el historial de compras del cliente.
        (Datos simulados para demostración)
        """
        try:
            cliente = self.get_object()
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        historial = [
            {"fecha": "2025-10-10", "producto": "Laptop Lenovo", "total": 3200},
            {"fecha": "2025-09-22", "producto": "Mouse Logitech", "total": 120},
            {"fecha": "2025-09-05", "producto": "Monitor Samsung", "total": 950},
        ]
        return Response({
            "cliente": cliente.nombre_comercial,
            "historial_compras": historial
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request, pk=None):
        """
        Devuelve estadísticas de compras del cliente.
        (Datos simulados para entrega)
        """
        try:
            cliente = self.get_object()
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        estadisticas = {
            "total_compras": 15,
            "monto_total": 7850,
            "promedio_por_compra": 523.33,
            "producto_mas_comprado": "Teclado Mecánico RGB",
            "ultima_compra": "2025-10-10"
        }

        return Response({
            "cliente": cliente.nombre_comercial,
            "estadisticas": estadisticas
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instancia = self.get_object()
        instancia.estado = 0
        instancia.save()

        return Response(
            {'message': 'Cliente desactivado correctamente.'},
            status=status.HTTP_200_OK
        )