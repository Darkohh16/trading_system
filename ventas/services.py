"""
Servicios para la lógica de negocio de Ventas.

Aquí se encapsulará la lógica compleja que no pertenece
directamente a las vistas o serializadores, como el cálculo de precios,
la aplicación de reglas y la gestión de stock.
"""
import dataclasses
from decimal import Decimal
from typing import List, Optional

from productos.models import Articulo
from clientes.models import Cliente
from precios.models import ListaPrecio, PrecioArticulo, ReglaPrecio
from trading_system.choices import EstadoOrden


@dataclasses.dataclass
class LineaCalculada:
    """Representa una línea de detalle de orden con precios calculados."""
    articulo: Articulo
    cantidad: int
    precio_base: Decimal
    precio_unitario: Decimal
    descuento: Decimal
    total_item: Decimal
    reglas_aplicadas: List[str] = dataclasses.field(default_factory=list)
    vendido_bajo_costo: bool = False


@dataclasses.dataclass
class PedidoCalculado:
    """Representa un pedido completo con sus totales calculados."""
    lineas: List[LineaCalculada]
    subtotal: Decimal
    descuento_total: Decimal
    total: Decimal
    cliente: Optional[Cliente] = None
    lista_precio: Optional[ListaPrecio] = None


class VentaService:
    """
    Servicio para gestionar la lógica de negocio de ventas.
    """

    def calcular_linea_articulo(self, articulo_id: str, cantidad: int, sucursal_id: int, canal: int) -> LineaCalculada:
        """
        Calcula el precio de un solo artículo.
        """
        articulo = Articulo.objects.get(articulo_id=articulo_id)

        lista_precio = ListaPrecio.objects.filter(
            sucursal_id=sucursal_id,
            canal=canal,
            estado=1
        ).first()

        if not lista_precio:
            raise ValueError("No se encontró una lista de precios activa para la sucursal y canal especificados.")

        try:
            precio_articulo = PrecioArticulo.objects.get(
                lista_precio=lista_precio,
                articulo=articulo
            )
            precio_base = precio_articulo.precio_base
        except PrecioArticulo.DoesNotExist:
            raise ValueError(f"El artículo {articulo.descripcion} no tiene un precio asignado en la lista '{lista_precio.nombre}'.")

        # Lógica de reglas a implementar aquí para un solo artículo
        precio_unitario = precio_base
        descuento_linea = Decimal('0.0')
        reglas_aplicadas = []

        total_item = (precio_unitario * cantidad) - descuento_linea

        return LineaCalculada(
            articulo=articulo,
            cantidad=cantidad,
            precio_base=precio_base,
            precio_unitario=precio_unitario,
            descuento=descuento_linea,
            total_item=total_item,
            reglas_aplicadas=reglas_aplicadas,
            vendido_bajo_costo=(precio_unitario < articulo.costo_actual)
        )

    def calcular_pedido(self, cliente_id: int, sucursal_id: int, canal: int, lineas: list) -> PedidoCalculado:
        """
        Calcula los precios, descuentos y totales para un pedido completo.

        Args:
            cliente_id: ID del cliente.
            sucursal_id: ID de la sucursal.
            canal: Canal de venta.
            lineas: Lista de diccionarios con {'articulo_id': id, 'cantidad': cant}.

        Returns:
            Un objeto PedidoCalculado con todos los totales.
        """
        # NOTA: Esta es una implementación inicial. La lógica de reglas se irá añadiendo.
        # Por ahora, solo busca el precio base.

        cliente = Cliente.objects.get(cliente_id=cliente_id)
        
        # 1. Encontrar la lista de precios aplicable (lógica simplificada)
        lista_precio = ListaPrecio.objects.filter(
            sucursal_id=sucursal_id,
            canal=canal,
            estado=1
        ).first()

        if not lista_precio:
            raise ValueError("No se encontró una lista de precios activa para la sucursal y canal especificados.")

        lineas_calculadas = []
        subtotal_pedido = Decimal('0.0')
        descuento_pedido = Decimal('0.0')

        for linea_data in lineas:
            linea_calculada = self.calcular_linea_articulo(
                articulo_id=linea_data['articulo_id'],
                cantidad=linea_data['cantidad'],
                sucursal_id=sucursal_id,
                canal=canal
            )
            lineas_calculadas.append(linea_calculada)
            subtotal_pedido += linea_calculada.precio_unitario * linea_calculada.cantidad
            descuento_pedido += linea_calculada.descuento

        # 5. Calcular totales del pedido
        total_pedido = subtotal_pedido - descuento_pedido

        return PedidoCalculado(
            lineas=lineas_calculadas,
            subtotal=subtotal_pedido,
            descuento_total=descuento_pedido,
            total=total_pedido,
            cliente=cliente,
            lista_precio=lista_precio
        )
