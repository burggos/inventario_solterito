# apps/inventario/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from django.core.paginator import Paginator
from .models import Movimiento, Producto, Categoria, Proveedor, OrdenCompra, DetalleCompra, Venta, DetalleVenta
from .forms import MovimientoForm, ProductoForm, ProductoEditForm, ProveedorForm, OrdenCompraForm, DetalleCompraForm, VentaForm, DetalleVentaForm
from django.db.models import Sum, F, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models.functions import TruncMonth, TruncDate, TruncWeek, TruncYear
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

@login_required
def dashboard(request):
    """Main dashboard with KPIs and quick overview."""
    hoy = timezone.now().date()
    
    total_productos = Producto.objects.filter(activo=True).count()
    valor_inventario = Producto.objects.filter(activo=True).aggregate(
        total=Sum(F('precio') * F('stock'))
    )['total'] or 0
    productos_stock_bajo = Producto.objects.filter(
        activo=True, stock__lte=F('stock_minimo')
    ).count()
    productos_sin_stock = Producto.objects.filter(activo=True, stock=0).count()
    movimientos_hoy = Movimiento.objects.filter(fecha__date=hoy).count()
    
    # Recent activity
    ultimos_movimientos = Movimiento.objects.select_related('producto').order_by('-fecha')[:8]
    productos_criticos = Producto.objects.filter(
        activo=True, stock__lte=F('stock_minimo')
    ).order_by('stock')[:5]
    
    # Category distribution for chart
    categorias_dist = Categoria.objects.filter(
        productos__activo=True
    ).annotate(
        total=Count('productos')
    ).order_by('-total')[:8]
    categorias_chart = json.dumps(
        [{'nombre': c.nombre, 'total': c.total} for c in categorias_dist],
        cls=DjangoJSONEncoder
    )
    
    # Sales last 7 days
    desde_7d = hoy - timedelta(days=7)
    ventas_semana = Venta.objects.filter(
        fecha_venta__date__gte=desde_7d, estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Compras pendientes
    compras_pendientes = OrdenCompra.objects.filter(estado='pendiente').count()
    
    context = {
        'total_productos': total_productos,
        'valor_inventario': valor_inventario,
        'productos_stock_bajo': productos_stock_bajo,
        'productos_sin_stock': productos_sin_stock,
        'movimientos_hoy': movimientos_hoy,
        'ultimos_movimientos': ultimos_movimientos,
        'productos_criticos': productos_criticos,
        'categorias_chart': categorias_chart,
        'ventas_semana': ventas_semana,
        'compras_pendientes': compras_pendientes,
    }
    return render(request, 'inventario/dashboard.html', context)


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
            stock_inicial = form.cleaned_data.get('stock_inicial') or 0
            producto = form.save(commit=False)
            producto.stock = 0  # Stock managed via Movimiento
            producto.save()
            if stock_inicial > 0:
                Movimiento.objects.create(
                    producto=producto,
                    tipo='entrada',
                    cantidad=stock_inicial,
                    descripcion='Stock inicial al crear producto',
                    usuario=request.user.username,
                )
            messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
            return redirect('inventario:detalle_producto', pk=producto.pk)
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/crear_producto.html', {'form': form})

@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoEditForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventario:detalle_producto', pk=producto.pk)
    else:
        form = ProductoEditForm(instance=producto)
    
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
    selected_product = None
    if producto_id:
        try:
            producto = Producto.objects.get(pk=producto_id)
            initial['producto'] = producto
            selected_product = {'id': producto.pk, 'nombre': producto.nombre, 'stock': producto.stock}
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
            # Preserve selected product on validation error
            prod_id = request.POST.get('producto')
            if prod_id:
                try:
                    producto = Producto.objects.get(pk=prod_id)
                    selected_product = {'id': producto.pk, 'nombre': producto.nombre, 'stock': producto.stock}
                except Producto.DoesNotExist:
                    pass
    else:
        form = MovimientoForm(initial=initial)
    
    return render(request, 'inventario/crear_movimiento.html', {
        'form': form,
        'selected_product': selected_product,
    })


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
    fecha_desde_raw = request.GET.get('desde', '')
    fecha_hasta_raw = request.GET.get('hasta', '')
    fecha_desde = None
    fecha_hasta = None
    rango_label = 'Últimos 6 meses'

    try:
        if fecha_desde_raw:
            fecha_desde = datetime.strptime(fecha_desde_raw, '%Y-%m-%d').date()
        if fecha_hasta_raw:
            fecha_hasta = datetime.strptime(fecha_hasta_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha_desde = None
        fecha_hasta = None

    if fecha_desde and fecha_hasta:
        rango_label = f'{fecha_desde.strftime("%d/%m/%Y")} al {fecha_hasta.strftime("%d/%m/%Y")} '
    elif fecha_desde:
        rango_label = f'Desde {fecha_desde.strftime("%d/%m/%Y")} '
    elif fecha_hasta:
        rango_label = f'Hasta {fecha_hasta.strftime("%d/%m/%Y")} '

    movimientos_q = Q()
    if fecha_desde:
        movimientos_q &= Q(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        movimientos_q &= Q(fecha__date__lte=fecha_hasta)

    # Determinar el rango de fechas para productos más vendidos
    if fecha_desde or fecha_hasta:
        movimientos_rango = Movimiento.objects.filter(movimientos_q)
        producto_fecha_q = Q()
        if fecha_desde:
            producto_fecha_q &= Q(movimientos__fecha__date__gte=fecha_desde)
        if fecha_hasta:
            producto_fecha_q &= Q(movimientos__fecha__date__lte=fecha_hasta)
    else:
        desde = hoy - timedelta(days=180)  # 6 meses aproximados
        movimientos_rango = Movimiento.objects.filter(fecha__date__gte=desde)
        producto_fecha_q = Q(movimientos__fecha__date__gte=desde)

    total_movimientos_rango = movimientos_rango.count()
    total_entradas_rango = movimientos_rango.filter(tipo='entrada').count()
    total_salidas_rango = movimientos_rango.filter(tipo='salida').count()

    # Obtener el tipo de agrupación del request
    grouping = request.GET.get('grouping', 'dia')
    
    # Definir el campo de agrupación según el parámetro
    if grouping == 'semana':
        trunc_func = TruncWeek('fecha')
        label_field = 'semana'
        date_format = 'Semana %V (%d/%m/%Y)'
    elif grouping == 'mes':
        trunc_func = TruncMonth('fecha')
        label_field = 'mes'
        date_format = '%B %Y'
    elif grouping == 'ano':
        trunc_func = TruncYear('fecha')
        label_field = 'ano'
        date_format = '%Y'
    else:  # dia (por defecto)
        trunc_func = TruncDate('fecha')
        label_field = 'dia'
        date_format = '%d/%m/%Y'

    movimientos_por_mes = movimientos_rango.annotate(periodo=trunc_func) \
        .values('periodo') \
        .annotate(entradas=Count('id', filter=Q(tipo='entrada')), 
                  salidas=Count('id', filter=Q(tipo='salida'))) \
        .order_by('periodo')

    movimientos_por_mes = list(movimientos_por_mes)
    movimientos_procesados = []
    for item in movimientos_por_mes:
        # Convertir el date object a string y crear diccionario JSON-serializable
        if item['periodo']:
            periodo_str = item['periodo'].strftime(date_format) if hasattr(item['periodo'], 'strftime') else str(item['periodo'])
        else:
            periodo_str = 'Sin fecha'
        
        movimientos_procesados.append({
            'mes': periodo_str,
            'entradas': item['entradas'],
            'salidas': item['salidas']
        })
    
    movimientos_por_mes = movimientos_procesados

    productos_mas_vendidos_qs = Producto.objects.filter(
        activo=True,
        movimientos__tipo='salida'
    ).annotate(
        total_vendido=Sum(
            'movimientos__cantidad',
            filter=Q(movimientos__tipo='salida') & producto_fecha_q
        )
    ).filter(total_vendido__gt=0).order_by('-total_vendido')[:5]
    productos_mas_vendidos = list(productos_mas_vendidos_qs)
    max_vendido = max((p.total_vendido or 0 for p in productos_mas_vendidos), default=1)
    for producto in productos_mas_vendidos:
        producto.porcentaje_vendido = int((producto.total_vendido or 0) / max_vendido * 100) if max_vendido else 0

    context = {
        'total_productos': total_productos,
        'valor_inventario': valor_inventario,
        'productos_stock_bajo': productos_stock_bajo,
        'movimientos_hoy': movimientos_hoy,
        'total_movimientos_rango': total_movimientos_rango,
        'total_entradas_rango': total_entradas_rango,
        'total_salidas_rango': total_salidas_rango,
        'rango_label': rango_label,
        'productos_criticos': productos_criticos,
        'movimientos_por_mes': json.dumps(movimientos_por_mes, cls=DjangoJSONEncoder),
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_donut_json': json.dumps(
            [{'nombre': p.nombre, 'total_vendido': p.total_vendido} for p in productos_mas_vendidos],
            cls=DjangoJSONEncoder
        ),
        'fecha_desde': fecha_desde_raw,
        'fecha_hasta': fecha_hasta_raw,
        'grouping': grouping,
    }
    
    return render(request, 'inventario/reportes.html', context)


# ============================================================================
# PROVEEDORES
# ============================================================================

@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    query = request.GET.get('q', '')
    if query:
        proveedores = proveedores.filter(
            Q(nombre__icontains=query) | Q(email__icontains=query) | Q(ruc__icontains=query)
        )
    activo = request.GET.get('activo', '')
    if activo == '1':
        proveedores = proveedores.filter(activo=True)
    elif activo == '0':
        proveedores = proveedores.filter(activo=False)

    paginator = Paginator(proveedores, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'inventario/lista_proveedores.html', {
        'page_obj': page_obj, 'query': query, 'activo': activo,
    })


@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, 'Proveedor creado correctamente.')
            return redirect('inventario:detalle_proveedor', pk=proveedor.pk)
    else:
        form = ProveedorForm()
    return render(request, 'inventario/crear_proveedor.html', {'form': form})


@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('inventario:detalle_proveedor', pk=proveedor.pk)
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'inventario/editar_proveedor.html', {'form': form, 'proveedor': proveedor})


@login_required
def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    ordenes = proveedor.ordenes_compra.all().order_by('-fecha_creacion')[:10]
    return render(request, 'inventario/detalle_proveedor.html', {
        'proveedor': proveedor, 'ordenes': ordenes,
    })


# ============================================================================
# COMPRAS
# ============================================================================

@login_required
def lista_compras(request):
    compras = OrdenCompra.objects.all().select_related('proveedor')
    estado = request.GET.get('estado', '')
    if estado:
        compras = compras.filter(estado=estado)
    proveedor_id = request.GET.get('proveedor', '')
    if proveedor_id and proveedor_id.isdigit():
        compras = compras.filter(proveedor_id=int(proveedor_id))
    fecha_desde = request.GET.get('desde', '')
    if fecha_desde:
        compras = compras.filter(fecha_creacion__date__gte=fecha_desde)
    fecha_hasta = request.GET.get('hasta', '')
    if fecha_hasta:
        compras = compras.filter(fecha_creacion__date__lte=fecha_hasta)

    paginator = Paginator(compras, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/lista_compras.html', {
        'page_obj': page_obj, 'proveedores': proveedores,
        'estado': estado, 'proveedor_seleccionado': proveedor_id,
        'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta,
    })


@login_required
def crear_compra(request):
    """Redirects to the unified fast purchase interface."""
    return redirect('inventario:compra_rapida')


@login_required
def detalle_compra(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    detalles = orden.detalles.all().select_related('producto')
    return render(request, 'inventario/detalle_compra.html', {
        'orden': orden, 'detalles': detalles,
    })


@login_required
@require_http_methods(["POST"])
def recibir_compra(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if orden.estado in ('completada', 'cancelada'):
        messages.error(request, 'Esta orden ya fue completada o cancelada.')
        return redirect('inventario:detalle_compra', pk=orden.pk)

    for detalle in orden.detalles.all():
        detalle.cantidad_recibida = detalle.cantidad_solicitada
        detalle.save()
        # Crear movimiento de entrada (signal actualiza stock)
        Movimiento.objects.create(
            producto=detalle.producto,
            tipo='entrada',
            cantidad=detalle.cantidad_recibida,
            descripcion=f'Recepción de compra {orden.numero}',
            usuario=request.user.username,
        )

    orden.estado = 'completada'
    orden.fecha_entrega_real = timezone.now().date()
    orden.save()
    messages.success(request, f'Compra {orden.numero} recibida. Stock actualizado.')
    return redirect('inventario:detalle_compra', pk=orden.pk)


# ============================================================================
# VENTAS
# ============================================================================

@login_required
def lista_ventas(request):
    ventas = Venta.objects.all()
    estado = request.GET.get('estado', '')
    if estado:
        ventas = ventas.filter(estado=estado)
    forma_pago = request.GET.get('forma_pago', '')
    if forma_pago:
        ventas = ventas.filter(forma_pago=forma_pago)
    fecha_desde = request.GET.get('desde', '')
    if fecha_desde:
        ventas = ventas.filter(fecha_venta__date__gte=fecha_desde)
    fecha_hasta = request.GET.get('hasta', '')
    if fecha_hasta:
        ventas = ventas.filter(fecha_venta__date__lte=fecha_hasta)
    query = request.GET.get('q', '')
    if query:
        ventas = ventas.filter(
            Q(numero__icontains=query) | Q(cliente_nombre__icontains=query)
        )

    paginator = Paginator(ventas, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'inventario/lista_ventas.html', {
        'page_obj': page_obj, 'estado': estado, 'forma_pago': forma_pago,
        'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta, 'query': query,
    })


@login_required
def crear_venta(request):
    """Redirects to the unified POS sale interface."""
    return redirect('inventario:venta_rapida')


@login_required
def detalle_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.all().select_related('producto')
    return render(request, 'inventario/detalle_venta.html', {
        'venta': venta, 'detalles': detalles,
    })


@login_required
@require_http_methods(["POST"])
def cancelar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if venta.estado == 'cancelada':
        messages.error(request, 'Esta venta ya está cancelada.')
        return redirect('inventario:detalle_venta', pk=venta.pk)

    # Revertir stock via movimiento (signal actualiza stock)
    for detalle in venta.detalles.all():
        Movimiento.objects.create(
            producto=detalle.producto,
            tipo='entrada',
            cantidad=detalle.cantidad,
            descripcion=f'Cancelación de venta {venta.numero}',
            usuario=request.user.username,
        )

    venta.estado = 'cancelada'
    venta.save()
    messages.success(request, f'Venta {venta.numero} cancelada. Stock revertido.')
    return redirect('inventario:detalle_venta', pk=venta.pk)


# ============================================================================
# API ENDPOINTS (AJAX)
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_buscar_productos(request):
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse([], safe=False)
    productos = Producto.objects.filter(
        activo=True
    ).filter(
        Q(nombre__icontains=q) | Q(codigo_barras__icontains=q)
    )[:10]
    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'precio': str(p.precio),
            'stock': p.stock,
            'codigo_barras': p.codigo_barras or '',
        }
        for p in productos
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def api_producto_detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    return JsonResponse({
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': str(producto.precio),
        'stock': producto.stock,
        'codigo_barras': producto.codigo_barras or '',
    })


# ============================================================================
# POS - VENTA RÁPIDA
# ============================================================================

@login_required
def venta_rapida(request):
    """Renders the POS-style fast sale interface."""
    return render(request, 'inventario/venta_rapida.html')


@login_required
def compra_rapida(request):
    """Renders the fast purchase interface."""
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/compra_rapida.html', {
        'proveedores': proveedores,
    })


@login_required
@require_http_methods(["POST"])
def api_pos_venta(request):
    """AJAX endpoint for POS sale submission. Expects JSON body."""
    import json as json_mod
    from decimal import Decimal, InvalidOperation
    from django.db import transaction

    try:
        data = json_mod.loads(request.body)
    except (json_mod.JSONDecodeError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    items = data.get('items', [])
    if not items:
        return JsonResponse({'ok': False, 'error': 'No hay productos en la venta'}, status=400)

    cliente = (data.get('cliente', '') or '').strip() or 'Cliente General'
    forma_pago = data.get('forma_pago', 'efectivo')
    notas = data.get('notas', '')

    # Validate forma_pago
    valid_pagos = [c[0] for c in Venta.PAGO_CHOICES]
    if forma_pago not in valid_pagos:
        forma_pago = 'efectivo'

    try:
        with transaction.atomic():
            # Validate all items first (with lock to prevent race conditions)
            validated = []
            for item in items:
                producto = Producto.objects.select_for_update().get(
                    pk=item['producto_id'], activo=True
                )
                cantidad = int(item['cantidad'])
                if cantidad <= 0:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Cantidad inválida para {producto.nombre}'
                    }, status=400)
                if producto.stock < cantidad:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Stock insuficiente para {producto.nombre} (disponible: {producto.stock})'
                    }, status=400)
                validated.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio': Decimal(str(item.get('precio', str(producto.precio)))),
                })

            # Create sale
            venta = Venta(
                cliente_nombre=cliente,
                forma_pago=forma_pago,
                notas=notas,
                estado='completada',
                usuario_vendedor=request.user.username,
            )
            venta.save()

            total = Decimal('0')
            for vi in validated:
                detalle = DetalleVenta(
                    venta=venta,
                    producto=vi['producto'],
                    cantidad=vi['cantidad'],
                    precio_unitario=vi['precio'],
                    descuento_porcentaje=Decimal('0'),
                )
                detalle.save()
                total += detalle.subtotal
                # Signal handles stock update
                Movimiento.objects.create(
                    producto=vi['producto'],
                    tipo='salida',
                    cantidad=vi['cantidad'],
                    descripcion=f'Venta POS {venta.numero}',
                    usuario=request.user.username,
                )

            venta.total = total
            venta.save(update_fields=['total'])

        return JsonResponse({
            'ok': True,
            'venta_id': venta.pk,
            'numero': venta.numero,
            'total': str(venta.total),
        })

    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=400)
    except (ValueError, InvalidOperation, KeyError) as e:
        return JsonResponse({'ok': False, 'error': f'Error en datos: {str(e)}'}, status=400)


@login_required
@require_http_methods(["POST"])
def api_pos_compra(request):
    """AJAX endpoint for fast purchase submission. Creates order and receives immediately."""
    import json as json_mod
    from decimal import Decimal, InvalidOperation
    from django.db import transaction

    try:
        data = json_mod.loads(request.body)
    except (json_mod.JSONDecodeError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    items = data.get('items', [])
    if not items:
        return JsonResponse({'ok': False, 'error': 'No hay productos en la compra'}, status=400)

    proveedor_id = data.get('proveedor_id')
    if not proveedor_id:
        return JsonResponse({'ok': False, 'error': 'Selecciona un proveedor'}, status=400)

    notas = data.get('notas', '')

    try:
        with transaction.atomic():
            proveedor = Proveedor.objects.get(pk=proveedor_id, activo=True)

            validated = []
            for item in items:
                producto = Producto.objects.get(pk=item['producto_id'], activo=True)
                cantidad = int(item['cantidad'])
                precio = Decimal(str(item.get('precio', str(producto.precio))))
                if cantidad <= 0:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Cantidad inválida para {producto.nombre}'
                    }, status=400)
                if precio < 0:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Precio inválido para {producto.nombre}'
                    }, status=400)
                validated.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio': precio,
                })

            # Create purchase order
            orden = OrdenCompra(
                proveedor=proveedor,
                estado='completada',
                notas=notas,
                usuario_creador=request.user.username,
                fecha_entrega_real=timezone.now().date(),
            )
            orden.save()

            total = Decimal('0')
            for vi in validated:
                detalle = DetalleCompra(
                    orden_compra=orden,
                    producto=vi['producto'],
                    cantidad_solicitada=vi['cantidad'],
                    cantidad_recibida=vi['cantidad'],
                    precio_unitario=vi['precio'],
                )
                detalle.save()
                total += detalle.subtotal
                # Signal handles stock update
                Movimiento.objects.create(
                    producto=vi['producto'],
                    tipo='entrada',
                    cantidad=vi['cantidad'],
                    descripcion=f'Compra rápida {orden.numero}',
                    usuario=request.user.username,
                )

            orden.total = total
            orden.save(update_fields=['total'])

        return JsonResponse({
            'ok': True,
            'orden_id': orden.pk,
            'numero': orden.numero,
            'total': str(orden.total),
        })

    except Proveedor.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Proveedor no encontrado'}, status=400)
    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=400)
    except (ValueError, InvalidOperation, KeyError) as e:
        return JsonResponse({'ok': False, 'error': f'Error en datos: {str(e)}'}, status=400)
