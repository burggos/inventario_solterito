from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

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

        # stock_minimo mayor que stock
        p = Producto(
            nombre="Err2",
            categoria=self.cat,
            precio=1,
            stock=1,
            stock_minimo=5,
        )
        with self.assertRaises(Exception):
            p.full_clean()

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
        # el signal debe haber incrementado el stock
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 15)

    def test_crear_movimiento_salida_insuficiente(self):
        # cuando el stock no alcanza, la señal no debe restar
        m = Movimiento.objects.create(
            producto=self.prod,
            tipo="salida",
            cantidad=20,
        )
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 10)

    def test_crear_movimiento_salida_valido(self):
        m = Movimiento.objects.create(
            producto=self.prod,
            tipo="salida",
            cantidad=5,
        )
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 5)


class ProductoViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.login(username="tester", password="pass")
        self.cat = Categoria.objects.create(nombre="Prueba")

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
