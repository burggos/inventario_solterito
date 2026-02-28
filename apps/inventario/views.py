# apps/inventario/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from django.core.paginator import Paginator

from .models import Movimiento, Producto, Categoria
from .forms import MovimientoForm, ProductoForm
from django.db.models import Sum, F, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models.functions import TruncMonth

@login_required
def lista_productos(request):
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    
    # Búsqueda por nombre
    query = request.GET.get('q', '')
    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
    
    # Filtro por categoría
    categoria_id = request.GET.get('categoria', '')
    if categoria_id and categoria_id.isdigit():
        productos = productos.filter(categoria_id=int(categoria_id))
    
    # Filtro por stock bajo
    stock_bajo = request.GET.get('stock_bajo', '')
    if stock_bajo == 'on' or stock_bajo == 'true':
        productos = productos.filter(stock__lte=F('stock_minimo'))
    
    # Paginación
    paginator = Paginator(productos, 12)  # 12 productos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.all().order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'query': query,
        'categoria_seleccionada': categoria_id,
        'stock_bajo': stock_bajo,
    }
    return render(request, 'inventario/lista_productos.html', context)


@login_required
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    movimientos = producto.movimientos.all().order_by('-fecha')[:10]  # últimos 10 movimientos
    context = {
        'producto': producto,
        'movimientos': movimientos
    }
    return render(request, 'inventario/detalle_producto.html', context)


@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            return redirect('inventario:detalle_producto', pk=producto.pk)
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/crear_producto.html', {'form': form})

@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('inventario:detalle_producto', pk=producto.pk)
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'inventario/editar_producto.html', {'form': form, 'producto': producto})


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        # Antes de eliminar, verificar si tiene movimientos asociados
        if producto.movimientos.exists():
            messages.error(request, 'No se puede eliminar un producto con movimientos asociados. Desactívelo en su lugar.')
            return redirect('inventario:detalle_producto', pk=producto.pk)
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('inventario:lista_productos')
    
    return render(request, 'inventario/eliminar_producto.html', {'producto': producto})

@login_required
def lista_movimientos(request):
    movimientos = Movimiento.objects.all().select_related('producto').order_by('-fecha')
    
    # Filtros
    producto_id = request.GET.get('producto', '')
    if producto_id and producto_id.isdigit():
        movimientos = movimientos.filter(producto_id=int(producto_id))
    
    tipo = request.GET.get('tipo', '')
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    
    fecha_desde = request.GET.get('desde', '')
    if fecha_desde:
        movimientos = movimientos.filter(fecha__date__gte=fecha_desde)
    
    fecha_hasta = request.GET.get('hasta', '')
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(movimientos, 20)  # 20 movimientos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Para los selects
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'productos': productos,
        'producto_seleccionado': producto_id,
        'tipo_seleccionado': tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    return render(request, 'inventario/lista_movimientos.html', context)

@login_required
def crear_movimiento(request):
    # Si viene un producto por GET, preseleccionarlo
    producto_id = request.GET.get('producto')
    initial = {}
    if producto_id:
        try:
            producto = Producto.objects.get(pk=producto_id)
            initial['producto'] = producto
        except Producto.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = MovimientoForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.usuario = request.user.username  # si tienes campo usuario
            movimiento.save()
            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('inventario:detalle_producto', pk=movimiento.producto.pk)
    else:
        form = MovimientoForm(initial=initial)
    
    return render(request, 'inventario/crear_movimiento.html', {'form': form})


@login_required
@permission_required('inventario.view_producto', raise_exception=True)
def reportes(request):
    # --- KPIs ---
    # Total de productos activos
    total_productos = Producto.objects.filter(activo=True).count()
    
    # Valor total del inventario (suma de precio * stock)
    valor_inventario = Producto.objects.filter(activo=True).aggregate(
        total=Sum(F('precio') * F('stock'))
    )['total'] or 0
    
    # Productos con stock bajo (stock <= stock_minimo)
    productos_stock_bajo = Producto.objects.filter(
        activo=True, 
        stock__lte=F('stock_minimo')
    ).count()
    
    # Movimientos de hoy
    hoy = timezone.now().date()
    movimientos_hoy = Movimiento.objects.filter(fecha__date=hoy).count()
    
    # Productos críticos (detalle)
    productos_criticos = Producto.objects.filter(
        activo=True, 
        stock__lte=F('stock_minimo')
    ).order_by('stock')[:10]

    # --- Datos para gráficos ---
    # 1. Movimientos por mes (últimos 6 meses)
    desde = hoy - timedelta(days=180)  # 6 meses aproximados

    movimientos_por_mes = Movimiento.objects.filter(fecha__date__gte=desde) \
    .annotate(mes=TruncMonth('fecha')) \
    .values('mes') \
    .annotate(entradas=Count('id', filter=Q(tipo='entrada')), 
              salidas=Count('id', filter=Q(tipo='salida'))) \
    .order_by('mes')
    
    # 2. Productos más vendidos (por cantidad de salidas)
    productos_mas_vendidos = Producto.objects.filter(
        activo=True,
        movimientos__tipo='salida'
    ).annotate(
        total_vendido=Sum('movimientos__cantidad', filter=Q(movimientos__tipo='salida'))
    ).order_by('-total_vendido')[:5]

    # Convertir movimientos_por_mes a lista y formatear fechas
    movimientos_por_mes = list(movimientos_por_mes)
    for item in movimientos_por_mes:
        item['mes'] = item['mes'].strftime('%Y-%m')  # Convierte date a string

    context = {
        'total_productos': total_productos,
        'valor_inventario': valor_inventario,
        'productos_stock_bajo': productos_stock_bajo,
        'movimientos_hoy': movimientos_hoy,
        'productos_criticos': productos_criticos,
        'movimientos_por_mes': movimientos_por_mes,  # Ya convertidas las fechas
        'productos_mas_vendidos': productos_mas_vendidos,
    }
    
    return render(request, 'inventario/reportes.html', context)

