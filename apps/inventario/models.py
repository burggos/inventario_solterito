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


# ============================================================================
# NUEVOS MODELOS PARA SISTEMA DE VENTAS Y COMPRAS
# ============================================================================

class Proveedor(models.Model):
    """Información de proveedores para compras"""
    nombre = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    ruc = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="RUT o número de identificación")
    contacto_principal = models.CharField(max_length=100, blank=True)
    terminos_pago = models.TextField(blank=True, help_text="Términos y condiciones de pago")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class OrdenCompra(models.Model):
    """Orden de compra a proveedores"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('recibida_parcial', 'Recibida Parcial'),
    ]
    
    numero = models.CharField(max_length=50, unique=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='ordenes_compra')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega_esperada = models.DateField(null=True, blank=True)
    fecha_entrega_real = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    usuario_creador = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"OC-{self.numero} ({self.proveedor.nombre})"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils.timezone import now
            timestamp = now().strftime('%Y%m%d%H%M%S')
            self.numero = f"OC-{self.proveedor.id}-{timestamp}"
        super().save(*args, **kwargs)


class DetalleCompra(models.Model):
    """Detalle de items en una orden de compra"""
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compra"
        unique_together = ['orden_compra', 'producto']

    def __str__(self):
        return f"{self.orden_compra.numero} - {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad_solicitada * self.precio_unitario
        super().save(*args, **kwargs)


class Venta(models.Model):
    """Registro de ventas"""
    ESTADO_CHOICES = [
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]
    
    PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('credito', 'Crédito'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
    ]
    
    numero = models.CharField(max_length=50, unique=True, blank=True)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    cliente_nombre = models.CharField(max_length=200, default="Cliente General")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completada')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    forma_pago = models.CharField(max_length=20, choices=PAGO_CHOICES, default='efectivo')
    notas = models.TextField(blank=True)
    usuario_vendedor = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']

    def __str__(self):
        return f"V-{self.numero} - {self.cliente_nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils.timezone import now
            timestamp = now().strftime('%Y%m%d%H%M%S')
            self.numero = f"V-{timestamp}"
        super().save(*args, **kwargs)


class DetalleVenta(models.Model):
    """Detalle de items en una venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"

    def __str__(self):
        return f"{self.venta.numero} - {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        descuento = (self.cantidad * self.precio_unitario) * (self.descuento_porcentaje / 100)
        self.subtotal = (self.cantidad * self.precio_unitario) - descuento
        super().save(*args, **kwargs)
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"