from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea grupos y asigna permisos base para Administrador, Vendedor y Bodeguero.'

    def handle(self, *args, **options):
        admin, _ = Group.objects.get_or_create(name='Administrador')
        vendedor, _ = Group.objects.get_or_create(name='Vendedor')
        bodeguero, _ = Group.objects.get_or_create(name='Bodeguero')

        # Admin: acceso total dentro de la app
        admin_perms = Permission.objects.filter(content_type__app_label='inventario')
        admin.permissions.set(admin_perms)

        # Vendedor: ventas + consulta de catálogo/stock + PDF factura
        vendedor_codes = [
            'view_producto', 'view_categoria', 'view_movimiento',
            'view_venta', 'add_venta', 'change_venta',
            'view_detalleventa', 'add_detalleventa',
            'register_sales', 'generate_invoice_pdf',
            'view_cliente',
            # módulos visibles en sidebar
            'ver_productos', 'ver_clientes', 'ver_ventas',
        ]
        vendedor.permissions.set(Permission.objects.filter(codename__in=vendedor_codes))

        # Bodeguero: compras + inventario operativo, sin ventas ni ajustes de inventario
        bodeguero_codes = [
            'view_producto', 'add_producto', 'change_producto',
            'view_categoria',
            'view_movimiento', 'add_movimiento', 'change_movimiento',
            'view_ordencompra', 'add_ordencompra', 'change_ordencompra',
            'view_detallecompra', 'add_detallecompra', 'change_detallecompra',
            'view_proveedor', 'add_proveedor', 'change_proveedor',
            'view_cliente',
            # módulos visibles en sidebar
            'ver_productos', 'ver_proveedores', 'ver_compras', 'ver_movimientos',
        ]
        bodeguero.permissions.set(Permission.objects.filter(codename__in=bodeguero_codes))

        self.stdout.write(self.style.SUCCESS('Roles y permisos configurados correctamente.'))
