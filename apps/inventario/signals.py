"""
Las señales de stock se retiraron.

Ahora el stock se actualiza en Movimiento.save() dentro de una transacción atómica,
evitando dobles actualizaciones y movimientos inconsistentes.
"""