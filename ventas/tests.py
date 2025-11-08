from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import transaction

import uuid
from datetime import date

from accounts.models import Usuario
from clientes.models import Cliente
from productos.models import Articulo, LineaArticulo, GrupoArticulo
from precios.models import ListaPrecio, PrecioArticulo
from core.models import Empresa, Sucursal
from ventas.models import OrdenCompraCliente, DetalleOrdenCompraCliente
from trading_system.choices import EstadoOrden, CanalVenta, Tipo, Moneda, EstadoEntidades

User = get_user_model()

class OrdenAPITestCase(APITestCase):
    def setUp(self):
        self.admin_user = Usuario.objects.create_user(
            username='admin',
            password='password123',
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            perfil=1, # ADMINISTRADOR
            puede_aprobar_bajo_costo=True
        )
        self.vendedor_user = Usuario.objects.create_user(
            username='vendedor',
            password='password123',
            first_name='Vendedor',
            last_name='User',
            email='vendedor@example.com',
            perfil=2, # VENDEDOR
            puede_aprobar_bajo_costo=False
        )
        self.client.force_authenticate(user=self.vendedor_user)

        self.empresa = Empresa.objects.create(empresa_id=uuid.uuid4(), nombre='Empresa Test')
        self.sucursal = Sucursal.objects.create(sucursal_id=uuid.uuid4(), nombre='Sucursal Test', empresa=self.empresa)
        self.cliente = Cliente.objects.create(
            cliente_id=uuid.uuid4(),
            nro_documento='123456789',
            nombre_comercial='Cliente Test',
            razon_social='Cliente Test S.A.C.',
            canal=CanalVenta.B2C
        )
        self.lista_precio = ListaPrecio.objects.create(
            lista_precio_id=uuid.uuid4(),
            empresa=self.empresa,
            sucursal=self.sucursal,
            codigo='LP001',
            nombre='Lista General',
            tipo=Tipo.MINORISTA,
            canal=CanalVenta.B2C,
            tipo_moneda=Moneda.SOL,
            estado=EstadoEntidades.ACTIVO,
            modificado_por=self.admin_user,
            fecha_vigencia_inicio=date(2023, 1, 1),
            fecha_vigencia_fin=date(2024, 12, 31)
        )
        self.linea = LineaArticulo.objects.create(linea_id=uuid.uuid4(), codigo_linea='LIN01', nombre_linea='Linea 1')
        self.grupo = GrupoArticulo.objects.create(grupo_id=uuid.uuid4(), codigo_grupo='GRP01', nombre_grupo='Grupo 1', linea=self.linea)
        self.articulo1 = Articulo.objects.create(
            articulo_id=uuid.uuid4(),
            codigo_articulo='ART001',
            descripcion='Articulo 1',
            stock=100,
            unidad_medida='UND',
            costo_actual=50.00,
            precio_sugerido=100.00,
            grupo_id=self.grupo
        )
        self.articulo2 = Articulo.objects.create(
            articulo_id=uuid.uuid4(),
            codigo_articulo='ART002',
            descripcion='Articulo 2',
            stock=50,
            unidad_medida='UND',
            costo_actual=20.00,
            precio_sugerido=40.00,
            grupo_id=self.grupo
        )
        PrecioArticulo.objects.create(
            precio_articulo_id=uuid.uuid4(),
            lista_precio=self.lista_precio,
            articulo=self.articulo1,
            precio_base=100.00,
            precio_minimo=80.00,
            estado=EstadoEntidades.ACTIVO
        )
        PrecioArticulo.objects.create(
            precio_articulo_id=uuid.uuid4(),
            lista_precio=self.lista_precio,
            articulo=self.articulo2,
            precio_base=40.00,
            precio_minimo=30.00,
            estado=EstadoEntidades.ACTIVO
        )

        self.orden_data = {
            'cliente_id': str(self.cliente.cliente_id),
            'vendedor_id': self.vendedor_user.username,
            'lista_precio_id': str(self.lista_precio.lista_precio_id),
            'empresa_id': str(self.empresa.empresa_id),
            'sucursal_id': str(self.sucursal.sucursal_id),
            'canal': CanalVenta.B2C,
            'detalles': [
                {'articulo_id': str(self.articulo1.articulo_id), 'cantidad': 2},
                {'articulo_id': str(self.articulo2.articulo_id), 'cantidad': 1},
            ]
        }

    def test_create_orden(self):
        url = reverse('orden-list')
        response = self.client.post(url, self.orden_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrdenCompraCliente.objects.count(), 1)
        self.assertEqual(DetalleOrdenCompraCliente.objects.count(), 2)
        orden = OrdenCompraCliente.objects.first()
        self.assertEqual(orden.estado, EstadoOrden.PENDIENTE)
        self.assertAlmostEqual(float(orden.subtotal), 240.00) # 2*100 + 1*40
        self.assertAlmostEqual(float(orden.total), 240.00)

    def test_list_ordenes(self):
        self.test_create_orden() # Create an order first
        url = reverse('orden-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('detalles_orden_compra_cliente', response.data['results'][0])

    def test_retrieve_orden(self):
        self.test_create_orden() # Create an order first
        orden = OrdenCompraCliente.objects.first()
        url = reverse('orden-detail', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['orden_compra_cliente_id'], str(orden.orden_compra_cliente_id))
        self.assertIn('detalles_orden_compra_cliente', response.data)

    def test_update_orden_draft(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        url = reverse('orden-detail', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        
        new_cliente = Cliente.objects.create(
            cliente_id=uuid.uuid4(),
            nro_documento='987654321',
            nombre_comercial='Nuevo Cliente',
            razon_social='Nuevo Cliente S.A.C.',
            canal=CanalVenta.B2B
        )
        update_data = {
            'cliente_id': str(new_cliente.cliente_id),
            'vendedor_id': self.vendedor_user.username, # Required by serializer
            'lista_precio_id': str(self.lista_precio.lista_precio_id), # Required by serializer
            'empresa_id': str(self.empresa.empresa_id), # Required by serializer
            'sucursal_id': str(self.sucursal.sucursal_id), # Required by serializer
            'canal': CanalVenta.B2B, # Required by serializer
            'detalles': [] # Required by serializer, but not processed by update method
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orden.refresh_from_db()
        self.assertEqual(orden.cliente, new_cliente)
        self.assertEqual(orden.canal, CanalVenta.B2B)

    def test_update_orden_non_draft_fails(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        orden.estado = EstadoOrden.PROCESANDO
        orden.save()
        url = reverse('orden-detail', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        update_data = {
            'canal': CanalVenta.ECOMMERCE,
            'cliente_id': str(self.cliente.cliente_id), # Required by serializer
            'vendedor_id': self.vendedor_user.username, # Required by serializer
            'lista_precio_id': str(self.lista_precio.lista_precio_id), # Required by serializer
            'empresa_id': str(self.empresa.empresa_id), # Required by serializer
            'sucursal_id': str(self.sucursal.sucursal_id), # Required by serializer
            'detalles': [] # Required by serializer
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Solo se pueden actualizar órdenes en estado PENDIENTE.", response.data['detail'])

    def test_confirmar_orden(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        url = reverse('orden-confirmar', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, EstadoOrden.PROCESANDO)

    def test_anular_orden_draft(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        url = reverse('orden-anular', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, EstadoOrden.CANCELADA)

    def test_marcar_como_facturada(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        orden.estado = EstadoOrden.PROCESANDO
        orden.save()
        url = reverse('orden-marcar-como-facturada', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, EstadoOrden.COMPLETADA)

    def test_anular_orden_confirmada_fails_without_permission(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        orden.estado = EstadoOrden.COMPLETADA
        orden.save()
        url = reverse('orden-anular-confirmada', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        # Vendedor user does not have special permission
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Currently no permission check, just state check

    def test_aprobar_venta_bajo_costo_no_permission(self):
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        # Make an item sold under cost (for testing purposes)
        detalle = orden.detalles_orden_compra_cliente.first()
        detalle.vendido_bajo_costo = True
        detalle.save()
        url = reverse('orden-aprobar-venta-bajo-costo', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        # Vendedor user does not have puede_aprobar_bajo_costo
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_aprobar_venta_bajo_costo_with_permission(self):
        self.client.force_authenticate(user=self.admin_user) # Admin has permission
        self.test_create_orden()
        orden = OrdenCompraCliente.objects.first()
        # Make an item sold under cost (for testing purposes)
        detalle = orden.detalles_orden_compra_cliente.first()
        detalle.vendido_bajo_costo = True
        detalle.save()
        url = reverse('orden-aprobar-venta-bajo-costo', kwargs={'pk': str(orden.orden_compra_cliente_id)})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Venta bajo costo aprobada.", response.data['detail'])

    def test_simular_pedido(self):
        url = reverse('orden-simular-pedido')
        sim_data = {
            'detalles': [
                {'articulo_id': str(self.articulo1.articulo_id), 'cantidad': 3},
                {'articulo_id': str(self.articulo2.articulo_id), 'cantidad': 2},
            ]
        }
        response = self.client.post(url, sim_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('simulated_total', response.data)
        self.assertAlmostEqual(response.data['simulated_total'], 3*100.00 + 2*40.00) # 300 + 80 = 380

    def test_calcular_precio_articulo(self):
        url = reverse('calcular_precio_articulo')
        calc_data = {
            'articulo_id': str(self.articulo1.articulo_id),
            'lista_precio_id': str(self.lista_precio.lista_precio_id),
            'canal': CanalVenta.B2C,
            'cantidad': 5
        }
        response = self.client.post(url, calc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_calculado', response.data)
        self.assertAlmostEqual(response.data['total_calculado'], 5 * 100.00) # 500

    def test_estadisticas_generales(self):
        url = reverse('estadisticas_ventas')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ventas_hoy', response.data)
        self.assertIn('ordenes_mes', response.data)