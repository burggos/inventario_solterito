# Plan de Expansion: El Solterito (Actualizado)

Fecha actualizacion: 2026-05-09

## Resumen Ejecutivo
Este plan integra roles y permisos, reportes dinamicos, descuentos por cliente y generacion de PDF sobre el proyecto actual, manteniendo arquitectura Django MVT y compatibilidad con despliegue modular.

---

## FASE A: Roles y Control de Acceso

### Requerimientos
- [x] Definir roles: Administrador, Vendedor, Bodeguero.
- [x] Crear decoradores de rol para vistas existentes.
- [x] Crear mixin para CBVs nuevas con validacion de grupos.
- [x] Implementar grupos de Django y semilla automatica de permisos.
- [x] Mostrar opciones de interfaz segun rol autenticado.

### Implementado
- [x] Archivo de permisos: `apps/inventario/permissions.py`.
- [x] Template tags para roles: `apps/inventario/templatetags/role_tags.py`.
- [x] Comando: `python manage.py seed_roles`.
- [x] Restricciones por rol en productos, compras, ventas, movimientos y reportes.
- [x] Sidebar dinamico por rol en `templates/base.html`.

---

## FASE B: Clientes y Descuentos

### Requerimientos
- [x] Modelo de cliente con descuento fijo, temporal y fidelidad.
- [x] Aplicar descuento automaticamente durante la venta.
- [x] Mostrar subtotal, descuento aplicado y total final.
- [x] Guardar historial de descuentos usados.
- [x] Evitar totales negativos.

### Implementado
- [x] Modelo `Cliente` con reglas de descuento.
- [x] Modelo `HistorialDescuentoCliente`.
- [x] Campos `subtotal` y `descuento_total` en `Venta`.
- [x] Endpoint `api_cliente_descuento`.
- [x] Integracion POS en `venta_rapida.html` (cliente + descuento en vivo).
- [x] Persistencia de historial de descuento en `api_pos_venta`.

---

## FASE C: Reportes Dinamicos (HTMX + Chart.js)

### Estado
- [x] Modulo retirado del producto por decision funcional.
- [x] Eliminadas rutas, vistas y templates asociados.

---

## FASE D: PDFs Profesionales

### Requerimientos
- [x] PDF de factura de venta.
- [x] PDF de comprobante de compra.
- [x] Ver/descargar/imprimir en navegador.
- [x] Plantilla limpia con datos completos.

### Implementado
- [x] Motor PDF via `reportlab`.
- [x] Vistas:
  - `venta_pdf`
  - `compra_pdf`
- [x] Templates PDF:
  - `templates/inventario/pdf/venta_factura.html`
  - `templates/inventario/pdf/compra_comprobante.html`
- [x] Botones de acceso en detalle de venta y compra.

---

## FASE E: Requisitos Tecnicos

- [x] Arquitectura modular mantenida.
- [x] Patron MVT mantenido.
- [x] Nuevas funcionalidades en CBV donde aplica (clientes).
- [x] Validaciones backend de descuentos y stock.
- [x] UI moderna en Tailwind y componentes existentes.
- [x] Mensajes amigables de exito/error.
- [x] Uso de `select_related` en consultas criticas.
- [x] Compatible con PostgreSQL a nivel ORM (sin SQL acoplado a SQLite).

---

## FASE F: Resultado Integrable

### Entregables completos incluidos
- [x] Modelos nuevos y extendidos.
- [x] Vistas nuevas + integracion en vistas existentes.
- [x] URLs registradas.
- [x] Formularios de clientes y ventas actualizados.
- [x] Templates de clientes, reportes dinamicos y PDF.
- [x] Lógica de permisos y grupos.
- [x] JavaScript de POS con descuentos automáticos.
- [x] Migraciones pendientes de generar/aplicar en entorno destino.

---

## Comandos de ejecucion

1. Instalar dependencias

```bash
pip install -r requirements.txt
```

2. Crear migraciones y aplicarlas

```bash
python manage.py makemigrations
python manage.py migrate
```

3. Sembrar roles y permisos

```bash
python manage.py seed_roles
```

4. Ejecutar pruebas

```bash
python manage.py test
```

---

## Pendientes recomendados (siguiente iteracion)

- [ ] Factura PDF con logo embebido y formato corporativo final.
- [ ] Exportacion de reportes dinamicos a PDF/Excel.
- [ ] Panel de gestion de usuarios por rol desde UI (actualmente via Admin + grupos).
- [ ] Pruebas de concurrencia para salidas simultaneas de inventario.
