# Plan de Expansión: Sistema de Ventas y Compras

## Base del Proyecto

- [x] CRUD de productos (crear, editar, eliminar, listar, detalle)
- [x] Gestión de inventario con movimientos (entrada/salida/ajuste)
- [x] Dashboard con KPIs, gráficos Chart.js y resumen de actividad
- [x] UI estandarizada (Tailwind CSS + Dark Mode + CSS personalizado)
- [x] Autenticación (Login/Logout)
- [x] Reportes de inventario
- [x] Migraciones aplicadas

---

## FASE 0: Modelos y Configuración

- [x] Modelo `Proveedor` (nombre, email, teléfono, dirección, RUC, términos de pago)
- [x] Modelo `OrdenCompra` (proveedor, estado, total, número auto-generado)
- [x] Modelo `DetalleCompra` (orden, producto, cantidad solicitada/recibida, precio, subtotal)
- [x] Modelo `Venta` (cliente, forma de pago, estado, total, número auto-generado)
- [x] Modelo `DetalleVenta` (venta, producto, cantidad, precio, descuento, subtotal)
- [x] Formularios: `ProveedorForm`, `OrdenCompraForm`, `DetalleCompraForm`, `VentaForm`, `DetalleVentaForm`
- [x] Admin registrado para todos los modelos (Proveedor, OrdenCompra, DetalleCompra, Venta, DetalleVenta)
- [x] Migraciones generadas y aplicadas

---

## FASE 1: Proveedores — Vistas + URLs + Templates

- [x] `lista_proveedores` — Lista con búsqueda y filtros
- [x] `crear_proveedor` — Formulario de creación
- [x] `editar_proveedor` — Formulario de edición
- [x] `detalle_proveedor` — Detalle con historial de compras
- [x] Template `lista_proveedores.html`
- [x] Template `crear_proveedor.html`
- [x] Template `editar_proveedor.html`
- [x] Template `detalle_proveedor.html`
- [x] URLs registradas (`/proveedores/`, `/proveedores/nuevo/`, `/proveedores/<id>/`, `/proveedores/<id>/editar/`)

---

## FASE 2: Compras — Vistas + URLs + Templates

- [x] `lista_compras` — Lista de órdenes con filtros por estado/proveedor/fecha
- [x] `crear_compra` — Redirige al POS de compra rápida
- [x] `detalle_compra` — Detalle con lista de ítems
- [x] `recibir_compra` — Marcar como recibida y actualizar stock automáticamente
- [x] Template `lista_compras.html`
- [x] Template `crear_compra.html`
- [x] Template `detalle_compra.html`
- [x] Template `compra_rapida.html` (interfaz POS)
- [x] URLs registradas (`/compras/`, `/compras/nueva/`, `/compras/<id>/`, `/compras/<id>/recibir/`)

---

## FASE 3: Ventas — Vistas + URLs + Templates

- [x] `lista_ventas` — Lista con filtros por estado/fecha/forma de pago
- [x] `crear_venta` — Redirige al POS de venta rápida
- [x] `detalle_venta` — Detalle con lista de ítems
- [x] `cancelar_venta` — Cancelar y revertir stock
- [x] Template `lista_ventas.html`
- [x] Template `crear_venta.html`
- [x] Template `detalle_venta.html`
- [x] Template `venta_rapida.html` (interfaz POS)
- [x] URLs registradas (`/ventas/`, `/ventas/nueva/`, `/ventas/<id>/`, `/ventas/<id>/cancelar/`)

---

## FASE 4: API Endpoints (AJAX)

- [x] `api_buscar_productos` — Búsqueda por nombre/código para autocompletado (JSON)
- [x] `api_producto_detalle` — Obtener precio y stock de un producto (JSON)
- [x] `api_pos_venta` — Procesar venta desde POS (JSON, transaccional)
- [x] `api_pos_compra` — Procesar compra desde POS (JSON, transaccional)
- [x] URLs registradas (`/api/productos/buscar/`, `/api/productos/<id>/`, `/api/pos/venta/`, `/api/pos/compra/`)

---

## FASE 5: Integración

- [x] Señal `actualizar_stock` en movimientos (entrada/salida con F() expressions atómicas)
- [x] Creación automática de movimientos al completar venta POS
- [x] Creación automática de movimientos al completar compra POS
- [x] Recálculo automático de totales en ventas y órdenes de compra
- [x] Navbar actualizado con enlaces a Proveedores, Compras, Ventas
- [x] JavaScript dinámico con `fetch()` en templates POS (venta_rapida, compra_rapida, crear_movimiento)
- [ ] JavaScript centralizado en `app.js` (actualmente inline en templates)

---

## Posibles Mejoras Futuras

- [ ] Extraer JavaScript inline de templates POS a `static/js/app.js`
- [ ] Agregar paginación a listas de compras y ventas
- [ ] Dashboard: gráficos de ventas por período y forma de pago
- [ ] Exportación de reportes a PDF/Excel
- [ ] Gestión de usuarios con roles y permisos
- [ ] Notificaciones de stock bajo por email
- [ ] Soporte multi-sucursal
- [ ] Código de barras: escaneo desde cámara en POS
- [ ] Historial de precios por producto
