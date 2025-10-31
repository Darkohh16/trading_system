import django_filters
from .models import Empresa, Sucursal


class EmpresaFilter(django_filters.FilterSet):
    """Filtros avanzados para Empresa"""
    
    # Filtros exactos
    ruc = django_filters.CharFilter(field_name='ruc', lookup_expr='exact')
    estado = django_filters.NumberFilter(field_name='estado')
    
    # Filtros con búsqueda parcial
    razon_social = django_filters.CharFilter(field_name='razon_social', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    
    # Filtros por rango de fechas
    fecha_creacion_desde = django_filters.DateTimeFilter(
        field_name='fecha_creacion', 
        lookup_expr='gte',
        label='Fecha creación desde'
    )
    fecha_creacion_hasta = django_filters.DateTimeFilter(
        field_name='fecha_creacion', 
        lookup_expr='lte',
        label='Fecha creación hasta'
    )
    
    # Búsqueda global
    search = django_filters.CharFilter(method='filter_search', label='Búsqueda general')
    
    class Meta:
        model = Empresa
        fields = {
            'ruc': ['exact'],
            'razon_social': ['exact', 'icontains'],
            'estado': ['exact'],
            'fecha_creacion': ['gte', 'lte', 'exact'],
        }
    
    def filter_search(self, queryset, name, value):
        """Búsqueda en múltiples campos"""
        from django.db.models import Q
        return queryset.filter(
            Q(ruc__icontains=value) |
            Q(razon_social__icontains=value) |
            Q(email__icontains=value) |
            Q(direccion__icontains=value)
        )


class SucursalFilter(django_filters.FilterSet):
    """Filtros avanzados para Sucursal"""
    
    # Filtros exactos
    codigo_sucursal = django_filters.CharFilter(field_name='codigo_sucursal', lookup_expr='exact')
    estado = django_filters.NumberFilter(field_name='estado')
    empresa_id = django_filters.NumberFilter(field_name='empresa__empresa_id')
    
    # Filtros con búsqueda parcial
    nombre_sucursal = django_filters.CharFilter(field_name='nombre_sucursal', lookup_expr='icontains')
    ciudad = django_filters.CharFilter(field_name='ciudad', lookup_expr='icontains')
    pais = django_filters.CharFilter(field_name='pais', lookup_expr='icontains')
    
    # Filtros por empresa
    empresa_ruc = django_filters.CharFilter(field_name='empresa__ruc', lookup_expr='exact')
    empresa_razon_social = django_filters.CharFilter(
        field_name='empresa__razon_social', 
        lookup_expr='icontains'
    )
    
    # Filtros por rango de fechas
    fecha_creacion_desde = django_filters.DateTimeFilter(
        field_name='fecha_creacion', 
        lookup_expr='gte'
    )
    fecha_creacion_hasta = django_filters.DateTimeFilter(
        field_name='fecha_creacion', 
        lookup_expr='lte'
    )
    
    # Búsqueda global
    search = django_filters.CharFilter(method='filter_search', label='Búsqueda general')
    
    class Meta:
        model = Sucursal
        fields = {
            'codigo_sucursal': ['exact', 'icontains'],
            'nombre_sucursal': ['exact', 'icontains'],
            'ciudad': ['exact', 'icontains'],
            'pais': ['exact', 'icontains'],
            'estado': ['exact'],
            'fecha_creacion': ['gte', 'lte', 'exact'],
        }
    
    def filter_search(self, queryset, name, value):
        """Búsqueda en múltiples campos incluyendo empresa"""
        from django.db.models import Q
        return queryset.filter(
            Q(codigo_sucursal__icontains=value) |
            Q(nombre_sucursal__icontains=value) |
            Q(ciudad__icontains=value) |
            Q(direccion__icontains=value) |
            Q(empresa__razon_social__icontains=value) |
            Q(empresa__ruc__icontains=value)
        )