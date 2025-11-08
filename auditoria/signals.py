import json
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from precios.models import PrecioArticulo, ReglaPrecio
from auditoria.models import HistorialPrecioArticulo, AuditoriaReglaPrecio
from trading_system.choices import AccionAuditoria


# Variable thread-local para almacenar el usuario y motivo durante la solicitud
import threading
_thread_locals = threading.local()


def set_current_user(user):
    """Establece el usuario actual en el contexto thread-local"""
    _thread_locals.user = user


def get_current_user():
    """Obtiene el usuario actual del contexto thread-local"""
    return getattr(_thread_locals, 'user', None)


def set_audit_motivo(motivo):
    """Establece el motivo de auditoría en el contexto thread-local"""
    _thread_locals.motivo = motivo


def get_audit_motivo():
    """Obtiene el motivo de auditoría del contexto thread-local"""
    return getattr(_thread_locals, 'motivo', 'Cambio realizado desde el sistema')


@receiver(pre_save, sender=PrecioArticulo)
def precio_articulo_pre_save(sender, instance, **kwargs):
    """
    Captura el precio anterior antes de guardar para poder registrarlo en el historial
    """
    if instance.pk:  # Solo para actualizaciones, no para creaciones
        try:
            # Obtener la instancia anterior desde la base de datos
            instance._precio_anterior = PrecioArticulo.objects.get(pk=instance.pk)
        except PrecioArticulo.DoesNotExist:
            instance._precio_anterior = None
    else:
        instance._precio_anterior = None


@receiver(post_save, sender=PrecioArticulo)
def precio_articulo_post_save(sender, instance, created, **kwargs):
    """
    Registra en el historial cuando se crea o actualiza un PrecioArticulo
    """
    usuario = get_current_user()
    motivo = get_audit_motivo()
    
    if created:
        # Para creaciones, el precio anterior es 0 o None
        precio_anterior = 0
        precio_nuevo = instance.precio_base
        motivo_final = motivo if motivo else "Creación de precio inicial"
    else:
        # Para actualizaciones, usar el precio capturado en pre_save
        if hasattr(instance, '_precio_anterior') and instance._precio_anterior:
            precio_anterior = instance._precio_anterior.precio_base
        else:
            # Si no se capturó, intentar obtenerlo de otra forma
            precio_anterior = 0
        precio_nuevo = instance.precio_base
        motivo_final = motivo if motivo else "Actualización de precio"
    
    # Solo registrar si hay un usuario y si el precio cambió
    if usuario and precio_anterior != precio_nuevo:
        HistorialPrecioArticulo.objects.create(
            articulo_id=instance.articulo,
            lista_precio=instance.lista_precio,
            precio_anterior=precio_anterior,
            precio_nuevo=precio_nuevo,
            usuario=usuario,
            motivo=motivo_final
        )


def _serialize_regla_precio(regla):
    """
    Serializa una instancia de ReglaPrecio a un diccionario para auditoría
    """
    return {
        'regla_precio_id': str(regla.regla_precio_id),
        'codigo': regla.codigo,
        'lista_precio_id': str(regla.lista_precio.lista_precio_id),
        'tipo_regla': regla.tipo_regla,
        'prioridad': regla.prioridad,
        'aplica_canal': regla.aplica_canal,
        'aplica_linea_id': str(regla.aplica_linea.linea_id) if regla.aplica_linea else None,
        'aplica_grupo_id': str(regla.aplica_grupo.grupo_id) if regla.aplica_grupo else None,
        'aplica_articulo_id': str(regla.aplica_articulo.articulo_id) if regla.aplica_articulo else None,
        'cantidad_minima': regla.cantidad_minima,
        'monto_minimo': float(regla.monto_minimo) if regla.monto_minimo else None,
        'tipo_descuento': regla.tipo_descuento,
        'valor_descuento': float(regla.valor_descuento),
        'fecha_inicio': regla.fecha_inicio.isoformat() if regla.fecha_inicio else None,
        'fecha_fin': regla.fecha_fin.isoformat() if regla.fecha_fin else None,
        'descripcion': regla.descripcion,
        'estado': regla.estado,
    }


@receiver(pre_save, sender=ReglaPrecio)
def regla_precio_pre_save(sender, instance, **kwargs):
    """
    Captura los valores anteriores antes de guardar para poder registrarlos en auditoría
    """
    if instance.pk:  # Solo para actualizaciones
        try:
            instance._regla_anterior = ReglaPrecio.objects.get(pk=instance.pk)
        except ReglaPrecio.DoesNotExist:
            instance._regla_anterior = None
    else:
        instance._regla_anterior = None


@receiver(post_save, sender=ReglaPrecio)
def regla_precio_post_save(sender, instance, created, **kwargs):
    """
    Registra en auditoría cuando se crea o actualiza una ReglaPrecio
    """
    usuario = get_current_user()
    
    if not usuario:
        return
    
    if created:
        # Para creaciones
        AuditoriaReglaPrecio.objects.create(
            regla_precio=instance,
            accion=AccionAuditoria.CREACION,
            valor_anterior=None,
            valor_nuevo=_serialize_regla_precio(instance),
            usuario=usuario
        )
    else:
        # Para actualizaciones, comparar valores anteriores y nuevos
        if hasattr(instance, '_regla_anterior') and instance._regla_anterior:
            valor_anterior = _serialize_regla_precio(instance._regla_anterior)
            valor_nuevo = _serialize_regla_precio(instance)
            
            # Solo registrar si hubo cambios
            if valor_anterior != valor_nuevo:
                AuditoriaReglaPrecio.objects.create(
                    regla_precio=instance,
                    accion=AccionAuditoria.MODIFICACION,
                    valor_anterior=valor_anterior,
                    valor_nuevo=valor_nuevo,
                    usuario=usuario
                )


@receiver(pre_delete, sender=ReglaPrecio)
def regla_precio_pre_delete(sender, instance, **kwargs):
    """
    Registra en auditoría cuando se elimina una ReglaPrecio
    Se ejecuta antes de eliminar para poder acceder a la relación FK
    """
    usuario = get_current_user()
    
    if usuario:
        # Serializar los datos antes de eliminar
        valor_anterior = _serialize_regla_precio(instance)
        regla_id = instance.regla_precio_id
        codigo_regla = instance.codigo
        
        # Crear el registro de auditoría antes de que se elimine la instancia
        AuditoriaReglaPrecio.objects.create(
            regla_precio=instance,  # La instancia aún existe aquí (pre_delete)
            regla_precio_id_backup=regla_id,  # Guardamos el ID como backup
            codigo_regla=codigo_regla,  # Guardamos el código para referencia
            accion=AccionAuditoria.ELIMINACION,
            valor_anterior=valor_anterior,
            valor_nuevo=None,
            usuario=usuario
        )
