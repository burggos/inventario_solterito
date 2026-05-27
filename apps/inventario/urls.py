# apps/inventario/urls.py
from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('producto/nuevo/', views.crear_producto, name='crear_producto'),
    path('categoria/nueva/', views.crear_categoria, name='crear_categoria'),
    path('producto/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:pk>/desactivar/', views.desactivar_producto, name='desactivar_producto'),
    path('producto/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimiento/nuevo/', views.crear_movimiento, name='crear_movimiento'),
    path('reportes/', views.reportes, name='reportes'),

    # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='lista_clientes'),
    path('clientes/nuevo/', views.ClienteCreateView.as_view(), name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='editar_cliente'),

    # Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/<int:pk>/', views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/<int:pk>/editar/', views.editar_proveedor, name='editar_proveedor'),

    # Compras
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/pdf-registro/', views.compras_pdf_lista, name='compras_pdf_lista'),
    path('compras/nueva/', views.crear_compra, name='crear_compra'),
    path('compras/<int:pk>/', views.detalle_compra, name='detalle_compra'),
    path('compras/<int:pk>/recibir/', views.recibir_compra, name='recibir_compra'),
    path('compras/<int:pk>/pdf/', views.compra_pdf, name='compra_pdf'),

    # Ventas
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/pdf-registro/', views.ventas_pdf_lista, name='ventas_pdf_lista'),
    path('ventas/nueva/', views.crear_venta, name='crear_venta'),
    path('ventas/<int:pk>/', views.detalle_venta, name='detalle_venta'),
    path('ventas/<int:pk>/cancelar/', views.cancelar_venta, name='cancelar_venta'),
    path('ventas/<int:pk>/pdf/', views.venta_pdf, name='venta_pdf'),

    # POS / Operaciones rápidas
    path('pos/venta/', views.venta_rapida, name='venta_rapida'),
    path('pos/compra/', views.compra_rapida, name='compra_rapida'),

    # API (AJAX)
    path('api/productos/buscar/', views.api_buscar_productos, name='api_buscar_productos'),
    path('api/productos/similares/', views.api_productos_similares, name='api_productos_similares'),
    path('api/productos/<int:pk>/', views.api_producto_detalle, name='api_producto_detalle'),
    path('api/productos/<int:pk>/precio-referencia/', views.api_producto_precio_referencia, name='api_producto_precio_referencia'),
    path('api/clientes/<int:pk>/descuento/', views.api_cliente_descuento, name='api_cliente_descuento'),
    path('api/pos/venta/', views.api_pos_venta, name='api_pos_venta'),
    path('api/pos/compra/', views.api_pos_compra, name='api_pos_compra'),
    path('api/ajuste-inventario/', views.api_ajuste_inventario, name='api_ajuste_inventario'),

    # Usuarios (solo Administrador)
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),

    # Roles (solo Administrador)
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/nuevo/', views.crear_rol, name='crear_rol'),
    path('roles/<int:pk>/editar/', views.editar_rol, name='editar_rol'),
    path('roles/<int:pk>/eliminar/', views.eliminar_rol, name='eliminar_rol'),
]