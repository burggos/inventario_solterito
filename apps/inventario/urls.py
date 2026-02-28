# apps/inventario/urls.py
from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('producto/nuevo/', views.crear_producto, name='crear_producto'),
    path('producto/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimiento/nuevo/', views.crear_movimiento, name='crear_movimiento'),
    path('reportes/', views.reportes, name='reportes'),
]