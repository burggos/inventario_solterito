from django.contrib import admin
from .models import (
    Categoria,
    Producto,
    Movimiento,
    Proveedor,
    Cliente,
    OrdenCompra,
    DetalleCompra,
    Venta,
    DetalleVenta,
    HistorialDescuentoCliente,
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'necesita_reposicion', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'codigo_barras')
    list_editable = ('precio', 'activo')
    readonly_fields = ('stock', 'fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'imagen')
        }),
        ('Precio y stock', {
            'fields': ('precio', 'stock', 'stock_minimo', 'codigo_barras')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'descripcion')
    readonly_fields = ('fecha',)


# ============================================================================
# ADMIN PARA NUEVOS MODELOS DE VENTAS Y COMPRAS
# ============================================================================

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'ciudad', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'ciudad', 'fecha_creacion')
    search_fields = ('nombre', 'email', 'telefono', 'ruc')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'ruc', 'activo')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'contacto_principal')
        }),
        ('Dirección', {
            'fields': ('direccion', 'ciudad')
        }),
        ('Términos', {
            'fields': ('terminos_pago',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'documento', 'telefono', 'activo', 'descuento_fijo',
        'descuento_temporal', 'descuento_fidelidad', 'umbral_fidelidad'
    )
    list_filter = ('activo',)
    search_fields = ('nombre', 'documento', 'email', 'telefono')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1
    readonly_fields = ('subtotal',)
    fields = ('producto', 'cantidad_solicitada', 'cantidad_recibida', 'precio_unitario', 'subtotal')


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('numero', 'proveedor', 'fecha_creacion', 'estado', 'total')
    list_filter = ('estado', 'fecha_creacion', 'proveedor')
    search_fields = ('numero', 'proveedor__nombre')
    readonly_fields = ('numero', 'fecha_creacion', 'total')
    inlines = [DetalleCompraInline]
    fieldsets = (
        ('Información básica', {
            'fields': ('numero', 'proveedor', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_entrega_esperada', 'fecha_entrega_real')
        }),
        ('Financiero', {
            'fields': ('total',)
        }),
        ('Notas', {
            'fields': ('notas', 'usuario_creador')
        }),
    )


@admin.register(DetalleCompra)
class DetalleCompraAdmin(admin.ModelAdmin):
    list_display = ('orden_compra', 'producto', 'cantidad_solicitada', 'cantidad_recibida', 'precio_unitario', 'subtotal')
    list_filter = ('orden_compra__proveedor', 'fecha_creacion')
    search_fields = ('orden_compra__numero', 'producto__nombre')
    readonly_fields = ('subtotal', 'fecha_creacion')


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields = ('subtotal',)
    fields = ('producto', 'cantidad', 'precio_unitario', 'descuento_porcentaje', 'subtotal')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente_nombre', 'fecha_venta', 'subtotal', 'descuento_total', 'total', 'forma_pago', 'estado')
    list_filter = ('estado', 'forma_pago', 'fecha_venta')
    search_fields = ('numero', 'cliente_nombre')
    readonly_fields = ('numero', 'fecha_venta', 'subtotal', 'descuento_total', 'total')
    inlines = [DetalleVentaInline]
    fieldsets = (
        ('Información básica', {
            'fields': ('numero', 'cliente', 'cliente_nombre', 'estado')
        }),
        ('Fecha y pago', {
            'fields': ('fecha_venta', 'forma_pago')
        }),
        ('Financiero', {
            'fields': ('subtotal', 'descuento_total', 'total')
        }),
        ('Notas', {
            'fields': ('notas', 'usuario_vendedor')
        }),
    )


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'descuento_porcentaje', 'subtotal')
    list_filter = ('venta__fecha_venta', 'fecha_creacion')
    search_fields = ('venta__numero', 'producto__nombre')
    readonly_fields = ('subtotal', 'fecha_creacion')


@admin.register(HistorialDescuentoCliente)
class HistorialDescuentoClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'venta', 'porcentaje_aplicado', 'monto_descuento', 'tipo', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('cliente__nombre', 'venta__numero')
