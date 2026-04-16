# Plan de Expansión: Sistema de Ventas y Compras

## Estado Actual
- ✅ CRUD básico de productos
- ✅ Gestión de inventario simple
- ✅ Historial de movimientos genéricos
- ✅ UI estandarizada (Tailwind + Dark Mode)

## Expansión Propuesta: Sistema Dinámico de Ventas y Compras

### FASE 1: Nuevos Modelos (Base de Datos)

#### 1. Modelo Proveedor
```
- nombre
- email
- telefono
- direccion
- ciudad
- ruc (número de identificación)
- contacto_principal
- términos_de_pago
- activo
- fecha_creacion
```

#### 2. Modelo Orden de Compra
```
- numero (auto-incremental)
- proveedor (FK)
- fecha_creacion
- fecha_entrega_esperada
- estado (Pendiente, Completada, Cancelada)
- notas
- total
- usuario_creador (FK User)
```

#### 3. Modelo Detalle de Compra
```
- orden_compra (FK)
- producto (FK)
- cantidad_solicitada
- cantidad_recibida
- precio_unitario
- subtotal
```

#### 4. Modelo Venta
```
- numero (auto-incremental)
- fecha_venta
- cliente_nombre (o FK a Cliente si queremos)
- estado (Completada, Pendiente, Cancelada)
- total
- forma_pago (Efectivo, Tarjeta, Crédito)
- notas
```

#### 5. Modelo Detalle de Venta
```
- venta (FK)
- producto (FK)
- cantidad
- precio_unitario
- descuento_porcentaje
- subtotal
```

### FASE 2: Vistas (Backend)

#### Nuevas Vistas:
1. **Gestión de Proveedores**
   - Lista de proveedores
   - Crear/Editar proveedor
   - Historial de compras por proveedor

2. **Registrar Compra**
   - Interfaz dinámica para agregar items
   - Auto-completado de productos
   - Cálculo en tiempo real
   - Recibir compra (actualizar stock)

3. **Registrar Venta**
   - Interfaz dinámica similar
   - Cálculo de cambio
   - Impresión de recibo
   - Historial de ventas

### FASE 3: Mejoras de Interfaz (Frontend)

#### AJAX Dinámico:
1. **Agregar items sin recargar**
2. **Auto-completado**:
   - Buscar productos por nombre/código
   - Sugerir precios
3. **Cálculos en tiempo real**:
   - Actualizaciones automáticas de totales
   - Validación de stock disponible
4. **Búsqueda avanzada**:
   - Filtros de fecha
   - Filtros de estado
   - Búsqueda por número de transacción

### FASE 4: Reportes Mejorados

1. **Reporte de Ventas**:
   - Por período
   - Por cliente
   - Por forma de pago
   - Gráfico de tendencias

2. **Reporte de Compras**:
   - Por proveedor
   - Por período
   - Órdenes pendientes
   - Entregas retrasadas

3. **Gestión de Inventario**:
   - Productos con bajo stock
   - Rotación de productos
   - Costo de inventario

### FASE 5: Funcionalidades Avanzadas

1. **API REST** (para posibles apps móviles)
2. **Sincronización con banco** (para pagos)
3. **Automatización de emails**
4. **Backup automático**

---

## Prioridad de Implementación

### ✅ PRIMERO (Crítico):
1. Modelo de Proveedor
2. Modelo de Orden de Compra
3. Vista para registrar compras (simple)
4. Actualización automática de stock

### SEGUNDO (Importante):
1. Modelo de Venta
2. Vista para registrar ventas
3. Interfaz AJAX para dinámico
4. Reportes básicos

### TERCERO (Mejoras):
1. Auto-completado avanzado
2. Validaciones complejas
3. Reportes gráficos
4. Funciones avanzadas

---

## Cambios Requeridos

### Base de Datos:
- 5 nuevas migraciones

### Backend (models.py):
- 5 nuevos modelos
- ~300 líneas

### Views (views.py):
- 15 nuevas vistas
- ~500 líneas

### Templates:
- 10 nuevas páginas
- AJAX en algunos templates

### URL Configuration:
- 20 nuevos paths

### JS (app.js):
- AJAX dinámico
- Auto-completado
- Validaciones cliente
- ~400 líneas

### CSS:
- Estilos para nuevas funciones
- Soporte dark mode

---

## Tiempo Estimado:
- **FASE 1**: 1-2 horas
- **FASE 2**: 3-4 horas
- **FASE 3**: 2-3 horas
- **FASE 4**: 1-2 horas
- **FASE 5**: 2-3 horas

**Total**: 9-14 horas de trabajo

---

## ¿Por dónde empezamos?

Recomendación: Comenzar con **FASE 1 + FASE 2 (parcial)** para tener una base funcional.
