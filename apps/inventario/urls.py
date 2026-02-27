# apps/inventario/urls.py
from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
]