# apps/inventario/views.py
from django.shortcuts import render
from .models import Producto

def lista_productos(request):
    productos = Producto.objects.filter(activo=True)  # Solo productos activos
    context = {
        'productos': productos
    }
    return render(request, 'inventario/lista_productos.html', context)