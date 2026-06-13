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
    CategoriaForm,
)
from .permissions import role_required, RoleRequiredMixin, ROLE_ADMIN, ROLE_VENDEDOR, ROLE_BODEGUERO
from django.db.models import Sum, Count, Q as ModelQ, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.db.models.functions import TruncMonth, TruncDate, TruncWeek, TruncYear
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.http import require_http_methods
import logging
import time

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Main dashboard with KPIs and quick overview."""
    from .services import get_dashboard_metrics
    context = get_dashboard_metrics()
    return render(request, 'inventario/dashboard.html', context)


@login_required
def lista_productos(request):
    productos = Producto.objects.select_related('categoria', 'proveedor')

    estado = request.GET.get('estado', 'activos')
    if estado == 'desactivados':
        productos = productos.filter(activo=False)
    elif estado == 'todos':
        pass
    else:
        estado = 'activos'
        productos = productos.filter(activo=True)
    
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
        'estado_seleccionado': estado,
        'categoria_seleccionada': categoria_id,
        'stock_bajo': stock_bajo,
    }
    return render(request, 'inventario/lista_productos.html', context)


@login_required
def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'proveedor'),
        pk=pk,
    )
    movimientos = list(producto.movimientos.all().order_by('-fecha')[:12])

    hoy = timezone.now().date()

    def construir_tendencia(dias):
        inicio = hoy - timedelta(days=dias - 1)
        movimientos_rango = list(
            producto.movimientos.filter(fecha__date__gte=inicio, fecha__date__lte=hoy).order_by('fecha')
        )

        neto_rango = 0
        for mov in movimientos_rango:
            if mov.tipo == 'entrada':
                neto_rango += mov.cantidad
            elif mov.tipo == 'salida':
                neto_rango -= mov.cantidad

        stock_inicio = producto.stock - neto_rango
        stock_cursor = stock_inicio
        movimientos_por_dia = {}
        for mov in movimientos_rango:
            dia = mov.fecha.date()
            if dia not in movimientos_por_dia:
                movimientos_por_dia[dia] = {'entrada': 0, 'salida': 0}
            if mov.tipo == 'entrada':
                movimientos_por_dia[dia]['entrada'] += mov.cantidad
            elif mov.tipo == 'salida':
                movimientos_por_dia[dia]['salida'] += mov.cantidad

        tendencia = []
        cursor_fecha = inicio
        while cursor_fecha <= hoy:
            resumen = movimientos_por_dia.get(cursor_fecha, {'entrada': 0, 'salida': 0})
            variacion = resumen['entrada'] - resumen['salida']
            stock_cursor += variacion
            tendencia.append(
                {
                    'fecha': cursor_fecha.strftime('%d/%m'),
                    'stock': max(stock_cursor, 0),
                    'entrada': resumen['entrada'],
                    'salida': resumen['salida'],
                    'variacion': variacion,
                }
            )
            cursor_fecha += timedelta(days=1)

        return tendencia

    tendencia_stock_7 = construir_tendencia(7)
    tendencia_stock_30 = construir_tendencia(30)
    tiene_movimientos = producto.movimientos.exists()

    context = {
        'producto': producto,
        'movimientos': movimientos,
        'tiene_movimientos': tiene_movimientos,
        'tendencia_stock_7': tendencia_stock_7,
        'tendencia_stock_30': tendencia_stock_30,
        'hoy_label': hoy.strftime('%d/%m'),
    }
    return render(request, 'inventario/detalle_producto.html', context)


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada correctamente.')
            return redirect('inventario:lista_productos')
    else:
        form = CategoriaForm()
    return render(request, 'inventario/crear_categoria.html', {'form': form})

@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            from .services import crear_producto_con_stock_inicial
            producto = crear_producto_con_stock_inicial(form, request.user.username)
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
@role_required(ROLE_ADMIN)
def desactivar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == 'POST':
        producto.activo = False
        producto.save(update_fields=['activo', 'fecha_actualizacion'])
        messages.success(request, f'Producto "{producto.nombre}" desactivado correctamente.')
        return redirect('inventario:lista_productos')

    return redirect('inventario:detalle_producto', pk=producto.pk)

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
        form = MovimientoForm(request.POST, user=request.user)
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
        form = MovimientoForm(initial=initial, user=request.user)
    
    return render(request, 'inventario/crear_movimiento.html', {
        'form': form,
        'selected_product': selected_product,
    })


@login_required
@role_required(ROLE_ADMIN)
@permission_required('inventario.view_producto', raise_exception=True)
def reportes(request):
    from .services import get_reportes_metrics
    context = get_reportes_metrics(request.GET)
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

    detalles = list(orden.detalles.all().select_related('producto'))
    if not detalles:
        messages.error(request, 'La orden no tiene ítems para recibir.')
        return redirect('inventario:detalle_compra', pk=orden.pk)

    valores_recibidos = {}
    for detalle in detalles:
        if detalle.cantidad_recibida >= detalle.cantidad_solicitada:
            field_name = f'recibido_{detalle.pk}'
            raw_value = request.POST.get(field_name)
            if raw_value is not None:
                try:
                    cantidad_intentada = int(raw_value)
                except (TypeError, ValueError):
                    messages.error(request, f'Cantidad inválida para {detalle.producto.nombre}.')
                    return redirect('inventario:detalle_compra', pk=orden.pk)

                if cantidad_intentada != detalle.cantidad_recibida:
                    messages.error(
                        request,
                        f'{detalle.producto.nombre} ya está completamente recibido y no puede editarse de nuevo.',
                    )
                    return redirect('inventario:detalle_compra', pk=orden.pk)

            valores_recibidos[detalle.pk] = detalle.cantidad_recibida
            continue

        field_name = f'recibido_{detalle.pk}'
        raw_value = request.POST.get(field_name, str(detalle.cantidad_recibida))
        try:
            cantidad_recibida = int(raw_value)
        except (TypeError, ValueError):
            messages.error(request, f'Cantidad inválida para {detalle.producto.nombre}.')
            return redirect('inventario:detalle_compra', pk=orden.pk)

        if cantidad_recibida < detalle.cantidad_recibida:
            messages.error(
                request,
                f'No puedes reducir lo ya recibido de {detalle.producto.nombre} (actual: {detalle.cantidad_recibida}).',
            )
            return redirect('inventario:detalle_compra', pk=orden.pk)

        if cantidad_recibida > detalle.cantidad_solicitada:
            messages.error(
                request,
                f'La cantidad recibida de {detalle.producto.nombre} no puede superar la solicitada ({detalle.cantidad_solicitada}).',
            )
            return redirect('inventario:detalle_compra', pk=orden.pk)

        valores_recibidos[detalle.pk] = cantidad_recibida

    hubo_movimientos = False
    for detalle in detalles:
        nuevo_recibido = valores_recibidos[detalle.pk]
        adicional = nuevo_recibido - detalle.cantidad_recibida
        if adicional > 0:
            Movimiento.objects.create(
                producto=detalle.producto,
                tipo='entrada',
                cantidad=adicional,
                descripcion=f'Recepción de compra {orden.numero}',
                usuario=request.user.username,
            )
            detalle.cantidad_recibida = nuevo_recibido
            detalle.save(update_fields=['cantidad_recibida'])
            hubo_movimientos = True

    detalles_actualizados = list(orden.detalles.all())
    total_solicitado = sum(d.cantidad_solicitada for d in detalles_actualizados)
    total_recibido = sum(d.cantidad_recibida for d in detalles_actualizados)

    if total_recibido == 0:
        orden.estado = 'pendiente'
        orden.fecha_entrega_real = None
        orden.save(update_fields=['estado', 'fecha_entrega_real'])
        messages.info(request, f'Compra {orden.numero} sigue pendiente. Aún no registras recepción.')
        return redirect('inventario:detalle_compra', pk=orden.pk)

    if total_recibido == total_solicitado:
        orden.estado = 'completada'
        orden.fecha_entrega_real = timezone.now().date()
        orden.save(update_fields=['estado', 'fecha_entrega_real'])
        if hubo_movimientos:
            messages.success(request, f'Compra {orden.numero} recibida completamente. Stock actualizado.')
        else:
            messages.info(request, f'Compra {orden.numero} ya estaba completamente recibida.')
        return redirect('inventario:detalle_compra', pk=orden.pk)

    orden.estado = 'recibida_parcial'
    orden.fecha_entrega_real = timezone.now().date()
    orden.save(update_fields=['estado', 'fecha_entrega_real'])
    if hubo_movimientos:
        messages.success(request, f'Compra {orden.numero} actualizada con recepción parcial.')
    else:
        messages.info(request, f'Compra {orden.numero} sigue con recepción parcial sin cambios.')
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

    revertio_stock = False
    if venta.estado == 'completada':
        # Revertir stock solo si la venta ya habia descontado inventario.
        for detalle in venta.detalles.all():
            Movimiento.objects.create(
                producto=detalle.producto,
                tipo='entrada',
                cantidad=detalle.cantidad,
                descripcion=f'Cancelación de venta {venta.numero}',
                usuario=request.user.username,
            )
        revertio_stock = True

    venta.estado = 'cancelada'
    venta.save()
    if revertio_stock:
        messages.success(request, f'Venta {venta.numero} cancelada. Stock revertido.')
    else:
        messages.success(request, f'Pedido por encargo {venta.numero} cancelado.')
    return redirect('inventario:detalle_venta', pk=venta.pk)


# ============================================================================
# API ENDPOINTS (AJAX)
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_buscar_productos(request):
    q = (request.GET.get('q', '') or '').strip()

    productos = Producto.objects.filter(activo=True)

    proveedor_id = request.GET.get('proveedor_id', '')
    if proveedor_id and proveedor_id.isdigit():
        proveedor_id_int = int(proveedor_id)
        productos = productos.filter(
            ModelQ(proveedor_id=proveedor_id_int)
            | ModelQ(detallecompra__orden_compra__proveedor_id=proveedor_id_int)
        ).distinct()

        # Si no hay texto de búsqueda, devolver lista inicial de productos del proveedor.
        if not q:
            productos = productos.annotate(
                veces_comprado=Count(
                    'detallecompra',
                    filter=ModelQ(detallecompra__orden_compra__proveedor_id=proveedor_id_int),
                ),
                es_proveedor_principal=Case(
                    When(proveedor_id=proveedor_id_int, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            ).order_by('-es_proveedor_principal', '-veces_comprado', 'nombre')[:15]

            data = [
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'precio': str(p.precio),
                    'precio_compra': str(p.precio_compra) if p.precio_compra is not None else None,
                    'precio_venta': str(p.precio_venta) if p.precio_venta is not None else None,
                    'stock': p.stock,
                    'codigo_barras': p.codigo_barras or '',
                }
                for p in productos
            ]
            return JsonResponse(data, safe=False)

    if len(q) < 2:
        return JsonResponse([], safe=False)

    productos = productos.filter(
        Q(nombre__icontains=q) | Q(codigo_barras__icontains=q)
    )[:10]
    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'precio': str(p.precio),
            'precio_compra': str(p.precio_compra) if p.precio_compra is not None else None,
            'precio_venta': str(p.precio_venta) if p.precio_venta is not None else None,
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
        'precio_compra': str(producto.precio_compra) if producto.precio_compra is not None else None,
        'precio_venta': str(producto.precio_venta) if producto.precio_venta is not None else None,
        'stock': producto.stock,
        'codigo_barras': producto.codigo_barras or '',
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
@require_http_methods(["GET"])
def api_producto_precio_referencia(request, pk):
    """Retorna precio promedio y ultimo precio de compra para un producto/proveedor."""
    from decimal import Decimal, InvalidOperation

    producto = get_object_or_404(Producto, pk=pk, activo=True)
    proveedor_id = request.GET.get('proveedor_id')
    precio_actual_raw = request.GET.get('precio')

    detalles = DetalleCompra.objects.filter(producto=producto).select_related('orden_compra')
    if proveedor_id and str(proveedor_id).isdigit():
        detalles = detalles.filter(orden_compra__proveedor_id=int(proveedor_id))

    detalles = detalles.order_by('-fecha_creacion')
    recientes = list(detalles.values_list('precio_unitario', flat=True)[:5])

    if not recientes:
        return JsonResponse({'ok': True, 'has_reference': False})

    promedio = sum(recientes, Decimal('0')) / Decimal(len(recientes))
    ultimo = recientes[0]

    variacion = None
    if precio_actual_raw is not None:
        try:
            precio_actual = Decimal(str(precio_actual_raw))
            if promedio > 0:
                variacion = ((precio_actual - promedio) / promedio) * Decimal('100')
        except (InvalidOperation, ValueError, TypeError):
            variacion = None

    payload = {
        'ok': True,
        'has_reference': True,
        'precio_promedio': str(promedio.quantize(Decimal('0.01'))),
        'precio_ultimo': str(ultimo.quantize(Decimal('0.01'))),
        'muestras': len(recientes),
    }
    if variacion is not None:
        payload['variacion_pct'] = float(round(variacion, 2))

    return JsonResponse(payload)


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
@require_http_methods(["GET"])
def api_productos_similares(request):
    """Sugerencias de productos parecidos por nombre para evitar duplicados."""
    nombre = (request.GET.get('nombre', '') or '').strip()
    if len(nombre) < 3:
        return JsonResponse([], safe=False)

    filtros = Q(nombre__icontains=nombre)
    for token in [t for t in nombre.split() if len(t) >= 3]:
        filtros |= Q(nombre__icontains=token)

    productos = (
        Producto.objects.filter(activo=True)
        .filter(filtros)
        .exclude(nombre__iexact=nombre)
        .select_related('categoria')
        .order_by('nombre')[:5]
    )

    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'categoria': p.categoria.nombre if p.categoria else '',
            'precio': str(p.precio),
        }
        for p in productos
    ]
    return JsonResponse(data, safe=False)


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
    producto_inicial = None
    producto_inicial_id = request.GET.get('producto')
    if producto_inicial_id and producto_inicial_id.isdigit():
        producto = Producto.objects.select_related('proveedor').filter(
            pk=int(producto_inicial_id),
            activo=True,
        ).first()
        if producto:
            producto_inicial = {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': str(producto.precio_compra) if producto.precio_compra is not None else str(producto.precio),
                'precio_compra': str(producto.precio_compra) if producto.precio_compra is not None else None,
                'precio_venta': str(producto.precio_venta) if producto.precio_venta is not None else None,
                'stock': producto.stock,
                'codigo_barras': producto.codigo_barras or '',
                'proveedor_id': producto.proveedor_id or '',
                'proveedor_nombre': producto.proveedor.nombre if producto.proveedor_id else '',
            }

    return render(request, 'inventario/compra_rapida.html', {
        'proveedores': proveedores,
        'producto_inicial': producto_inicial,
    })


@login_required
@role_required(ROLE_ADMIN, ROLE_VENDEDOR)
@require_http_methods(["POST"])
def api_pos_venta(request):
    """AJAX endpoint for POS sale submission. Expects JSON body."""
    import json as json_mod
    from decimal import Decimal, InvalidOperation
    from django.db import transaction

    start_ts = time.monotonic()

    try:
        data = json_mod.loads(request.body)
    except (json_mod.JSONDecodeError, TypeError):
        logger.warning('pos_venta payload_invalido user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    items = data.get('items', [])
    if not items:
        logger.info('pos_venta sin_items user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'No hay productos en la venta'}, status=400)

    cliente = (data.get('cliente', '') or '').strip() or 'Cliente General'
    cliente_id = data.get('cliente_id')
    descuento_manual_raw = data.get('descuento_manual_porcentaje', 0)
    forma_pago = data.get('forma_pago', 'efectivo')
    notas = data.get('notas', '')
    registrar_como_pendiente = bool(data.get('registrar_como_pendiente'))

    try:
        descuento_manual_porcentaje = Decimal(str(descuento_manual_raw or 0))
    except (InvalidOperation, ValueError, TypeError):
        logger.warning('pos_venta descuento_invalido user=%s valor=%s', request.user.username, descuento_manual_raw)
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
                if not registrar_como_pendiente and producto.stock < cantidad:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Stock insuficiente para {producto.nombre} (disponible: {producto.stock})'
                    }, status=400)
                validated.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio': Decimal(str(item.get('precio', str(producto.precio_venta if producto.precio_venta is not None else producto.precio)))),
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
                estado='pendiente' if registrar_como_pendiente else 'completada',
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
                if not registrar_como_pendiente:
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

        duration_ms = int((time.monotonic() - start_ts) * 1000)
        logger.info(
            'pos_venta ok user=%s venta=%s items=%s total=%s dur_ms=%s',
            request.user.username,
            venta.numero,
            len(items),
            venta.total,
            duration_ms,
        )

        return JsonResponse({
            'ok': True,
            'venta_id': venta.pk,
            'numero': venta.numero,
            'estado': venta.estado,
            'subtotal': str(venta.subtotal),
            'descuento_total': str(venta.descuento_total),
            'total': str(venta.total),
        })

    except Producto.DoesNotExist:
        logger.warning('pos_venta producto_no_encontrado user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=400)
    except (ValueError, InvalidOperation, KeyError) as e:
        logger.warning('pos_venta error_datos user=%s detalle=%s', request.user.username, str(e))
        return JsonResponse({'ok': False, 'error': f'Error en datos: {str(e)}'}, status=400)
    except Exception as e:
        logger.exception('pos_venta error_interno user=%s detalle=%s', request.user.username, str(e))
        return JsonResponse({'ok': False, 'error': 'Error interno al procesar la venta'}, status=500)


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
@require_http_methods(["POST"])
def api_pos_compra(request):
    """AJAX endpoint for fast purchase submission. Creates order and receives immediately."""
    import json as json_mod
    from decimal import Decimal, InvalidOperation
    from django.db import transaction

    start_ts = time.monotonic()

    try:
        data = json_mod.loads(request.body)
    except (json_mod.JSONDecodeError, TypeError):
        logger.warning('pos_compra payload_invalido user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    items = data.get('items', [])
    if not items:
        logger.info('pos_compra sin_items user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'No hay productos en la compra'}, status=400)

    proveedor_id = data.get('proveedor_id')
    if not proveedor_id:
        logger.info('pos_compra sin_proveedor user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'Selecciona un proveedor'}, status=400)

    notas = data.get('notas', '')
    registrar_como_pendiente = bool(data.get('registrar_como_pendiente'))

    try:
        with transaction.atomic():
            proveedor = Proveedor.objects.get(pk=proveedor_id, activo=True)

            validated = []
            for item in items:
                producto = Producto.objects.get(pk=item['producto_id'], activo=True)
                cantidad = int(item['cantidad'])
                precio_ref_compra = producto.precio_compra if producto.precio_compra is not None else producto.precio
                precio = Decimal(str(item.get('precio', str(precio_ref_compra))))
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
                estado='pendiente' if registrar_como_pendiente else 'completada',
                notas=notas,
                usuario_creador=request.user.username,
                fecha_entrega_real=None if registrar_como_pendiente else timezone.now().date(),
            )
            orden.save()

            total = Decimal('0')
            for vi in validated:
                detalle = DetalleCompra(
                    orden_compra=orden,
                    producto=vi['producto'],
                    cantidad_solicitada=vi['cantidad'],
                    cantidad_recibida=0 if registrar_como_pendiente else vi['cantidad'],
                    precio_unitario=vi['precio'],
                )
                detalle.save()
                total += detalle.subtotal
                if not registrar_como_pendiente:
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

        duration_ms = int((time.monotonic() - start_ts) * 1000)
        logger.info(
            'pos_compra ok user=%s orden=%s proveedor_id=%s items=%s total=%s dur_ms=%s',
            request.user.username,
            orden.numero,
            proveedor_id,
            len(items),
            orden.total,
            duration_ms,
        )

        return JsonResponse({
            'ok': True,
            'orden_id': orden.pk,
            'numero': orden.numero,
            'estado': orden.estado,
            'total': str(orden.total),
        })

    except Proveedor.DoesNotExist:
        logger.warning('pos_compra proveedor_no_encontrado user=%s proveedor_id=%s', request.user.username, proveedor_id)
        return JsonResponse({'ok': False, 'error': 'Proveedor no encontrado'}, status=400)
    except Producto.DoesNotExist:
        logger.warning('pos_compra producto_no_encontrado user=%s', request.user.username)
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=400)
    except (ValueError, InvalidOperation, KeyError) as e:
        logger.warning('pos_compra error_datos user=%s detalle=%s', request.user.username, str(e))
        return JsonResponse({'ok': False, 'error': f'Error en datos: {str(e)}'}, status=400)
    except Exception as e:
        logger.exception('pos_compra error_interno user=%s detalle=%s', request.user.username, str(e))
        return JsonResponse({'ok': False, 'error': 'Error interno al procesar la compra'}, status=500)


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


@login_required
@role_required(ROLE_ADMIN, ROLE_BODEGUERO)
@require_http_methods(["POST"])
def api_ajuste_inventario(request):
    """AJAX endpoint para ajuste masivo de inventario por conteo físico."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Payload inválido'}, status=400)

    items = body.get('items', [])
    motivo = body.get('motivo', '').strip()

    if not items:
        return JsonResponse({'ok': False, 'error': 'No hay productos para ajustar'})
    if not motivo:
        return JsonResponse({'ok': False, 'error': 'El motivo del ajuste es obligatorio'})
    if len(items) > 100:
        return JsonResponse({'ok': False, 'error': 'Máximo 100 productos por ajuste'}, status=400)

    ajustados = []
    try:
        with transaction.atomic():
            for item in items:
                producto_id = int(item['producto_id'])
                delta = int(item['delta'])
                producto = Producto.objects.select_for_update().get(pk=producto_id)
                nuevo_stock = producto.stock + delta
                mov = Movimiento(
                    producto=producto,
                    tipo='ajuste',
                    cantidad=nuevo_stock,
                    descripcion=motivo,
                    usuario=request.user.username,
                )
                mov.save()
                producto.refresh_from_db(fields=['stock'])
                ajustados.append({'nombre': producto.nombre, 'nuevo_stock': producto.stock})
    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=404)
    except (KeyError, ValueError) as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    logger.info('ajuste_inventario user=%s items=%d', request.user.username, len(ajustados))
    return JsonResponse({'ok': True, 'ajustados': len(ajustados)})


# ---------------------------------------------------------------------------
# Gestión de usuarios (solo Administrador)
# ---------------------------------------------------------------------------

@login_required
@role_required(ROLE_ADMIN)
def lista_usuarios(request):
    from django.contrib.auth.models import User
    usuarios = User.objects.prefetch_related('groups').order_by('username')
    return render(request, 'inventario/lista_usuarios.html', {'usuarios': usuarios})


@login_required
@role_required(ROLE_ADMIN)
def crear_usuario(request):
    from django.contrib.auth.models import User, Group
    from .forms import CrearUsuarioForm
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
            )
            try:
                group = Group.objects.get(name=form.cleaned_data['rol'])
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
            messages.success(request, f'Usuario "{user.username}" creado correctamente.')
            return redirect('inventario:lista_usuarios')
    else:
        form = CrearUsuarioForm()
    return render(request, 'inventario/crear_usuario.html', {'form': form})


@login_required
@role_required(ROLE_ADMIN)
def editar_usuario(request, pk):
    from django.contrib.auth.models import User, Group
    from .forms import EditarUsuarioForm
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser:
        messages.error(request, 'No se puede editar un superusuario desde aquí.')
        return redirect('inventario:lista_usuarios')
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST)
        if form.is_valid():
            usuario.first_name = form.cleaned_data.get('first_name', '')
            usuario.last_name = form.cleaned_data.get('last_name', '')
            usuario.is_active = form.cleaned_data.get('is_active', True)
            new_pass = form.cleaned_data.get('password1')
            if new_pass:
                usuario.set_password(new_pass)
            usuario.save()
            usuario.groups.clear()
            try:
                group = Group.objects.get(name=form.cleaned_data['rol'])
                usuario.groups.add(group)
            except Group.DoesNotExist:
                pass
            messages.success(request, f'Usuario "{usuario.username}" actualizado.')
            return redirect('inventario:lista_usuarios')
    else:
        current_rol = usuario.groups.first().name if usuario.groups.exists() else 'Vendedor'
        form = EditarUsuarioForm(initial={
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'rol': current_rol,
            'is_active': usuario.is_active,
        })
    return render(request, 'inventario/editar_usuario.html', {'form': form, 'usuario': usuario})


# ---------------------------------------------------------------------------
# Gestión de roles (solo Administrador)
# ---------------------------------------------------------------------------

@login_required
@role_required(ROLE_ADMIN)
def lista_roles(request):
    from django.contrib.auth.models import Group
    from django.db.models import Count, Prefetch
    from django.contrib.auth.models import User
    roles = (
        Group.objects
        .prefetch_related(Prefetch('user_set', queryset=User.objects.order_by('username')))
        .annotate(num_usuarios=Count('user'))
        .order_by('name')
    )
    return render(request, 'inventario/lista_roles.html', {'roles': roles})


@login_required
@role_required(ROLE_ADMIN)
def crear_rol(request):
    from django.contrib.auth.models import Group
    from django.contrib.auth.models import Permission
    from .forms import RolForm, MODULOS
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            group = Group.objects.create(name=form.cleaned_data['nombre'])
            codenames = form.cleaned_data.get('modulos', [])
            perms = Permission.objects.filter(
                content_type__app_label='inventario',
                codename__in=codenames,
            )
            group.permissions.set(perms)
            messages.success(request, f'Rol "{group.name}" creado correctamente.')
            return redirect('inventario:lista_roles')
    else:
        form = RolForm()
    return render(request, 'inventario/crear_rol.html', {'form': form, 'modulos': MODULOS})


@login_required
@role_required(ROLE_ADMIN)
def editar_rol(request, pk):
    from django.contrib.auth.models import Group
    from django.contrib.auth.models import Permission
    from .forms import RolForm, MODULOS
    rol = get_object_or_404(Group, pk=pk)
    modulo_codenames = [m[0] for m in MODULOS]
    if request.method == 'POST':
        form = RolForm(request.POST, group_instance=rol)
        if form.is_valid():
            rol.name = form.cleaned_data['nombre']
            rol.save()
            # Actualizar solo los permisos de módulo (sin tocar los demás)
            codenames = form.cleaned_data.get('modulos', [])
            perms_modulo = Permission.objects.filter(
                content_type__app_label='inventario',
                codename__in=modulo_codenames,
            )
            perms_a_asignar = Permission.objects.filter(
                content_type__app_label='inventario',
                codename__in=codenames,
            )
            # Quitar los de módulo actuales y poner los seleccionados
            for p in perms_modulo:
                rol.permissions.remove(p)
            for p in perms_a_asignar:
                rol.permissions.add(p)
            messages.success(request, f'Rol "{rol.name}" actualizado.')
            return redirect('inventario:lista_roles')
    else:
        # Pre-marcar los módulos que ya tiene el rol
        current = list(
            rol.permissions.filter(
                content_type__app_label='inventario',
                codename__in=modulo_codenames,
            ).values_list('codename', flat=True)
        )
        form = RolForm(initial={'nombre': rol.name, 'modulos': current}, group_instance=rol)
    return render(request, 'inventario/editar_rol.html', {'form': form, 'rol': rol, 'modulos': MODULOS})


@login_required
@role_required(ROLE_ADMIN)
def eliminar_rol(request, pk):
    from django.contrib.auth.models import Group
    rol = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        nombre = rol.name
        rol.delete()
        messages.success(request, f'Rol "{nombre}" eliminado.')
        return redirect('inventario:lista_roles')
    return render(request, 'inventario/eliminar_rol.html', {'rol': rol})
