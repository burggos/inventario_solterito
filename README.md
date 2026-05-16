# Sistema de Gestión de Inventario - Tienda El Solterito

Aplicación web desarrollada con Django para la gestión integral de inventario, ventas y compras de la tienda **El Solterito**. Permite administrar productos, categorías, proveedores, movimientos de stock, órdenes de compra y ventas con punto de venta (POS).

---

## Características principales

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

## Tecnologías

- **Backend:** Django 3.2.12
- **Frontend:** Tailwind CSS (CDN) + CSS personalizado
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción en Render)
- **Servidor:** Gunicorn + WhiteNoise
- **Lenguaje:** Python 3.11.9

---

## Requisitos

- Python 3.8+
- pip
- Navegador moderno

---

## Instalación y ejecución

### Pasos comunes (todos los sistemas operativos)

1. Clonar el repositorio:

```bash
git clone https://github.com/burggos/inventario_solterito.git
cd inventario_solterito
```

### Linux / macOS

2. Crear y activar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Aplicar migraciones:

```bash
python manage.py migrate
```

Opcional, si quieres cargar datos de ejemplo:

```bash
python manage.py shell < seed_data.py
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

### Windows

2. Crear y activar un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
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

## Estructura del proyecto

```text
inventario_solterito/
├── manage.py
├── requirements.txt            # Dependencias consolidadas (desarrollo + producción)
├── render.yaml                 # Configuración de deployment en Render
├── .python-version             # Pin de Python (3.11.9)
├── .env.example                # Template de variables de entorno
├── db.sqlite3                  # Base de datos local generada tras migrar
├── solterito_inventario/       # Configuración del proyecto Django
│   ├── settings.py             # Soporta SQLite (dev) y PostgreSQL (prod)
│   ├── urls.py
│   ├── wsgi.py                 # WSGI para Gunicorn
│   └── asgi.py
├── apps/
│   └── inventario/             # Aplicación principal
│       ├── models.py           # Categoría, Producto, Movimiento, Proveedor, OrdenCompra, Venta
│       ├── views.py            # Vistas y endpoints API (AJAX)
│       ├── forms.py            # Formularios con validaciones de rol
│       ├── urls.py             # Rutas de la aplicación
│       ├── signals.py          # Señales Django
│       ├── permissions.py      # Decoradores de permisos por rol
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

## Modelos de datos

| Modelo | Descripción |
|--------|-------------|
| **Categoría** | Clasificación de productos (ej: Lácteos, Bebidas) |
| **Producto** | Artículos del inventario con precio, stock, código de barras e imagen |
| **Movimiento** | Registro de entradas, salidas y ajustes de stock |
| **Proveedor** | Datos de proveedores (contacto, RUC, términos de pago) |
| **OrdenCompra** | Órdenes de compra a proveedores con detalles por producto |
| **Venta** | Registro de ventas con forma de pago y detalles por producto |

---

## Rutas principales

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

## Deployment en Render

La aplicación está configurada para ejecutarse en [Render](https://render.com) con PostgreSQL gratuito.

**Configuración actual:**
- **Python:** 3.11.9 (definido en `.python-version`)
- **Base de datos:** PostgreSQL (libre)
- **Servidor:** Gunicorn con WhiteNoise para státicos
- **Migraciones:** Se ejecutan automáticamente en `preDeployCommand`

**Variables de entorno requeridas en Render:**
- `DJANGO_SECRET_KEY` (generado automáticamente)
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=.onrender.com`
- `DATABASE_URL` (vinculada automáticamente a la BD PostgreSQL)

---

## Pruebas

```bash
python manage.py test
```

---

## Notas

- El frontend usa Tailwind CSS desde CDN — no se requiere npm.
- `db.sqlite3` es un archivo local de desarrollo: se genera con `python manage.py migrate` y no debe versionarse.
- Si necesitas una base poblada para demos o pruebas manuales, puedes ejecutar `python manage.py shell < seed_data.py`.
- Las imágenes de productos se almacenan en `media/productos/`.
- **Dependencias consolidadas:** Un único `requirements.txt` cubre desarrollo y producción.
- **Entorno virtual:** Usa `.venv` localmente; `.gitignore` previene versionado accidental.
- **Státicos:** Se recompilan en el build de Render; no se versiona la carpeta `staticfiles/`.

---

## Licencia

Proyecto desarrollado con fines académicos para el Instituto Tecnológico San Agustín.
