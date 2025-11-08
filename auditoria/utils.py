from contextlib import contextmanager
from auditoria.signals import set_current_user, set_audit_motivo, get_current_user, get_audit_motivo


@contextmanager
def auditoria_context(usuario, motivo=None):
    """
    Context manager para establecer el contexto de auditoría temporalmente
    
    Uso:
        with auditoria_context(usuario, motivo="Actualización masiva"):
            # Operaciones que se auditarán
            precio.save()
    """
    usuario_anterior = get_current_user()
    motivo_anterior = get_audit_motivo()
    
    try:
        set_current_user(usuario)
        if motivo:
            set_audit_motivo(motivo)
        yield
    finally:
        set_current_user(usuario_anterior)
        set_audit_motivo(motivo_anterior)


def registrar_cambio_precio(precio_articulo, usuario, motivo="Cambio de precio"):
    """
    Función helper para registrar manualmente un cambio de precio
    
    Args:
        precio_articulo: Instancia de PrecioArticulo
        usuario: Usuario que realiza el cambio
        motivo: Motivo del cambio
    
    Uso:
        registrar_cambio_precio(precio, request.user, "Ajuste por promoción")
    """
    from auditoria.models import HistorialPrecioArticulo
    from precios.models import PrecioArticulo
    
    # Obtener el precio anterior si existe
    try:
        precio_anterior_obj = PrecioArticulo.objects.get(pk=precio_articulo.pk)
        precio_anterior = precio_anterior_obj.precio_base
    except PrecioArticulo.DoesNotExist:
        precio_anterior = 0
    
    # Registrar en el historial
    HistorialPrecioArticulo.objects.create(
        articulo_id=precio_articulo.articulo,
        lista_precio=precio_articulo.lista_precio,
        precio_anterior=precio_anterior,
        precio_nuevo=precio_articulo.precio_base,
        usuario=usuario,
        motivo=motivo
    )


def obtener_historial_precio(articulo, lista_precio=None, limit=10):
    """
    Obtiene el historial de cambios de precio para un artículo
    
    Args:
        articulo: Instancia de Articulo
        lista_precio: Instancia de ListaPrecio (opcional, filtra por lista)
        limit: Número máximo de registros a retornar
    
    Returns:
        QuerySet de HistorialPrecioArticulo
    """
    from auditoria.models import HistorialPrecioArticulo
    
    queryset = HistorialPrecioArticulo.objects.filter(articulo_id=articulo)
    
    if lista_precio:
        queryset = queryset.filter(lista_precio=lista_precio)
    
    return queryset[:limit]


def obtener_auditoria_regla(regla_precio, limit=10):
    """
    Obtiene el historial de auditoría para una regla de precio
    
    Args:
        regla_precio: Instancia de ReglaPrecio
        limit: Número máximo de registros a retornar
    
    Returns:
        QuerySet de AuditoriaReglaPrecio
    """
    from auditoria.models import AuditoriaReglaPrecio
    
    return AuditoriaReglaPrecio.objects.filter(regla_precio=regla_precio)[:limit]
