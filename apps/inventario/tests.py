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
from inventario.models import Producto, Categoria, Movimiento


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
