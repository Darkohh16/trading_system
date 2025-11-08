from datetime import date
from decimal import Decimal
from django.db.models import Q

from precios.models import PrecioArticulo, ReglaPrecio, ListaPrecio
from productos.models import Articulo
from trading_system.choices import EstadoEntidades, TipoRegla, TipoDescuento, CanalVenta


def calculate_price(articulo: Articulo, lista_precio: ListaPrecio, canal: int, cantidad: int):
    """
    Calcula el precio final de un artículo aplicando las reglas de precios correspondientes.

    Args:
        articulo (Articulo): La instancia del artículo.
        lista_precio (ListaPrecio): La lista de precios a aplicar.
        canal (int): El canal de venta (de trading_system.choices.CanalVenta).
        cantidad (int): La cantidad de artículos que se están comprando.

    Returns:
        dict: Un diccionario con el resultado del cálculo.
            {
                "precio_base": Decimal,
                "precio_final": Decimal,
                "descuento_total": Decimal,
                "reglas_aplicadas": list[str],
                "vendido_bajo_costo": bool,
                "error": str # Si ocurre un error
            }
    """
    today = date.today()
    
    # 1. Obtener el precio base y mínimo del artículo en la lista de precios
    try:
        precio_info = PrecioArticulo.objects.get(
            lista_precio=lista_precio,
            articulo=articulo,
            estado=EstadoEntidades.ACTIVO
        )
        precio_base = precio_info.precio_base
        precio_minimo = precio_info.precio_minimo
    except PrecioArticulo.DoesNotExist:
        # Si no hay un precio definido, no se puede vender.
        return {
            "error": f"El artículo {articulo.descripcion} no tiene un precio definido en la lista {lista_precio.nombre}."
        }

    # 2. Inicializar variables
    precio_calculado = precio_base
    descuento_total = Decimal('0.0')
    reglas_aplicadas = []

    # 3. Buscar y filtrar todas las reglas de precios aplicables
    # Filtro por jerarquía de producto: artículo, grupo o línea
    # Se asume que Articulo tiene un FK a GrupoArticulo y GrupoArticulo a LineaArticulo
    q_rules = Q(lista_precio=lista_precio) & \
              Q(estado=EstadoEntidades.ACTIVO) & \
              Q(fecha_inicio__lte=today) & \
              Q(fecha_fin__gte=today) & \
              (
               Q(aplica_articulo=articulo) |
               Q(aplica_grupo=articulo.grupo_id) |
               Q(aplica_linea=articulo.grupo_id.linea))
    
    # Filtro por canal de venta (si la regla lo especifica)
    q_rules &= (Q(aplica_canal__isnull=True) | Q(aplica_canal='') | Q(aplica_canal=str(canal)))
    
    # Filtro por cantidad mínima
    q_rules &= (Q(cantidad_minima__isnull=True) | Q(cantidad_minima__lte=cantidad))

    reglas = ReglaPrecio.objects.filter(q_rules).order_by('prioridad')

    # 4. Aplicar las reglas en orden de prioridad
    for regla in reglas:
        descuento_de_regla = Decimal('0.0')
        
        if regla.tipo_regla == TipoRegla.PRECIO_FINAL:
            # Esta regla establece un precio final, ignorando cálculos anteriores.
            # El descuento se calcula como la diferencia para fines informativos.
            descuento_de_regla = precio_calculado - regla.valor_descuento
            precio_calculado = regla.valor_descuento
        
        elif regla.tipo_regla == TipoRegla.DESCUENTO:
            if regla.tipo_descuento == TipoDescuento.PORCENTAJE:
                descuento_de_regla = (precio_calculado * regla.valor_descuento) / 100
            elif regla.tipo_descuento == TipoDescuento.MONTO:
                descuento_de_regla = regla.valor_descuento
            
            precio_calculado -= descuento_de_regla
        
        elif regla.tipo_regla == TipoRegla.RECARGO:
            if regla.tipo_descuento == TipoDescuento.PORCENTAJE:
                recargo = (precio_calculado * regla.valor_descuento) / 100
                precio_calculado += recargo
                # El recargo se trata como un descuento negativo
                descuento_de_regla = -recargo
            elif regla.tipo_descuento == TipoDescuento.MONTO:
                precio_calculado += regla.valor_descuento
                descuento_de_regla = -regla.valor_descuento

        if descuento_de_regla != Decimal('0.0'):
            descuento_total += descuento_de_regla
            reglas_aplicadas.append(regla.descripcion)

    # 5. Validar contra el precio mínimo
    if precio_calculado < precio_minimo:
        # Si el precio calculado es menor que el mínimo, se ajusta al mínimo.
        # El descuento se reajusta para reflejar el cambio.
        descuento_total = precio_base - precio_minimo
        precio_final = precio_minimo
        reglas_aplicadas.append("Ajustado a precio mínimo de venta.")
    else:
        precio_final = precio_calculado

    # 6. Determinar si la venta es bajo costo
    vendido_bajo_costo = precio_final < articulo.costo_actual

    # 7. Devolver el resultado
    return {
        "precio_base": precio_base,
        "precio_final": precio_final.quantize(Decimal('0.01')),
        "descuento_total": descuento_total.quantize(Decimal('0.01')),
        "reglas_aplicadas": reglas_aplicadas,
        "vendido_bajo_costo": vendido_bajo_costo
    }
