from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

# Import using the app name rather than the package path to avoid
# "model not in INSTALLED_APPS" errors when the package sits under
# an extra "apps" directory.
from inventario.models import Producto, Categoria, Movimiento, Venta, DetalleVenta, Proveedor, OrdenCompra, DetalleCompra


class ProductoModelTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Prueba")

    def test_crear_producto_basico(self):
        p = Producto.objects.create(
            nombre="Queso",
            categoria=self.cat,
            precio=10.50,
            stock=5,
            stock_minimo=2,
        )
        self.assertEqual(str(p), "Queso (Stock: 5)")
        self.assertFalse(p.necesita_reposicion)
        p.stock = 1
        self.assertTrue(p.necesita_reposicion)

    def test_validaciones_modelo(self):
        # precio negativo
        p = Producto(
            nombre="Error",
            categoria=self.cat,
            precio=-1,
            stock=1,
            stock_minimo=0,
        )
        with self.assertRaises(Exception):
            p.full_clean()

        # stock_minimo mayor que stock ya no es un error de validación
        # (el stock se gestiona a través de Movimientos, no directamente)

        # código de barras duplicado
        Producto.objects.create(
            nombre="Primero",
            categoria=self.cat,
            precio=2,
            stock=1,
            stock_minimo=0,
            codigo_barras="123",
        )
        p2 = Producto(
            nombre="Segundo",
            categoria=self.cat,
            precio=2,
            stock=1,
            stock_minimo=0,
            codigo_barras="123",
        )
        with self.assertRaises(Exception):
            p2.full_clean()


class MovimientoModelTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Prueba")
        self.prod = Producto.objects.create(
            nombre="Leche",
            categoria=self.cat,
            precio=3.20,
            stock=10,
            stock_minimo=2,
        )

    def test_crear_movimiento_entrada(self):
        m = Movimiento.objects.create(
            producto=self.prod,
            tipo="entrada",
            cantidad=5,
        )
        self.assertEqual(str(m), "entrada - Leche (5)")
        # el movimiento debe haber incrementado el stock
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 15)

    def test_crear_movimiento_salida_insuficiente(self):
        # cuando el stock no alcanza, la salida debe fallar y no registrarse
        with self.assertRaises(ValidationError):
            Movimiento.objects.create(
                producto=self.prod,
                tipo="salida",
                cantidad=20,
            )
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 10)
        self.assertEqual(Movimiento.objects.filter(producto=self.prod, tipo='salida', cantidad=20).count(), 0)

    def test_crear_movimiento_salida_valido(self):
        m = Movimiento.objects.create(
            producto=self.prod,
            tipo="salida",
            cantidad=5,
        )
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 5)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ProductoViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.login(username="tester", password="pass")
        self.cat = Categoria.objects.create(nombre="Prueba")
        self.producto_activo = Producto.objects.create(
            nombre='Activo',
            categoria=self.cat,
            precio=10,
            stock=5,
            stock_minimo=1,
            activo=True,
        )
        self.producto_inactivo = Producto.objects.create(
            nombre='Inactivo',
            categoria=self.cat,
            precio=15,
            stock=0,
            stock_minimo=1,
            activo=False,
        )

    def test_lista_productos_vista_requiere_login(self):
        self.client.logout()
        response = self.client.get(reverse('inventario:lista_productos'))
        self.assertEqual(response.status_code, 302)  # redirige al login

    def test_crear_producto_post_valido(self):
        data = {
            'nombre': 'Pan',
            'categoria': self.cat.pk,
            'precio': '1.20',
            'stock': '10',
            'stock_minimo': '2',
        }
        resp = self.client.post(reverse('inventario:crear_producto'), data)
        # debería redirigir al detalle del producto
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Producto.objects.filter(nombre='Pan').exists())

    def test_lista_productos_muestra_desactivados_cuando_se_filtra(self):
        response = self.client.get(reverse('inventario:lista_productos'), {'estado': 'desactivados'})
        productos_renderizados = list(response.context['page_obj'].object_list)
        self.assertIn(self.producto_inactivo, productos_renderizados)
        self.assertNotIn(self.producto_activo, productos_renderizados)

    def test_detalle_producto_inactivo_sigue_disponible(self):
        response = self.client.get(reverse('inventario:detalle_producto', args=[self.producto_inactivo.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inactivo')

    def test_compra_rapida_admite_producto_inicial_por_querystring(self):
        response = self.client.get(reverse('inventario:compra_rapida'), {'producto': self.producto_activo.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['producto_inicial']['id'], self.producto_activo.pk)
        self.assertContains(response, 'compra-producto-inicial-data')

    def test_dashboard_linkea_stock_critico_a_compra_rapida(self):
        producto_critico = Producto.objects.create(
            nombre='Critico',
            categoria=self.cat,
            precio=9,
            stock=1,
            stock_minimo=3,
            activo=True,
        )

        response = self.client.get(reverse('inventario:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('inventario:compra_rapida') + f'?producto={producto_critico.pk}')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class NoError500ViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass')
        view_producto_perm = Permission.objects.get(codename='view_producto')
        self.user.user_permissions.add(view_producto_perm)
        self.client.login(username='tester', password='pass')

        self.cat = Categoria.objects.create(nombre='Prueba')
        self.producto = Producto.objects.create(
            nombre='Leche',
            categoria=self.cat,
            precio=3.20,
            stock=10,
            stock_minimo=2,
        )
        self.producto_sin_mov = Producto.objects.create(
            nombre='Pan',
            categoria=self.cat,
            precio=1.20,
            stock=5,
            stock_minimo=1,
        )
        self.movimiento = Movimiento.objects.create(
            producto=self.producto,
            tipo='entrada',
            cantidad=3,
        )

    def assertNot500(self, response, url):
        self.assertNotEqual(
            response.status_code,
            500,
            f'Error 500 en la vista {url}',
        )

    def test_get_views_do_not_return_500(self):
        urls = [
            reverse('inventario:lista_productos'),
            reverse('inventario:detalle_producto', args=[self.producto.pk]),
            reverse('inventario:crear_producto'),
            reverse('inventario:editar_producto', args=[self.producto.pk]),
            reverse('inventario:eliminar_producto', args=[self.producto_sin_mov.pk]),
            reverse('inventario:lista_movimientos'),
            reverse('inventario:crear_movimiento'),
            reverse('inventario:reportes'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNot500(response, url)

    def test_get_lista_productos_with_filters_does_not_return_500(self):
        url = reverse('inventario:lista_productos') + '?q=Leche&categoria={}&stock_bajo=on&page=1'.format(self.cat.pk)
        response = self.client.get(url)
        self.assertNot500(response, url)

    def test_get_crear_movimiento_with_initial_product_does_not_return_500(self):
        url = reverse('inventario:crear_movimiento') + '?producto={}'.format(self.producto.pk)
        response = self.client.get(url)
        self.assertNot500(response, url)

    def test_get_reportes_with_date_range_does_not_return_500(self):
        hoy = timezone.now().date()
        desde = hoy - timedelta(days=7)
        url = reverse('inventario:reportes') + f'?desde={desde}&hasta={hoy}'
        response = self.client.get(url)
        self.assertNot500(response, url)
        self.assertContains(response, 'Inteligencia de Negocio')

    def test_post_crear_producto_invalid_does_not_return_500(self):
        data = {
            'nombre': '',
            'categoria': '',
            'precio': '-1',
            'stock': '-5',
            'stock_minimo': '10',
        }
        response = self.client.post(reverse('inventario:crear_producto'), data)
        self.assertNot500(response, reverse('inventario:crear_producto'))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'nombre', ['Este campo es obligatorio.'])

    def test_post_crear_movimiento_invalid_stock_does_not_return_500(self):
        self.producto.refresh_from_db()
        data = {
            'producto': self.producto.pk,
            'tipo': 'salida',
            'cantidad': '999',
            'descripcion': 'Salida mayor al stock',
        }
        response = self.client.post(reverse('inventario:crear_movimiento'), data)
        self.assertNot500(response, reverse('inventario:crear_movimiento'))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'Stock insuficiente. Stock actual: {}'.format(self.producto.stock))

    def test_post_editar_producto_does_not_return_500(self):
        data = {
            'nombre': 'Leche Actualizada',
            'categoria': self.cat.pk,
            'precio': '4.00',
            'stock': '8',
            'stock_minimo': '2',
        }
        response = self.client.post(reverse('inventario:editar_producto', args=[self.producto.pk]), data)
        self.assertNot500(response, reverse('inventario:editar_producto', args=[self.producto.pk]))
        self.assertEqual(response.status_code, 302)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, 'Leche Actualizada')

    def test_post_editar_producto_invalid_does_not_return_500(self):
        data = {
            'nombre': '',
            'categoria': self.cat.pk,
            'precio': '-2.00',
            'stock': '2',
            'stock_minimo': '1',
        }
        response = self.client.post(reverse('inventario:editar_producto', args=[self.producto.pk]), data)
        self.assertNot500(response, reverse('inventario:editar_producto', args=[self.producto.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'nombre', ['Este campo es obligatorio.'])

    def test_post_eliminar_producto_with_movimientos_does_not_return_500(self):
        response = self.client.post(reverse('inventario:eliminar_producto', args=[self.producto.pk]))
        self.assertNot500(response, reverse('inventario:eliminar_producto', args=[self.producto.pk]))
        self.assertEqual(response.status_code, 302)

    def test_post_desactivar_producto_with_movimientos_marks_inactive(self):
        response = self.client.post(reverse('inventario:desactivar_producto', args=[self.producto.pk]))
        self.assertNot500(response, reverse('inventario:desactivar_producto', args=[self.producto.pk]))
        self.assertEqual(response.status_code, 302)
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)

    def test_post_crear_movimiento_does_not_return_500(self):
        data = {
            'producto': self.producto.pk,
            'tipo': 'entrada',
            'cantidad': '2',
            'descripcion': 'Ingreso de prueba',
        }
        response = self.client.post(reverse('inventario:crear_movimiento'), data)
        self.assertNot500(response, reverse('inventario:crear_movimiento'))

    def test_post_eliminar_producto_does_not_return_500(self):
        response = self.client.post(reverse('inventario:eliminar_producto', args=[self.producto_sin_mov.pk]))
        self.assertNot500(response, reverse('inventario:eliminar_producto', args=[self.producto_sin_mov.pk]))


class PosVentaPendienteTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='vendedor', password='pass')
        self.client.login(username='vendedor', password='pass')
        self.cat = Categoria.objects.create(nombre='Abarrotes')
        self.producto = Producto.objects.create(
            nombre='Arroz',
            categoria=self.cat,
            precio=5000,
            stock=1,
            stock_minimo=2,
            activo=True,
        )

    def test_api_pos_venta_crea_pedido_pendiente_sin_descontar_stock(self):
        response = self.client.post(
            reverse('inventario:api_pos_venta'),
            data={
                'items': [
                    {
                        'producto_id': self.producto.pk,
                        'cantidad': 3,
                        'precio': '5000',
                    }
                ],
                'cliente': 'Cliente Encargo',
                'forma_pago': 'efectivo',
                'registrar_como_pendiente': True,
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['estado'], 'pendiente')

        venta = Venta.objects.get(pk=payload['venta_id'])
        self.assertEqual(venta.estado, 'pendiente')
        self.assertEqual(venta.detalles.count(), 1)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 1)
        self.assertFalse(Movimiento.objects.filter(descripcion__icontains=venta.numero, tipo='salida').exists())

    def test_cancelar_venta_pendiente_no_incrementa_stock(self):
        venta = Venta.objects.create(
            cliente_nombre='Cliente Encargo',
            forma_pago='efectivo',
            estado='pendiente',
            subtotal=5000,
            total=5000,
            usuario_vendedor=self.user.username,
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=self.producto,
            cantidad=2,
            precio_unitario=5000,
        )

        stock_antes = self.producto.stock
        response = self.client.post(reverse('inventario:cancelar_venta', args=[venta.pk]))

        self.assertEqual(response.status_code, 302)
        venta.refresh_from_db()
        self.assertEqual(venta.estado, 'cancelada')
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, stock_antes)


class PosCompraTipoTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='bodega', password='pass')
        self.client.login(username='bodega', password='pass')
        self.cat = Categoria.objects.create(nombre='Lacteos')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Prueba', activo=True)
        self.producto = Producto.objects.create(
            nombre='Leche',
            categoria=self.cat,
            proveedor=self.proveedor,
            precio=4200,
            stock=3,
            stock_minimo=1,
            activo=True,
        )

    def test_api_pos_compra_directa_actualiza_stock_y_completa_orden(self):
        response = self.client.post(
            reverse('inventario:api_pos_compra'),
            data={
                'items': [
                    {
                        'producto_id': self.producto.pk,
                        'cantidad': 2,
                        'precio': '4000',
                    }
                ],
                'proveedor_id': self.proveedor.pk,
                'notas': 'Compra directa',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['estado'], 'completada')

        orden = OrdenCompra.objects.get(pk=payload['orden_id'])
        self.assertEqual(orden.estado, 'completada')
        self.assertIsNotNone(orden.fecha_entrega_real)
        detalle = orden.detalles.get(producto=self.producto)
        self.assertEqual(detalle.cantidad_recibida, 2)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_api_pos_compra_por_encargo_crea_orden_pendiente_sin_stock(self):
        stock_antes = self.producto.stock
        response = self.client.post(
            reverse('inventario:api_pos_compra'),
            data={
                'items': [
                    {
                        'producto_id': self.producto.pk,
                        'cantidad': 4,
                        'precio': '4100',
                    }
                ],
                'proveedor_id': self.proveedor.pk,
                'registrar_como_pendiente': True,
                'notas': 'Encargo al proveedor',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['estado'], 'pendiente')

        orden = OrdenCompra.objects.get(pk=payload['orden_id'])
        self.assertEqual(orden.estado, 'pendiente')
        self.assertIsNone(orden.fecha_entrega_real)
        detalle = orden.detalles.get(producto=self.producto)
        self.assertEqual(detalle.cantidad_solicitada, 4)
        self.assertEqual(detalle.cantidad_recibida, 0)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, stock_antes)
        self.assertFalse(Movimiento.objects.filter(descripcion__icontains=orden.numero, tipo='entrada').exists())


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class RecepcionCompraParcialTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='bodega2', password='pass')
        self.client.login(username='bodega2', password='pass')

        self.cat = Categoria.objects.create(nombre='Enlatados')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Recepcion', activo=True)
        self.producto = Producto.objects.create(
            nombre='Atun',
            categoria=self.cat,
            proveedor=self.proveedor,
            precio=7000,
            stock=5,
            stock_minimo=1,
            activo=True,
        )
        self.orden = OrdenCompra.objects.create(
            proveedor=self.proveedor,
            estado='pendiente',
            usuario_creador=self.user.username,
        )
        self.detalle = DetalleCompra.objects.create(
            orden_compra=self.orden,
            producto=self.producto,
            cantidad_solicitada=10,
            cantidad_recibida=0,
            precio_unitario=6500,
        )

    def test_recibir_compra_permite_recepcion_parcial_por_cantidad_real(self):
        response = self.client.post(
            reverse('inventario:recibir_compra', args=[self.orden.pk]),
            data={f'recibido_{self.detalle.pk}': '4'},
        )

        self.assertEqual(response.status_code, 302)
        self.orden.refresh_from_db()
        self.detalle.refresh_from_db()
        self.producto.refresh_from_db()

        self.assertEqual(self.orden.estado, 'recibida_parcial')
        self.assertEqual(self.detalle.cantidad_recibida, 4)
        self.assertEqual(self.producto.stock, 9)

    def test_recibir_compra_completa_despues_de_parcial_solo_suma_delta(self):
        self.client.post(
            reverse('inventario:recibir_compra', args=[self.orden.pk]),
            data={f'recibido_{self.detalle.pk}': '4'},
        )

        response = self.client.post(
            reverse('inventario:recibir_compra', args=[self.orden.pk]),
            data={f'recibido_{self.detalle.pk}': '10'},
        )

        self.assertEqual(response.status_code, 302)
        self.orden.refresh_from_db()
        self.detalle.refresh_from_db()
        self.producto.refresh_from_db()

        self.assertEqual(self.orden.estado, 'completada')
        self.assertEqual(self.detalle.cantidad_recibida, 10)
        self.assertEqual(self.producto.stock, 15)

    def test_no_permite_editar_item_ya_completo_en_orden_parcial(self):
        producto_extra = Producto.objects.create(
            nombre='Sardinas',
            categoria=self.cat,
            proveedor=self.proveedor,
            precio=5500,
            stock=2,
            stock_minimo=1,
            activo=True,
        )
        detalle_extra = DetalleCompra.objects.create(
            orden_compra=self.orden,
            producto=producto_extra,
            cantidad_solicitada=6,
            cantidad_recibida=0,
            precio_unitario=5000,
        )

        self.client.post(
            reverse('inventario:recibir_compra', args=[self.orden.pk]),
            data={
                f'recibido_{self.detalle.pk}': '10',
                f'recibido_{detalle_extra.pk}': '2',
            },
        )

        self.orden.refresh_from_db()
        self.detalle.refresh_from_db()
        detalle_extra.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(self.orden.estado, 'recibida_parcial')
        self.assertEqual(self.detalle.cantidad_recibida, 10)

        stock_antes = self.producto.stock
        response = self.client.post(
            reverse('inventario:recibir_compra', args=[self.orden.pk]),
            data={
                f'recibido_{self.detalle.pk}': '9',
                f'recibido_{detalle_extra.pk}': '4',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no puede editarse de nuevo')
        self.detalle.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(self.detalle.cantidad_recibida, 10)
        self.assertEqual(self.producto.stock, stock_antes)
