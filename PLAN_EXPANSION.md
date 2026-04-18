# Plan de Expansión: Sistema de Ventas y Compras

## Estado Actual
- ✅ CRUD de productos (crear, editar, eliminar, listar, detalle)
- ✅ Gestión de inventario con movimientos (entrada/salida/ajuste)
- ✅ Dashboard de reportes con gráficos Chart.js
- ✅ UI estandarizada (Tailwind CSS + Dark Mode)
- ✅ Modelos creados: Proveedor, OrdenCompra, DetalleCompra, Venta, DetalleVenta
- ✅ Formularios creados: ProveedorForm, OrdenCompraForm, DetalleCompraForm, VentaForm, DetalleVentaForm
- ✅ Admin registrado para todos los modelos
- ✅ Migraciones aplicadas

## Lo que FALTA implementar

### FASE 1: Vistas + URLs + Templates de Proveedores
1. `lista_proveedores` - Lista con búsqueda y filtros
2. `crear_proveedor` - Formulario de creación
3. `editar_proveedor` - Formulario de edición
4. `detalle_proveedor` - Detalle con historial de compras

### FASE 2: Vistas + URLs + Templates de Compras
1. `lista_compras` - Lista de órdenes con filtros por estado/proveedor/fecha
2. `crear_compra` - Formulario dinámico (AJAX para agregar ítems sin recargar)
3. `detalle_compra` - Detalle con lista de ítems
4. `recibir_compra` - Marcar como recibida y actualizar stock automáticamente

### FASE 3: Vistas + URLs + Templates de Ventas
1. `lista_ventas` - Lista con filtros por estado/fecha/forma de pago
2. `crear_venta` - Formulario dinámico (AJAX para agregar ítems)
3. `detalle_venta` - Detalle con lista de ítems
4. `cancelar_venta` - Cancelar y revertir stock

### FASE 4: API Endpoints (AJAX)
1. `api_buscar_productos` - Búsqueda por nombre/código para autocompletado
2. `api_producto_detalle` - Obtener precio y stock de un producto (JSON)

### FASE 5: Integración
1. Señales para actualizar stock al completar venta/recibir compra
2. Recálculo automático de totales en órdenes
3. Actualización del navbar con enlaces a Proveedores, Compras, Ventas
4. JavaScript dinámico en app.js para agregar ítems a compras/ventas

---

## Arquitectura de URLs

```
/proveedores/                    -> lista_proveedores
/proveedores/nuevo/              -> crear_proveedor
/proveedores/<id>/               -> detalle_proveedor
/proveedores/<id>/editar/        -> editar_proveedor

/compras/                        -> lista_compras
/compras/nueva/                  -> crear_compra
/compras/<id>/                   -> detalle_compra
/compras/<id>/recibir/           -> recibir_compra

/ventas/                         -> lista_ventas
/ventas/nueva/                   -> crear_venta
/ventas/<id>/                    -> detalle_venta
/ventas/<id>/cancelar/           -> cancelar_venta

/api/productos/buscar/           -> api_buscar_productos (JSON)
/api/productos/<id>/             -> api_producto_detalle (JSON)
```
