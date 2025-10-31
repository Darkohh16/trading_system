import django_filters
from precios.models import ListaPrecio

class ListaPrecioFilter(django_filters.FilterSet):

    empresa = django_filters.NumberFilter(field_name='empresa')
    sucursal = django_filters.NumberFilter(field_name='sucursal')
    canal = django_filters.NumberFilter(field_name='canal')
    tipo = django_filters.NumberFilter(field_name='tipo')
    estado = django_filters.NumberFilter(field_name='estado')
    fecha_vigencia_inicio_desde = django_filters.DateFilter(field_name='fecha_vigencia_inicio', lookup_expr='gte')
    fecha_vigencia_inicio_hasta = django_filters.DateFilter(field_name='fecha_vigencia_inicio', lookup_expr='lte')

    class Meta:
        model = ListaPrecio
        fields = [
            'empresa',
            'sucursal',
            'canal',
            'tipo',
            'estado',
        ]