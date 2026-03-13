from django.db import models
from django.utils import timezone

class Categoria(models.Model):
    """Categoría de productos (ej: Lácteos, Bebidas, Aseo)"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    """Producto del inventario"""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='productos'
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5, help_text="Cantidad mínima para alertar")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, unique=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"

    def clean(self):
        # validaciones de negocio simple
        from django.core.exceptions import ValidationError

        if self.precio is not None and self.precio < 0:
            raise ValidationError({'precio': 'El precio no puede ser negativo.'})
        if self.stock < 0:
            raise ValidationError({'stock': 'El stock no puede ser negativo.'})
        if self.stock_minimo < 0:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede ser negativo.'})
        if self.stock_minimo > self.stock:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede superar al stock actual.'})

        # código de barras único ya está en la base, pero aseguramos limpieza
        if self.codigo_barras:
            qs = Producto.objects.filter(codigo_barras=self.codigo_barras)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'codigo_barras': 'Este código de barras ya está en uso.'})

    @property
    def necesita_reposicion(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo

class Movimiento(models.Model):
    """Registro de entradas y salidas de productos"""
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(default=timezone.now)
    descripcion = models.TextField(blank=True, help_text="Motivo del movimiento")
    usuario = models.CharField(max_length=100, blank=True)  # Podrías relacionarlo con User después

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"