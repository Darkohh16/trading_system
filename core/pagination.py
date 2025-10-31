from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginación estándar con parámetros configurables.
    Uso: ?page=1&page_size=20
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """Respuesta personalizada con metadatos adicionales"""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.page_size),
            ('results', data)
        ]))


class LargeResultsSetPagination(PageNumberPagination):
    """
    Paginación para conjuntos grandes de datos.
    Página por defecto: 50 items
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """
    Paginación para listados pequeños.
    Página por defecto: 5 items
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """
    Paginación con limit y offset.
    Uso: ?limit=20&offset=40
    """
    default_limit = 10
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_paginated_response(self, data):
        """Respuesta personalizada"""
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('limit', self.get_limit(self.request)),
            ('offset', self.get_offset(self.request)),
            ('results', data)
        ]))


class CustomCursorPagination(CursorPagination):
    """
    Paginación con cursor (más eficiente para grandes volúmenes).
    Uso: ?cursor=cD0yMDIz...
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-fecha_creacion'  # Campo por el que se ordena
    cursor_query_param = 'cursor'