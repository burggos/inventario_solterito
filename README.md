# Sistema de Gestión de Inventario - Tienda El Solterito

Aplicación web desarrollada con Django para la gestión integral de inventario, ventas y compras de la tienda **El Solterito**. Permite administrar productos, categorías, proveedores, movimientos de stock, órdenes de compra y ventas con punto de venta (POS).

---

## 📌 Características principales

- **Dashboard** con resumen de productos, stock bajo, ventas y compras recientes
- **Gestión de productos** con categorías, código de barras, imágenes y alertas de stock mínimo
- **Movimientos de inventario** (entradas, salidas, ajustes) con historial completo
- **Sistema de ventas** con múltiples formas de pago (efectivo, tarjeta, transferencia, crédito, cheque)
- **Órdenes de compra** a proveedores con seguimiento de estado (pendiente, completada, cancelada, recibida parcial)
- **Punto de venta rápido (POS)** para ventas y compras con búsqueda AJAX de productos
- **Gestión de proveedores** con datos de contacto, RUC y términos de pago
- **Reportes** básicos de inventario
- **Autenticación** con Login/Logout

---

## 🛠️ Tecnologías

- **Backend:** Django 3.2
- **Frontend:** Tailwind CSS (CDN) + CSS personalizado
- **Base de datos:** SQLite (desarrollo)
- **Lenguaje:** Python 3.8+

---

## ✅ Requisitos

- Python 3.8+
- pip
- Navegador moderno

---

## 🚀 Instalación y ejecución

1. Clonar el repositorio:

```bash
git clone https://github.com/burggos/inventario_solterito.git
cd inventario_solterito
```

2. Crear y activar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Aplicar migraciones:

```bash
python manage.py migrate
```

5. Crear un superusuario:

```bash
python manage.py createsuperuser
```

6. Iniciar el servidor:

```bash
python manage.py runserver
```

7. Abrir en el navegador: `http://127.0.0.1:8000/`

---

## 🧱 Estructura del proyecto

```text
inventario_solterito/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── solterito_inventario/       # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── inventario/             # Aplicación principal
│       ├── models.py           # Categoría, Producto, Movimiento, Proveedor, OrdenCompra, Venta
│       ├── views.py            # Vistas y endpoints API (AJAX)
│       ├── forms.py            # Formularios
│       ├── urls.py             # Rutas de la aplicación
│       ├── signals.py          # Señales Django
│       ├── admin.py            # Configuración del admin
│       ├── tests.py            # Pruebas unitarias
│       └── migrations/
├── static/
│   ├── css/estilo.css          # Estilos personalizados
│   └── js/app.js               # JavaScript del frontend
├── media/
│   └── productos/              # Imágenes de productos
└── templates/
    ├── base.html               # Template base
    ├── includes/               # Componentes reutilizables
    ├── inventario/             # Templates de la app (dashboard, CRUD, POS, reportes)
    └── registration/           # Login/Logout
```

---

## 📋 Modelos de datos

| Modelo | Descripción |
|--------|-------------|
| **Categoría** | Clasificación de productos (ej: Lácteos, Bebidas) |
| **Producto** | Artículos del inventario con precio, stock, código de barras e imagen |
| **Movimiento** | Registro de entradas, salidas y ajustes de stock |
| **Proveedor** | Datos de proveedores (contacto, RUC, términos de pago) |
| **OrdenCompra** | Órdenes de compra a proveedores con detalles por producto |
| **Venta** | Registro de ventas con forma de pago y detalles por producto |

---

## 🌐 Rutas principales

| Ruta | Función |
|------|---------|
| `/` | Dashboard |
| `/productos/` | Lista de productos |
| `/movimientos/` | Historial de movimientos |
| `/proveedores/` | Gestión de proveedores |
| `/compras/` | Órdenes de compra |
| `/ventas/` | Registro de ventas |
| `/pos/venta/` | Punto de venta rápido |
| `/pos/compra/` | Compra rápida |
| `/reportes/` | Reportes de inventario |

---

## 🧪 Pruebas

```bash
python manage.py test
```

---

## ℹ️ Notas

- El frontend usa Tailwind CSS desde CDN — no se requiere npm.
- `db.sqlite3` se incluye como base de datos de desarrollo.
- Las imágenes de productos se almacenan en `media/productos/`.

---

## 📄 Licencia

Proyecto desarrollado con fines académicos para el Instituto Tecnológico San Agustín.
