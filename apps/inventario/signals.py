from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from .models import Movimiento, Producto

@receiver(post_save, sender=Movimiento)
def actualizar_stock(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto cuando se crea un nuevo movimiento.
    Usa F() expressions para operaciones atómicas en la base de datos.
    """
    if created:
        if instance.tipo == 'entrada':
            Producto.objects.filter(pk=instance.producto_id).update(
                stock=F('stock') + instance.cantidad
            )
        elif instance.tipo == 'salida':
            Producto.objects.filter(
                pk=instance.producto_id, stock__gte=instance.cantidad
            ).update(stock=F('stock') - instance.cantidad)