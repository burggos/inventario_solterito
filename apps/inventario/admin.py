from django.contrib import admin
from .models import Categoria, Producto, Movimiento

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'necesita_reposicion', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'codigo_barras')
    list_editable = ('precio', 'stock', 'activo')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
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
