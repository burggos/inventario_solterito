from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth, TruncDate, TruncWeek, TruncYear
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder

from .models import (
    Producto, Movimiento, Categoria, Venta, OrdenCompra, DetalleVenta
)

def get_dashboard_metrics():
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
    
    ultimos_movimientos = Movimiento.objects.select_related('producto').order_by('-fecha')[:8]
    productos_criticos = Producto.objects.filter(
        activo=True, stock__lte=F('stock_minimo')
    ).order_by('stock')[:5]
    
    categorias_dist = Categoria.objects.filter(
        productos__activo=True
    ).annotate(
        total=Count('productos')
    ).order_by('-total')[:8]
    categorias_chart = json.dumps(
        [{'nombre': c.nombre, 'total': c.total} for c in categorias_dist],
        cls=DjangoJSONEncoder
    )
    
    desde_7d = hoy - timedelta(days=7)
    ventas_semana = Venta.objects.filter(
        fecha_venta__date__gte=desde_7d, estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    compras_pendientes = OrdenCompra.objects.filter(estado='pendiente').count()
    
    return {
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



def get_reportes_metrics(get_data):
    from django.db.models import Avg, Max, Min, DecimalField, Value
    from django.db.models.functions import Coalesce, TruncDate as _TruncDate
    from django.db.models import Sum, Count, F, Q
    from django.db.models.functions import TruncMonth, TruncDate, TruncWeek, TruncYear
    from decimal import Decimal
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    from .models import Producto, Movimiento, Categoria, Venta, OrdenCompra, DetalleVenta
    from django.utils import timezone
    from datetime import timedelta, datetime

    hoy = timezone.now().date()

    # ── Filtros avanzados ──
    fecha_desde_raw = get_data.get('desde', '')
    fecha_hasta_raw = get_data.get('hasta', '')
    grouping = get_data.get('grouping', 'dia')
    filtro_forma_pago = get_data.get('forma_pago', '')
    filtro_estado = get_data.get('estado', '')
    filtro_categoria = get_data.get('categoria', '')
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

    # Producto más vendido y top productos se calculan junto al chart (ver sección gráficos)
    producto_mas_vendido = 'N/A'
    producto_mas_vendido_top_qty = 0

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

    # Costo de compras en el período (para KPI secundario y gráfico Ventas vs Compras)
    costos_compras = compras_periodo.filter(estado='completada').aggregate(t=Sum('total'))['t'] or Decimal('0')
    # Margen bruto real: suma(subtotal_venta - precio_compra * cantidad) por línea de venta
    # Más preciso que ingresos - compras_período porque usa COGS real de cada producto vendido
    margen_estimado = DetalleVenta.objects.filter(detalle_venta_q).annotate(
        costo_unitario=Coalesce(F('producto__precio_compra'), F('producto__precio'))
    ).aggregate(
        total=Sum(F('subtotal') - F('costo_unitario') * F('cantidad'))
    )['total'] or Decimal('0')
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

    # Chart 5 + KPI + tabla: una sola query DetalleVenta para gráfico, KPI y tabla (fuente unificada)
    top_productos_data = list(DetalleVenta.objects.filter(detalle_venta_q).values(
        'producto__nombre', 'producto__pk'
    ).annotate(
        total_qty=Sum('cantidad'), total_revenue=Sum('subtotal')
    ).order_by('-total_qty')[:10])

    # KPI: producto más vendido por cantidad
    if top_productos_data:
        producto_mas_vendido = top_productos_data[0]['producto__nombre']
        producto_mas_vendido_top_qty = top_productos_data[0]['total_qty'] or 0

    # Chart: top 5 por cantidad (ingresos en tooltip)
    top_productos_chart_json = json.dumps([{
        'nombre': item['producto__nombre'],
        'cantidad': item['total_qty'] or 0,
        'revenue': float(item['total_revenue'] or 0)
    } for item in top_productos_data[:5]], cls=DjangoJSONEncoder)

    # Tabla: misma fuente que el gráfico — consistencia garantizada, sin ajustes manuales
    _top_pks = [item['producto__pk'] for item in top_productos_data]
    _qty_map = {item['producto__pk']: (item['total_qty'] or 0) for item in top_productos_data}
    _max_qty = max(_qty_map.values(), default=1)
    _prods_map = {p.pk: p for p in Producto.objects.filter(pk__in=_top_pks).select_related('categoria')}
    productos_mas_vendidos = []
    for item in top_productos_data:
        p = _prods_map.get(item['producto__pk'])
        if p:
            p.total_vendido = _qty_map[p.pk]
            p.porcentaje_vendido = int(p.total_vendido / _max_qty * 100) if _max_qty else 0
            productos_mas_vendidos.append(p)

    # ── Tablas analíticas ──
    # Baja rotación: productos CON ventas pero pocas (cero-ventas van a Capital Muerto, sin superposición)
    productos_baja_rotacion = Producto.objects.filter(
        activo=True, stock__gt=0
    ).annotate(
        total_salidas=Coalesce(Sum(
            'movimientos__cantidad',
            filter=Q(movimientos__tipo='salida', movimientos__fecha__date__gte=rango_desde, movimientos__fecha__date__lte=rango_hasta)
        ), 0)
    ).filter(total_salidas__gt=0).order_by('total_salidas')[:5]

    # Productos sin movimiento en el período (count para insight, slice para tabla)
    _sin_movimiento_qs = Producto.objects.filter(activo=True).exclude(
        movimientos__fecha__date__gte=rango_desde,
        movimientos__fecha__date__lte=rango_hasta
    )
    sin_movimiento_total = _sin_movimiento_qs.count()
    productos_sin_movimiento = _sin_movimiento_qs.order_by('-stock')[:10]

    # Clientes destacados
    clientes_destacados = ventas_completadas.values('cliente_nombre').annotate(
        total_compras=Count('id'),
        total_gastado=Sum('total'),
        ticket_avg=Avg('total')
    ).order_by('-total_gastado')[:5]

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

    # KPI comparativos calculados una sola vez — reutilizados en insights y en el template
    cambio_ingresos_pct = Decimal('0')
    if prev_ingresos > 0:
        cambio_ingresos_pct = round(((ingresos_totales - prev_ingresos) / prev_ingresos) * 100, 1)

    cambio_ventas_pct = Decimal('0')
    if prev_ventas_count > 0:
        cambio_ventas_pct = round(((total_ventas_count - prev_ventas_count) / prev_ventas_count) * 100, 1)

    if cambio_ingresos_pct > 0:
        insights.append({
            'tipo': 'success',
            'icono': 'trending-up',
            'texto': f'Los ingresos aumentaron un {cambio_ingresos_pct}% respecto al período anterior'
        })
    elif cambio_ingresos_pct < 0:
        insights.append({
            'tipo': 'danger',
            'icono': 'trending-down',
            'texto': f'Los ingresos disminuyeron un {abs(cambio_ingresos_pct)}% respecto al período anterior'
        })
    elif prev_ingresos > 0:
        insights.append({
            'tipo': 'info',
            'icono': 'minus',
            'texto': 'Los ingresos se mantuvieron igual que el período anterior'
        })

    if cambio_ventas_pct > 0:
        insights.append({
            'tipo': 'success',
            'icono': 'shopping-cart',
            'texto': f'Las ventas aumentaron un {cambio_ventas_pct}% ({total_ventas_count} vs {prev_ventas_count})'
        })
    elif cambio_ventas_pct < 0:
        insights.append({
            'tipo': 'danger',
            'icono': 'shopping-cart',
            'texto': f'Las ventas cayeron un {abs(cambio_ventas_pct)}% ({total_ventas_count} vs {prev_ventas_count})'
        })

    if top_productos_data:
        insights.append({
            'tipo': 'info',
            'icono': 'star',
            'texto': f'El producto más vendido es "{producto_mas_vendido}" con {producto_mas_vendido_top_qty} unidades'
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

    # Productos sin movimiento (reutiliza el conteo ya calculado, sin query extra)
    if sin_movimiento_total > 0:
        insights.append({
            'tipo': 'warning',
            'icono': 'package',
            'texto': f'Hay {sin_movimiento_total} producto(s) sin ningún movimiento en el período'
        })

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

    # Top producto por ingresos — derivado de top_productos_data (sin query adicional)
    _top_by_revenue = max(top_productos_data, key=lambda x: x['total_revenue'] or 0, default=None)
    top_producto_ingresos = _top_by_revenue['producto__nombre'] if _top_by_revenue else 'N/A'
    top_producto_ingresos_val = float(_top_by_revenue['total_revenue'] or 0) if _top_by_revenue else 0
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
        valor_retenido=Coalesce(F('precio_compra'), F('precio')) * F('stock')
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


def crear_producto_con_stock_inicial(form, username):
    from django.db import transaction
    from django.utils import timezone
    from .models import Proveedor, OrdenCompra, DetalleCompra, Movimiento

    stock_inicial = form.cleaned_data.get('stock_inicial') or 0
    with transaction.atomic():
        producto = form.save(commit=False)
        producto.stock = 0  # Stock managed via Movimiento
        producto.save()

        if stock_inicial > 0:
            proveedor_seleccionado = producto.proveedor
            proveedor_default, _ = Proveedor.objects.get_or_create(
                nombre='Proveedor Alta Inicial',
                defaults={
                    'contacto_principal': 'Registro automático del sistema',
                    'activo': True,
                },
            )

            orden_compra = OrdenCompra.objects.create(
                proveedor=proveedor_seleccionado or proveedor_default,
                estado='completada',
                fecha_entrega_real=timezone.now().date(),
                notas=f'Compra automática por creación del producto "{producto.nombre}"',
                usuario_creador=username,
            )

            precio_compra_ref = producto.precio_compra if producto.precio_compra is not None else producto.precio
            DetalleCompra.objects.create(
                orden_compra=orden_compra,
                producto=producto,
                cantidad_solicitada=stock_inicial,
                cantidad_recibida=stock_inicial,
                precio_unitario=precio_compra_ref,
            )

            orden_compra.total = precio_compra_ref * stock_inicial
            orden_compra.save(update_fields=['total'])

            Movimiento.objects.create(
                producto=producto,
                tipo='entrada',
                cantidad=stock_inicial,
                descripcion=f'Stock inicial por alta de producto ({orden_compra.numero})',
                usuario=username,
            )
    return producto
