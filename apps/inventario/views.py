# apps/inventario/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from .models import (
    Movimiento,
    Producto,
    Categoria,
    Proveedor,
    Cliente,
    OrdenCompra,
    DetalleCompra,
    Venta,
    DetalleVenta,
    HistorialDescuentoCliente,
)
from .forms import (
    MovimientoForm,
    ProductoForm,
    ProductoEditForm,
    ProveedorForm,
    ClienteForm,
    OrdenCompraForm,
    DetalleCompraForm,
    VentaForm,
    DetalleVentaForm,
)
from .permissions import role_required, RoleRequiredMixin, ROLE_ADMIN, ROLE_VENDEDOR, ROLE_BODEGUERO
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import permission_required
from django.db.models.functions import TruncMonth, TruncDate, TruncWeek, TruncYear
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.http import require_http_methods

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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN)
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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN)
@permission_required('inventario.view_producto', raise_exception=True)
def reportes(request):
    from django.db.models import Avg, Max, Min, DecimalField, Value
    from django.db.models.functions import Coalesce, TruncDate as _TruncDate
    from decimal import Decimal

    hoy = timezone.now().date()

    # ── Filtros avanzados ──
    fecha_desde_raw = request.GET.get('desde', '')
    fecha_hasta_raw = request.GET.get('hasta', '')
    grouping = request.GET.get('grouping', 'dia')
    filtro_forma_pago = request.GET.get('forma_pago', '')
    filtro_estado = request.GET.get('estado', '')
    filtro_categoria = request.GET.get('categoria', '')

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
        rango_label = f'{fecha_desde.strftime("%d/%m/%Y")} al {fecha_hasta.strftime("%d/%m/%Y")}'
    elif fecha_desde:
        rango_label = f'Desde {fecha_desde.strftime("%d/%m/%Y")}'
    elif fecha_hasta:
        rango_label = f'Hasta {fecha_hasta.strftime("%d/%m/%Y")}'

    # Default range: 6 months
    default_desde = hoy - timedelta(days=180)
    rango_desde = fecha_desde or default_desde
    rango_hasta = fecha_hasta or hoy

    # ── Base querysets with date filters ──
    ventas_q = Q(fecha_venta__date__gte=rango_desde, fecha_venta__date__lte=rango_hasta)
    if filtro_forma_pago:
        ventas_q &= Q(forma_pago=filtro_forma_pago)
    if filtro_estado:
        ventas_q &= Q(estado=filtro_estado)

    ventas_periodo = Venta.objects.filter(ventas_q)

    compras_q = Q(fecha_creacion__date__gte=rango_desde, fecha_creacion__date__lte=rango_hasta)
    compras_periodo = OrdenCompra.objects.filter(compras_q)

    movimientos_q = Q(fecha__date__gte=rango_desde, fecha__date__lte=rango_hasta)
    movimientos_rango = Movimiento.objects.filter(movimientos_q)

    # Filtro por categoría (afecta ventas y productos)
    if filtro_categoria and filtro_categoria.isdigit():
        ventas_periodo = ventas_periodo.filter(detalles__producto__categoria_id=int(filtro_categoria)).distinct()

    # ── KPIs principales ──
    total_productos = Producto.objects.filter(activo=True).count()
    valor_inventario = Producto.objects.filter(activo=True).aggregate(
        total=Sum(F('precio') * F('stock'))
    )['total'] or 0
    productos_stock_bajo = Producto.objects.filter(
        activo=True, stock__lte=F('stock_minimo')
    ).count()
    movimientos_hoy = Movimiento.objects.filter(fecha__date=hoy).count()

    # ── KPIs de ventas ──
    ventas_completadas = ventas_periodo.filter(estado='completada')
    total_ventas_count = ventas_completadas.count()
    ingresos_totales = ventas_completadas.aggregate(total=Sum('total'))['total'] or Decimal('0')
    ticket_promedio = ventas_completadas.aggregate(avg=Avg('total'))['avg'] or Decimal('0')

    # Producto más vendido (por DetalleVenta en el período)
    detalle_venta_q = Q(venta__fecha_venta__date__gte=rango_desde, venta__fecha_venta__date__lte=rango_hasta, venta__estado='completada')
    if filtro_categoria and filtro_categoria.isdigit():
        detalle_venta_q &= Q(producto__categoria_id=int(filtro_categoria))

    producto_mas_vendido_qs = DetalleVenta.objects.filter(detalle_venta_q).values(
        'producto__nombre', 'producto__pk'
    ).annotate(
        total_qty=Sum('cantidad')
    ).order_by('-total_qty').first()
    producto_mas_vendido = producto_mas_vendido_qs['producto__nombre'] if producto_mas_vendido_qs else 'N/A'

    # Cliente más frecuente
    cliente_top_qs = ventas_completadas.values('cliente_nombre').annotate(
        total_compras=Count('id'), total_gastado=Sum('total')
    ).order_by('-total_compras').first()
    cliente_mas_frecuente = cliente_top_qs['cliente_nombre'] if cliente_top_qs else 'N/A'
    cliente_top_compras = cliente_top_qs['total_compras'] if cliente_top_qs else 0

    # Rotación de inventario: salidas del período / stock promedio
    total_salidas_qty = movimientos_rango.filter(tipo='salida').aggregate(t=Sum('cantidad'))['t'] or 0
    stock_promedio = Producto.objects.filter(activo=True).aggregate(avg=Avg('stock'))['avg'] or 1
    rotacion_inventario = round(total_salidas_qty / max(stock_promedio, 1), 2)

    # Margen estimado: ingresos (ventas) - costos (compras completadas)
    costos_compras = compras_periodo.filter(estado='completada').aggregate(t=Sum('total'))['t'] or Decimal('0')
    margen_estimado = ingresos_totales - costos_compras
    margen_porcentaje = round((margen_estimado / ingresos_totales * 100), 1) if ingresos_totales > 0 else Decimal('0')

    # ── Movimientos del rango ──
    total_movimientos_rango = movimientos_rango.count()
    total_entradas_rango = movimientos_rango.filter(tipo='entrada').count()
    total_salidas_rango = movimientos_rango.filter(tipo='salida').count()

    # ── Productos críticos ──
    productos_criticos = Producto.objects.filter(
        activo=True, stock__lte=F('stock_minimo')
    ).order_by('stock')[:10]

    # ── Agrupación temporal para gráficos ──
    if grouping == 'semana':
        trunc_func = TruncWeek('fecha')
        trunc_func_venta = TruncWeek('fecha_venta')
        trunc_func_compra = TruncWeek('fecha_creacion')
        date_format = 'Sem %V (%d/%m)'
    elif grouping == 'mes':
        trunc_func = TruncMonth('fecha')
        trunc_func_venta = TruncMonth('fecha_venta')
        trunc_func_compra = TruncMonth('fecha_creacion')
        date_format = '%B %Y'
    elif grouping == 'ano':
        trunc_func = TruncYear('fecha')
        trunc_func_venta = TruncYear('fecha_venta')
        trunc_func_compra = TruncYear('fecha_creacion')
        date_format = '%Y'
    else:
        trunc_func = TruncDate('fecha')
        trunc_func_venta = TruncDate('fecha_venta')
        trunc_func_compra = TruncDate('fecha_creacion')
        date_format = '%d/%m/%Y'

    # Chart 1: Movimientos (entradas vs salidas) - barras
    mov_chart_data = movimientos_rango.annotate(periodo=trunc_func).values('periodo').annotate(
        entradas=Count('id', filter=Q(tipo='entrada')),
        salidas=Count('id', filter=Q(tipo='salida'))
    ).order_by('periodo')
    movimientos_chart_json = json.dumps([{
        'label': item['periodo'].strftime(date_format) if hasattr(item['periodo'], 'strftime') else str(item['periodo']),
        'entradas': item['entradas'],
        'salidas': item['salidas']
    } for item in mov_chart_data], cls=DjangoJSONEncoder)

    # Chart 2: Evolución de ventas (línea) - ingresos por período
    ventas_evolucion = ventas_completadas.annotate(periodo=trunc_func_venta).values('periodo').annotate(
        total=Sum('total'), cantidad=Count('id')
    ).order_by('periodo')
    ventas_evolucion_json = json.dumps([{
        'label': item['periodo'].strftime(date_format) if hasattr(item['periodo'], 'strftime') else str(item['periodo']),
        'total': float(item['total'] or 0),
        'cantidad': item['cantidad']
    } for item in ventas_evolucion], cls=DjangoJSONEncoder)

    # Chart 3: Ventas vs Compras (barras comparativas)
    compras_evolucion = compras_periodo.filter(estado='completada').annotate(
        periodo=trunc_func_compra
    ).values('periodo').annotate(total=Sum('total')).order_by('periodo')
    compras_dict = {
        item['periodo'].strftime(date_format) if hasattr(item['periodo'], 'strftime') else str(item['periodo']): float(item['total'] or 0)
        for item in compras_evolucion
    }
    # Merge with ventas labels
    ventas_vs_compras = []
    for item in ventas_evolucion:
        label = item['periodo'].strftime(date_format) if hasattr(item['periodo'], 'strftime') else str(item['periodo'])
        ventas_vs_compras.append({
            'label': label,
            'ventas': float(item['total'] or 0),
            'compras': compras_dict.get(label, 0)
        })
    ventas_vs_compras_json = json.dumps(ventas_vs_compras, cls=DjangoJSONEncoder)

    # Chart 4: Distribución por categoría (dónut)
    cat_dist = DetalleVenta.objects.filter(detalle_venta_q).values(
        'producto__categoria__nombre'
    ).annotate(
        total=Sum('subtotal'), qty=Sum('cantidad')
    ).order_by('-total')[:10]
    categorias_dist_json = json.dumps([{
        'nombre': item['producto__categoria__nombre'] or 'Sin categoría',
        'total': float(item['total'] or 0),
        'qty': item['qty'] or 0
    } for item in cat_dist], cls=DjangoJSONEncoder)

    # Chart 5: Top 5 productos más vendidos (barras horizontales)
    top_productos_qs = DetalleVenta.objects.filter(detalle_venta_q).values(
        'producto__nombre', 'producto__pk'
    ).annotate(
        total_qty=Sum('cantidad'), total_revenue=Sum('subtotal')
    ).order_by('-total_qty')[:5]
    top_productos_chart_json = json.dumps([{
        'nombre': item['producto__nombre'],
        'cantidad': item['total_qty'] or 0,
        'revenue': float(item['total_revenue'] or 0)
    } for item in top_productos_qs], cls=DjangoJSONEncoder)

    # Also keep list version for table
    productos_mas_vendidos_qs = Producto.objects.filter(
        activo=True,
        movimientos__tipo='salida'
    ).annotate(
        total_vendido=Sum(
            'movimientos__cantidad',
            filter=Q(movimientos__tipo='salida', movimientos__fecha__date__gte=rango_desde, movimientos__fecha__date__lte=rango_hasta)
        )
    ).filter(total_vendido__gt=0).order_by('-total_vendido')[:10]
    productos_mas_vendidos = list(productos_mas_vendidos_qs)
    max_vendido = max((p.total_vendido or 0 for p in productos_mas_vendidos), default=1)
    for producto in productos_mas_vendidos:
        producto.porcentaje_vendido = int((producto.total_vendido or 0) / max_vendido * 100) if max_vendido else 0

    # ── Tablas analíticas ──
    # Productos con menor rotación (con al menos 1 movimiento, pero pocas salidas)
    productos_baja_rotacion = Producto.objects.filter(
        activo=True, stock__gt=0
    ).annotate(
        total_salidas=Coalesce(Sum(
            'movimientos__cantidad',
            filter=Q(movimientos__tipo='salida', movimientos__fecha__date__gte=rango_desde, movimientos__fecha__date__lte=rango_hasta)
        ), 0)
    ).order_by('total_salidas')[:5]

    # Productos sin movimiento en el período
    productos_sin_movimiento = Producto.objects.filter(activo=True).exclude(
        movimientos__fecha__date__gte=rango_desde,
        movimientos__fecha__date__lte=rango_hasta
    ).order_by('-stock')[:10]

    # Clientes destacados
    clientes_destacados = ventas_completadas.values('cliente_nombre').annotate(
        total_compras=Count('id'),
        total_gastado=Sum('total'),
        ticket_avg=Avg('total')
    ).order_by('-total_gastado')[:5]

    # Ventas recientes
    ventas_recientes = Venta.objects.select_related().order_by('-fecha_venta')[:5]

    # ── Insights automáticos ──
    insights = []

    # Comparar con período anterior de misma duración
    delta_dias = (rango_hasta - rango_desde).days
    prev_hasta = rango_desde - timedelta(days=1)
    prev_desde = prev_hasta - timedelta(days=delta_dias)

    prev_ventas_q = Q(fecha_venta__date__gte=prev_desde, fecha_venta__date__lte=prev_hasta, estado='completada')
    if filtro_forma_pago:
        prev_ventas_q &= Q(forma_pago=filtro_forma_pago)
    prev_ingresos = Venta.objects.filter(prev_ventas_q).aggregate(t=Sum('total'))['t'] or Decimal('0')
    prev_ventas_count = Venta.objects.filter(prev_ventas_q).count()

    if prev_ingresos > 0:
        cambio_ingresos = round(((ingresos_totales - prev_ingresos) / prev_ingresos) * 100, 1)
        if cambio_ingresos > 0:
            insights.append({
                'tipo': 'success',
                'icono': 'trending-up',
                'texto': f'Los ingresos aumentaron un {cambio_ingresos}% respecto al período anterior'
            })
        elif cambio_ingresos < 0:
            insights.append({
                'tipo': 'danger',
                'icono': 'trending-down',
                'texto': f'Los ingresos disminuyeron un {abs(cambio_ingresos)}% respecto al período anterior'
            })
        else:
            insights.append({
                'tipo': 'info',
                'icono': 'minus',
                'texto': 'Los ingresos se mantuvieron igual que el período anterior'
            })

    if prev_ventas_count > 0:
        cambio_ventas = round(((total_ventas_count - prev_ventas_count) / prev_ventas_count) * 100, 1)
        if cambio_ventas > 0:
            insights.append({
                'tipo': 'success',
                'icono': 'shopping-cart',
                'texto': f'Las ventas aumentaron un {cambio_ventas}% ({total_ventas_count} vs {prev_ventas_count})'
            })
        elif cambio_ventas < 0:
            insights.append({
                'tipo': 'danger',
                'icono': 'shopping-cart',
                'texto': f'Las ventas cayeron un {abs(cambio_ventas)}% ({total_ventas_count} vs {prev_ventas_count})'
            })

    if producto_mas_vendido_qs:
        insights.append({
            'tipo': 'info',
            'icono': 'star',
            'texto': f'El producto más vendido es "{producto_mas_vendido}" con {producto_mas_vendido_qs["total_qty"]} unidades'
        })

    if productos_stock_bajo > 0:
        insights.append({
            'tipo': 'warning',
            'icono': 'alert-triangle',
            'texto': f'Hay {productos_stock_bajo} producto(s) con stock crítico que requieren reposición'
        })

    # Mejor día de ventas
    mejor_dia_qs = ventas_completadas.annotate(
        dia=TruncDate('fecha_venta')
    ).values('dia').annotate(
        total_dia=Sum('total')
    ).order_by('-total_dia').first()
    if mejor_dia_qs:
        insights.append({
            'tipo': 'info',
            'icono': 'calendar',
            'texto': f'El mejor día de ventas fue {mejor_dia_qs["dia"].strftime("%d/%m/%Y")} con COP {mejor_dia_qs["total_dia"]:,.0f}'
        })

    # Forma de pago más usada
    forma_pago_top = ventas_completadas.values('forma_pago').annotate(
        cnt=Count('id')
    ).order_by('-cnt').first()
    if forma_pago_top:
        pago_labels = dict(Venta.PAGO_CHOICES)
        insights.append({
            'tipo': 'info',
            'icono': 'credit-card',
            'texto': f'La forma de pago más utilizada es "{pago_labels.get(forma_pago_top["forma_pago"], forma_pago_top["forma_pago"])}" ({forma_pago_top["cnt"]} ventas)'
        })

    # Productos sin movimiento
    sin_movimiento_count = Producto.objects.filter(activo=True).exclude(
        movimientos__fecha__date__gte=rango_desde,
        movimientos__fecha__date__lte=rango_hasta
    ).count()
    if sin_movimiento_count > 0:
        insights.append({
            'tipo': 'warning',
            'icono': 'package',
            'texto': f'Hay {sin_movimiento_count} producto(s) sin movimiento en el período (capital muerto)'
        })

    # ── KPI comparison values for template ──
    cambio_ingresos_pct = Decimal('0')
    if prev_ingresos > 0:
        cambio_ingresos_pct = round(((ingresos_totales - prev_ingresos) / prev_ingresos) * 100, 1)

    cambio_ventas_pct = Decimal('0')
    if prev_ventas_count > 0:
        cambio_ventas_pct = round(((total_ventas_count - prev_ventas_count) / prev_ventas_count) * 100, 1)

    prev_ticket = Venta.objects.filter(prev_ventas_q).aggregate(avg=Avg('total'))['avg'] or Decimal('0')
    cambio_ticket_pct = Decimal('0')
    if prev_ticket > 0:
        cambio_ticket_pct = round(((ticket_promedio - prev_ticket) / prev_ticket) * 100, 1)

    # Días promedio de inventario
    avg_daily_sales = Decimal('0')
    if delta_dias > 0 and total_salidas_qty > 0:
        avg_daily_sales = Decimal(str(total_salidas_qty)) / Decimal(str(max(delta_dias, 1)))
    total_stock_actual = Producto.objects.filter(activo=True).aggregate(t=Sum('stock'))['t'] or 0
    dias_inventario = round(Decimal(str(total_stock_actual)) / avg_daily_sales, 1) if avg_daily_sales > 0 else Decimal('0')

    # Top producto por ingresos (no por cantidad)
    top_producto_ingresos_qs = DetalleVenta.objects.filter(detalle_venta_q).values(
        'producto__nombre'
    ).annotate(
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue').first()
    top_producto_ingresos = top_producto_ingresos_qs['producto__nombre'] if top_producto_ingresos_qs else 'N/A'
    top_producto_ingresos_val = float(top_producto_ingresos_qs['total_revenue'] or 0) if top_producto_ingresos_qs else 0
    top_producto_ingresos_pct = round(top_producto_ingresos_val / float(ingresos_totales) * 100, 1) if ingresos_totales > 0 else 0

    # Categorías ranking con porcentajes
    total_ingresos_float = float(ingresos_totales) if ingresos_totales else 1
    categorias_ranking = []
    for item in cat_dist:
        cat_total = float(item['total'] or 0)
        categorias_ranking.append({
            'nombre': item['producto__categoria__nombre'] or 'Sin categoría',
            'ingresos': cat_total,
            'qty': item['qty'] or 0,
            'porcentaje': round(cat_total / total_ingresos_float * 100, 1) if total_ingresos_float > 0 else 0,
        })

    # Productos capital muerto: stock alto + baja o nula rotación
    productos_capital_muerto = Producto.objects.filter(
        activo=True, stock__gt=0
    ).annotate(
        total_salidas=Coalesce(Sum(
            'movimientos__cantidad',
            filter=Q(movimientos__tipo='salida', movimientos__fecha__date__gte=rango_desde, movimientos__fecha__date__lte=rango_hasta)
        ), 0),
        valor_retenido=F('precio') * F('stock')
    ).filter(total_salidas=0).order_by('-valor_retenido')[:10]

    # Rotación chart: Top productos vendidos vs stock actual
    rotacion_chart_qs = DetalleVenta.objects.filter(detalle_venta_q).values(
        'producto__nombre', 'producto__stock'
    ).annotate(
        vendido=Sum('cantidad')
    ).order_by('-vendido')[:8]
    rotacion_chart_json = json.dumps([{
        'nombre': item['producto__nombre'],
        'vendido': item['vendido'] or 0,
        'stock': item['producto__stock'] or 0,
    } for item in rotacion_chart_qs], cls=DjangoJSONEncoder)

    # ── Datos para filtros ──
    categorias = Categoria.objects.all().order_by('nombre')
    formas_pago = Venta.PAGO_CHOICES
    estados_venta = Venta.ESTADO_CHOICES

    context = {
        # KPIs analíticos
        'ingresos_totales': ingresos_totales,
        'prev_ingresos': prev_ingresos,
        'cambio_ingresos_pct': cambio_ingresos_pct,
        'total_ventas_count': total_ventas_count,
        'prev_ventas_count': prev_ventas_count,
        'cambio_ventas_pct': cambio_ventas_pct,
        'ticket_promedio': ticket_promedio,
        'cambio_ticket_pct': cambio_ticket_pct,
        'rotacion_inventario': rotacion_inventario,
        'dias_inventario': dias_inventario,
        'margen_estimado': margen_estimado,
        'margen_porcentaje': margen_porcentaje,
        'costos_compras': costos_compras,
        'top_producto_ingresos': top_producto_ingresos,
        'top_producto_ingresos_val': top_producto_ingresos_val,
        'top_producto_ingresos_pct': top_producto_ingresos_pct,
        'producto_mas_vendido': producto_mas_vendido,
        'cliente_mas_frecuente': cliente_mas_frecuente,
        'cliente_top_compras': cliente_top_compras,
        # Movimientos
        'total_movimientos_rango': total_movimientos_rango,
        'total_entradas_rango': total_entradas_rango,
        'total_salidas_rango': total_salidas_rango,
        'rango_label': rango_label,
        # Charts JSON
        'movimientos_chart_json': movimientos_chart_json,
        'ventas_evolucion_json': ventas_evolucion_json,
        'ventas_vs_compras_json': ventas_vs_compras_json,
        'categorias_dist_json': categorias_dist_json,
        'top_productos_chart_json': top_productos_chart_json,
        'rotacion_chart_json': rotacion_chart_json,
        # Tables
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_baja_rotacion': productos_baja_rotacion,
        'productos_sin_movimiento': productos_sin_movimiento,
        'productos_capital_muerto': productos_capital_muerto,
        'categorias_ranking': categorias_ranking,
        'clientes_destacados': clientes_destacados,
        # Insights
        'insights': insights,
        # Filters
        'fecha_desde': fecha_desde_raw,
        'fecha_hasta': fecha_hasta_raw,
        'grouping': grouping,
        'filtro_forma_pago': filtro_forma_pago,
        'filtro_estado': filtro_estado,
        'filtro_categoria': filtro_categoria,
        'categorias': categorias,
        'formas_pago': formas_pago,
        'estados_venta': estados_venta,
    }

    return render(request, 'inventario/reportes.html', context)


# ============================================================================
# PROVEEDORES
# ============================================================================

@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    ordenes = proveedor.ordenes_compra.all().order_by('-fecha_creacion')[:10]
    return render(request, 'inventario/detalle_proveedor.html', {
        'proveedor': proveedor, 'ordenes': ordenes,
    })


# ============================================================================
# COMPRAS
# ============================================================================


def _filtrar_compras_queryset(compras, params):
    estado = params.get('estado', '')
    if estado:
        compras = compras.filter(estado=estado)

    proveedor_id = params.get('proveedor', '')
    if proveedor_id and proveedor_id.isdigit():
        compras = compras.filter(proveedor_id=int(proveedor_id))

    fecha_desde = params.get('desde', '')
    if fecha_desde:
        compras = compras.filter(fecha_creacion__date__gte=fecha_desde)

    fecha_hasta = params.get('hasta', '')
    if fecha_hasta:
        compras = compras.filter(fecha_creacion__date__lte=fecha_hasta)

    return compras, estado, proveedor_id, fecha_desde, fecha_hasta


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def lista_compras(request):
    compras = OrdenCompra.objects.all().select_related('proveedor')
    compras, estado, proveedor_id, fecha_desde, fecha_hasta = _filtrar_compras_queryset(
        compras,
        request.GET,
    )

    paginator = Paginator(compras, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/lista_compras.html', {
        'page_obj': page_obj, 'proveedores': proveedores,
        'estado': estado, 'proveedor_seleccionado': proveedor_id,
        'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta,
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def crear_compra(request):
    """Redirects to the unified fast purchase interface."""
    return redirect('inventario:compra_rapida')


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def detalle_compra(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    detalles = orden.detalles.all().select_related('producto')
    return render(request, 'inventario/detalle_compra.html', {
        'orden': orden, 'detalles': detalles,
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
@require_http_methods(["POST"])
def recibir_compra(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if orden.estado in ('completada', 'cancelada'):
        messages.error(request, 'Esta orden ya fue completada o cancelada.')
        return redirect('inventario:detalle_compra', pk=orden.pk)

    for detalle in orden.detalles.all():
        detalle.cantidad_recibida = detalle.cantidad_solicitada
        detalle.save()
        # Crear movimiento de entrada (el modelo Movimiento actualiza stock)
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


def _filtrar_ventas_queryset(ventas, params):
    estado = params.get('estado', '')
    if estado:
        ventas = ventas.filter(estado=estado)

    forma_pago = params.get('forma_pago', '')
    if forma_pago:
        ventas = ventas.filter(forma_pago=forma_pago)

    fecha_desde = params.get('desde', '')
    if fecha_desde:
        ventas = ventas.filter(fecha_venta__date__gte=fecha_desde)

    fecha_hasta = params.get('hasta', '')
    if fecha_hasta:
        ventas = ventas.filter(fecha_venta__date__lte=fecha_hasta)

    query = params.get('q', '')
    if query:
        ventas = ventas.filter(
            Q(numero__icontains=query)
            | Q(cliente_nombre__icontains=query)
            | Q(usuario_vendedor__icontains=query)
        )

    return ventas, estado, forma_pago, fecha_desde, fecha_hasta, query


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
def lista_ventas(request):
    ventas = Venta.objects.all()
    ventas, estado, forma_pago, fecha_desde, fecha_hasta, query = _filtrar_ventas_queryset(
        ventas,
        request.GET,
    )

    paginator = Paginator(ventas, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'inventario/lista_ventas.html', {
        'page_obj': page_obj, 'estado': estado, 'forma_pago': forma_pago,
        'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta, 'query': query,
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
def crear_venta(request):
    """Redirects to the unified POS sale interface."""
    return redirect('inventario:venta_rapida')


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
def detalle_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.all().select_related('producto')
    return render(request, 'inventario/detalle_venta.html', {
        'venta': venta, 'detalles': detalles,
    })


@login_required
@role_required(ROLE_ADMIN)
@require_http_methods(["POST"])
def cancelar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if venta.estado == 'cancelada':
        messages.error(request, 'Esta venta ya está cancelada.')
        return redirect('inventario:detalle_venta', pk=venta.pk)

    # Revertir stock vía movimiento (el modelo Movimiento actualiza stock)
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
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
def venta_rapida(request):
    """Renders the POS-style fast sale interface."""
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/venta_rapida.html', {
        'clientes': clientes,
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def compra_rapida(request):
    """Renders the fast purchase interface."""
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/compra_rapida.html', {
        'proveedores': proveedores,
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
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
    cliente_id = data.get('cliente_id')
    descuento_manual_raw = data.get('descuento_manual_porcentaje', 0)
    forma_pago = data.get('forma_pago', 'efectivo')
    notas = data.get('notas', '')

    try:
        descuento_manual_porcentaje = Decimal(str(descuento_manual_raw or 0))
    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Descuento manual inválido'}, status=400)

    if descuento_manual_porcentaje < 0 or descuento_manual_porcentaje > 100:
        return JsonResponse({'ok': False, 'error': 'El descuento manual debe estar entre 0 y 100'}, status=400)

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

            cliente_obj = None
            descuento_cliente_porcentaje = Decimal('0')
            if cliente_id:
                try:
                    cliente_obj = Cliente.objects.get(pk=cliente_id, activo=True)
                    cliente = cliente_obj.nombre
                    descuento_cliente_porcentaje = cliente_obj.descuento_vigente()
                except Cliente.DoesNotExist:
                    return JsonResponse({'ok': False, 'error': 'Cliente no encontrado'}, status=400)

            descuento_porcentaje = descuento_cliente_porcentaje + descuento_manual_porcentaje
            if descuento_porcentaje > Decimal('100'):
                descuento_porcentaje = Decimal('100')

            # Create sale
            venta = Venta(
                cliente=cliente_obj,
                cliente_nombre=cliente,
                forma_pago=forma_pago,
                notas=notas,
                estado='completada',
                usuario_vendedor=request.user.username,
            )
            venta.save()

            subtotal = Decimal('0')
            for vi in validated:
                detalle = DetalleVenta(
                    venta=venta,
                    producto=vi['producto'],
                    cantidad=vi['cantidad'],
                    precio_unitario=vi['precio'],
                    descuento_porcentaje=Decimal('0'),
                )
                detalle.save()
                subtotal += detalle.subtotal
                # Movimiento actualiza stock en guardado atómico
                Movimiento.objects.create(
                    producto=vi['producto'],
                    tipo='salida',
                    cantidad=vi['cantidad'],
                    descripcion=f'Venta POS {venta.numero}',
                    usuario=request.user.username,
                )

            descuento_total = (subtotal * descuento_porcentaje) / Decimal('100')
            total = subtotal - descuento_total
            if total < 0:
                total = Decimal('0')

            venta.subtotal = subtotal
            venta.descuento_total = descuento_total
            venta.total = total
            venta.save(update_fields=['subtotal', 'descuento_total', 'total'])

            if cliente_obj and descuento_total > 0:
                tipo_descuento = 'automatico'
                if descuento_manual_porcentaje > 0 and descuento_cliente_porcentaje > 0:
                    tipo_descuento = 'combinado'
                elif descuento_manual_porcentaje > 0:
                    tipo_descuento = 'manual'

                HistorialDescuentoCliente.objects.create(
                    cliente=cliente_obj,
                    venta=venta,
                    porcentaje_aplicado=descuento_porcentaje,
                    monto_descuento=descuento_total,
                    tipo=tipo_descuento,
                )

        return JsonResponse({
            'ok': True,
            'venta_id': venta.pk,
            'numero': venta.numero,
            'subtotal': str(venta.subtotal),
            'descuento_total': str(venta.descuento_total),
            'total': str(venta.total),
        })

    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=400)
    except (ValueError, InvalidOperation, KeyError) as e:
        return JsonResponse({'ok': False, 'error': f'Error en datos: {str(e)}'}, status=400)


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
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
                # Movimiento actualiza stock en guardado atómico
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


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
@require_http_methods(["GET"])
def api_cliente_descuento(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk, activo=True)
    porcentaje = cliente.descuento_vigente()
    return JsonResponse({
        'id': cliente.pk,
        'nombre': cliente.nombre,
        'descuento_porcentaje': str(porcentaje),
    })


# ============================================================================
# CLIENTES (CBV)
# ============================================================================


class ClienteListView(RoleRequiredMixin, ListView):
    model = Cliente
    template_name = 'inventario/lista_clientes.html'
    context_object_name = 'clientes'
    paginate_by = 20
    allowed_groups = (ROLE_ADMIN, ROLE_VENDEDOR)

    def get_queryset(self):
        qs = Cliente.objects.all().order_by('nombre')
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(documento__icontains=q)
                | Q(email__icontains=q)
                | Q(telefono__icontains=q)
            )
        estado = self.request.GET.get('activo', '')
        if estado == '1':
            qs = qs.filter(activo=True)
        elif estado == '0':
            qs = qs.filter(activo=False)
        return qs


class ClienteCreateView(RoleRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'inventario/cliente_form.html'
    success_url = reverse_lazy('inventario:lista_clientes')
    allowed_groups = (ROLE_ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado correctamente.')
        return super().form_valid(form)


class ClienteUpdateView(RoleRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'inventario/cliente_form.html'
    success_url = reverse_lazy('inventario:lista_clientes')
    allowed_groups = (ROLE_ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)


# ============================================================================
# PDF DOCUMENTS
# ============================================================================


def _build_venta_pdf(venta, detalles):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, y, 'El Solterito - Factura de Venta')
    y -= 24
    p.setFont('Helvetica', 10)
    p.drawString(40, y, f'Factura: {venta.numero}')
    p.drawString(250, y, f'Fecha: {venta.fecha_venta.strftime("%d/%m/%Y %H:%M")}')
    y -= 16
    p.drawString(40, y, f'Cliente: {venta.cliente_nombre}')
    p.drawString(250, y, f'Vendedor: {venta.usuario_vendedor}')
    y -= 24

    p.setFont('Helvetica-Bold', 10)
    p.drawString(40, y, 'Producto')
    p.drawString(280, y, 'Cant')
    p.drawString(340, y, 'Precio')
    p.drawString(440, y, 'Subtotal')
    y -= 14
    p.line(40, y, width - 40, y)
    y -= 14

    p.setFont('Helvetica', 10)
    for d in detalles:
        if y < 120:
            p.showPage()
            y = height - 50
        p.drawString(40, y, d.producto.nombre[:38])
        p.drawRightString(310, y, str(d.cantidad))
        p.drawRightString(410, y, f'COP {float(d.precio_unitario):,.0f}')
        p.drawRightString(540, y, f'COP {float(d.subtotal):,.0f}')
        y -= 14

    y -= 12
    p.line(330, y, 540, y)
    y -= 16
    p.drawString(360, y, 'Subtotal:')
    p.drawRightString(540, y, f'COP {float(venta.subtotal):,.0f}')
    y -= 14
    p.drawString(360, y, 'Descuento:')
    p.drawRightString(540, y, f'COP {float(venta.descuento_total):,.0f}')
    y -= 14
    p.setFont('Helvetica-Bold', 10)
    p.drawString(360, y, 'Total:')
    p.drawRightString(540, y, f'COP {float(venta.total):,.0f}')

    p.showPage()
    p.save()
    return buffer.getvalue()


def _build_compra_pdf(orden, detalles):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, y, 'El Solterito - Comprobante de Compra')
    y -= 24
    p.setFont('Helvetica', 10)
    p.drawString(40, y, f'Compra: {orden.numero}')
    p.drawString(250, y, f'Fecha: {orden.fecha_creacion.strftime("%d/%m/%Y %H:%M")}')
    y -= 16
    p.drawString(40, y, f'Proveedor: {orden.proveedor.nombre}')
    y -= 24

    p.setFont('Helvetica-Bold', 10)
    p.drawString(40, y, 'Producto')
    p.drawString(280, y, 'Cant')
    p.drawString(340, y, 'Costo')
    p.drawString(440, y, 'Subtotal')
    y -= 14
    p.line(40, y, width - 40, y)
    y -= 14

    p.setFont('Helvetica', 10)
    for d in detalles:
        if y < 120:
            p.showPage()
            y = height - 50
        p.drawString(40, y, d.producto.nombre[:38])
        p.drawRightString(310, y, str(d.cantidad_solicitada))
        p.drawRightString(410, y, f'COP {float(d.precio_unitario):,.0f}')
        p.drawRightString(540, y, f'COP {float(d.subtotal):,.0f}')
        y -= 14

    y -= 12
    p.line(330, y, 540, y)
    y -= 16
    p.setFont('Helvetica-Bold', 10)
    p.drawString(360, y, 'Total:')
    p.drawRightString(540, y, f'COP {float(orden.total):,.0f}')

    p.showPage()
    p.save()
    return buffer.getvalue()


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
def venta_pdf(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente'), pk=pk)
    detalles = venta.detalles.select_related('producto')
    pdf = _build_venta_pdf(venta, detalles)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{venta.numero}.pdf"'
    return response


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def compra_pdf(request, pk):
    orden = get_object_or_404(OrdenCompra.objects.select_related('proveedor'), pk=pk)
    detalles = orden.detalles.select_related('producto')
    pdf = _build_compra_pdf(orden, detalles)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="compra_{orden.numero}.pdf"'
    return response


def _build_ventas_list_pdf(ventas, filtros_texto):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont('Helvetica-Bold', 15)
    p.drawString(40, y, 'El Solterito - Registro de Ventas')
    y -= 18
    p.setFont('Helvetica', 9)
    p.drawString(40, y, f'Generado: {timezone.now().strftime("%d/%m/%Y %H:%M")}')
    y -= 14
    p.drawString(40, y, f'Filtro aplicado: {filtros_texto}')
    y -= 18

    p.setFont('Helvetica-Bold', 9)
    p.drawString(40, y, 'Numero')
    p.drawString(120, y, 'Cliente')
    p.drawString(255, y, 'Vendedor')
    p.drawString(350, y, 'Fecha')
    p.drawString(425, y, 'Estado')
    p.drawRightString(550, y, 'Total')
    y -= 10
    p.line(40, y, width - 40, y)
    y -= 12

    total_general = 0
    p.setFont('Helvetica', 8)
    if not ventas:
        p.drawString(40, y, 'No hay ventas para los criterios seleccionados.')
    else:
        for venta in ventas:
            if y < 70:
                p.showPage()
                y = height - 50
                p.setFont('Helvetica-Bold', 9)
                p.drawString(40, y, 'Numero')
                p.drawString(120, y, 'Cliente')
                p.drawString(255, y, 'Vendedor')
                p.drawString(350, y, 'Fecha')
                p.drawString(425, y, 'Estado')
                p.drawRightString(550, y, 'Total')
                y -= 10
                p.line(40, y, width - 40, y)
                y -= 12
                p.setFont('Helvetica', 8)

            total_general += float(venta.total or 0)
            p.drawString(40, y, str(venta.numero)[:14])
            p.drawString(120, y, str(venta.cliente_nombre or '-')[:24])
            p.drawString(255, y, str(venta.usuario_vendedor or '-')[:16])
            p.drawString(350, y, venta.fecha_venta.strftime('%d/%m/%y'))
            p.drawString(425, y, venta.get_estado_display())
            p.drawRightString(550, y, f'COP {float(venta.total):,.0f}')
            y -= 12

    y -= 10
    p.line(370, y, 550, y)
    y -= 14
    p.setFont('Helvetica-Bold', 10)
    p.drawString(410, y, 'Total listado:')
    p.drawRightString(550, y, f'COP {total_general:,.0f}')

    p.showPage()
    p.save()
    return buffer.getvalue()


def _build_compras_list_pdf(compras, filtros_texto):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont('Helvetica-Bold', 15)
    p.drawString(40, y, 'El Solterito - Registro de Compras')
    y -= 18
    p.setFont('Helvetica', 9)
    p.drawString(40, y, f'Generado: {timezone.now().strftime("%d/%m/%Y %H:%M")}')
    y -= 14
    p.drawString(40, y, f'Filtro aplicado: {filtros_texto}')
    y -= 18

    p.setFont('Helvetica-Bold', 9)
    p.drawString(40, y, 'Numero')
    p.drawString(140, y, 'Proveedor')
    p.drawString(330, y, 'Fecha')
    p.drawString(410, y, 'Estado')
    p.drawRightString(550, y, 'Total')
    y -= 10
    p.line(40, y, width - 40, y)
    y -= 12

    total_general = 0
    p.setFont('Helvetica', 8)
    if not compras:
        p.drawString(40, y, 'No hay compras para los criterios seleccionados.')
    else:
        for orden in compras:
            if y < 70:
                p.showPage()
                y = height - 50
                p.setFont('Helvetica-Bold', 9)
                p.drawString(40, y, 'Numero')
                p.drawString(140, y, 'Proveedor')
                p.drawString(330, y, 'Fecha')
                p.drawString(410, y, 'Estado')
                p.drawRightString(550, y, 'Total')
                y -= 10
                p.line(40, y, width - 40, y)
                y -= 12
                p.setFont('Helvetica', 8)

            total_general += float(orden.total or 0)
            p.drawString(40, y, str(orden.numero)[:18])
            p.drawString(140, y, str(orden.proveedor.nombre if orden.proveedor else '-')[:32])
            p.drawString(330, y, orden.fecha_creacion.strftime('%d/%m/%y'))
            p.drawString(410, y, orden.get_estado_display())
            p.drawRightString(550, y, f'COP {float(orden.total):,.0f}')
            y -= 12

    y -= 10
    p.line(370, y, 550, y)
    y -= 14
    p.setFont('Helvetica-Bold', 10)
    p.drawString(410, y, 'Total listado:')
    p.drawRightString(550, y, f'COP {total_general:,.0f}')

    p.showPage()
    p.save()
    return buffer.getvalue()


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
def ventas_pdf_lista(request):
    scope = request.GET.get('scope', 'filtered')
    ventas = Venta.objects.all().order_by('-fecha_venta')

    if scope == 'all':
        filtros_texto = 'Todos los registros'
    else:
        ventas, estado, forma_pago, fecha_desde, fecha_hasta, query = _filtrar_ventas_queryset(ventas, request.GET)
        filtros_texto = (
            f'q={query or "-"}, estado={estado or "-"}, pago={forma_pago or "-"}, '
            f'desde={fecha_desde or "-"}, hasta={fecha_hasta or "-"}'
        )

    pdf = _build_ventas_list_pdf(list(ventas), filtros_texto)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="ventas_registro.pdf"'
    return response


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def compras_pdf_lista(request):
    scope = request.GET.get('scope', 'filtered')
    compras = OrdenCompra.objects.select_related('proveedor').order_by('-fecha_creacion')

    if scope == 'all':
        filtros_texto = 'Todos los registros'
    else:
        compras, estado, proveedor_id, fecha_desde, fecha_hasta = _filtrar_compras_queryset(compras, request.GET)
        filtros_texto = (
            f'proveedor={proveedor_id or "-"}, estado={estado or "-"}, '
            f'desde={fecha_desde or "-"}, hasta={fecha_hasta or "-"}'
        )

    pdf = _build_compras_list_pdf(list(compras), filtros_texto)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="compras_registro.pdf"'
    return response
