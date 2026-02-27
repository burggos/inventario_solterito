from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Movimiento, Producto

@receiver(post_save, sender=Movimiento)
def actualizar_stock(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto cuando se crea un nuevo movimiento.
    Si el movimiento es de entrada, suma; si es salida, resta.
    """
    if created:
        producto = instance.producto
        if instance.tipo == 'entrada':
            producto.stock += instance.cantidad
        elif instance.tipo == 'salida':
            # Validar que haya suficiente stock (aunque podemos hacerlo en el formulario/vista)
            if producto.stock >= instance.cantidad:
                producto.stock -= instance.cantidad
            else:
                # Podríamos lanzar un error o manejar de otra forma
                # Por ahora, simplemente no actualizamos y quizás registrar algo
                # Pero es mejor evitar llegar aquí con validaciones previas.
                pass
        elif instance.tipo == 'ajuste':
            # Para ajuste, podríamos establecer el stock directamente,
            # pero eso requeriría lógica adicional. Por ahora, ignoramos.
            pass
        producto.save()