from django.db import models

class EstadoEntidades(models.IntegerChoices):
    ACTIVO = 1, "Activo"
    DE_BAJA = 0, "De baja"

class AccesoSistema(models.IntegerChoices):
    ADMINISTRADOR = 1, "Administrador"
    VENDEDOR = 2, "Usuario"
    INVITADO = 3, "Invitado"

class EstadoOrden(models.IntegerChoices):
    PENDIENTE = 1, "Pendiente"
    PROCESANDO = 2, "Procesando"
    COMPLETADA = 3, "Completada"
    CANCELADA = 4, "Cancelada"

class Tipo(models.IntegerChoices):
    MAYORISTA = 1, "Mayorista"
    MINORISTA = 2, "Minorista"

class CanalVenta(models.IntegerChoices):
    B2B = 1, "B2B"
    B2C = 2, "B2C"
    ECOMMERCE = 3, "E-Commerce"

class Moneda(models.IntegerChoices):
    USD = 1, "Dólar Estadounidense"
    EUR = 2, "Euro"
    SOL = 3, "Sol Peruano"

class TipoRegla(models.IntegerChoices):
    CANAL = 1, "Canal"
    ESCALA_CANTIDAD = 2, "Escala por Cantidad"
    ESCALA_MONTO = 3, "Escala por Monto"
    LINEA = 4, "Línea"
    GRUPO = 5, "Grupo"
    ARTICULO = 6, "Artículo"
    MONTO_PEDIDO = 7, "Monto Pedido"
    COMBINACION = 8, "Combinación"

class TipoDescuento(models.IntegerChoices):
    PORCENTAJE = 1, "Porcentaje"
    MONTO_FIJO = 2, "Monto Fijo"

class TipoBeneficio(models.IntegerChoices):
    DESCUENTO_PORCENTAJE = 1, "Descuento porcentaje"
    DESCUENTO_MONTO_FIJO = 2, "Descuento monto fijo"
    REGALO = 3, "Regalo"

class TipoItem(models.IntegerChoices):
    ARTICULO = 1, "Artículo"
    GRUPO = 2, "Grupo"
    LINEA = 3, "Línea"

class AccionAuditoria(models.IntegerChoices):
    CREACION = 1, "Creación"
    MODIFICACION = 2, "Modificación"
    ELIMINACION = 3, "Eliminación"