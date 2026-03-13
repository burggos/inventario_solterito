# Sistema de Gestión de Inventario - Tienda El Solterito

Esta aplicación Django proporciona un pequeño sistema de inventario para la tienda "El Solterito". La implementación usa **Django 4.x**, Tailwind CSS para el frontend y está diseñada para ser fácil de desplegar localmente o en un servidor.

---

## 📦 Requisitos previos

Antes de comenzar asegúrate de tener:

- **Python 3.8+** (usa `python3 --version`)
- **pip** (gestor de paquetes)
- **Git** (opcional, para clonar el repo)
- Un **navegador web** moderno

> 💡 Opcionalmente puedes instalar [Poetry](https://python-poetry.org/) o [pipenv] para gestionar el entorno.

---

## 🚀 Montar el proyecto en otra máquina

1. **Clona el repositorio** (o copia la carpeta) y entra en él:
   ```bash
   git clone https://github.com/burggos/inventario_solterito.git
   cd inventario_solterito
   ```

2. **Configura un entorno virtual** e instálalo:
   ```bash
   python3 -m venv venv             # crea el virtualenv
   source venv/bin/activate         # Linux/macOS
   # venv\Scripts\activate       # Windows

   pip install -r requirements.txt  # instala dependencias
   ```
   > Si no existe `requirements.txt`, instala manualmente `django pillow` y luego ejecuta `pip freeze > requirements.txt`.

3. **Variables de entorno y ajustes**
   - copia el archivo de ejemplo `settings.py` si requieres diferenciar entornos.
   - Opcional: define `DATABASE_URL` o edita `DATABASES` en `settings.py` para apuntar a PostgreSQL, MySQL, etc.
   - Asegúrate de ajustar `ALLOWED_HOSTS` cuando salgas de `DEBUG`.

4. **Aplica migraciones y crea usuario**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Carga datos iniciales (opcional)**
   Puedes ejecutar fixtures `python manage.py loaddata initial_data.json` si existe.

6. **Ejecuta el servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```
   Accede en `http://127.0.0.1:8000/`.

7. **Pruebas**
   ```bash
   python manage.py test
   ```
   Se usa SQLite automáticamente en modo test (ver `settings.py`).

---

## 🗂 Estructura del proyecto
```text
inventario_solterito/
├── manage.py              # script de administración
├── requirements.txt
├── db.sqlite3             # base de datos por defecto (cambia en producción)
├── solterito_inventario/  # configuración de Django
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── apps/                  # aplicaciones locales
│   └── inventario/        # app principal
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       ├── tests.py       # pruebas unitarias
│       └── ...
├── static/                # recursos estáticos (CSS, JS, imágenes)
├── media/                 # archivos subidos por usuarios
└── templates/             # plantillas HTML
    ├── base.html
    └── inventario/
```

---

## ⚙️ Uso básico

1. Inicia sesión en el admin (`/admin`) con el superusuario.
2. Crea algunas **Categorías** (e.g. Lácteos, Aseo).
3. Agrega **Productos** con nombre, precio, stock, etc.
4. Registra **Movimientos** (entradas/salidas) para llevar el historial.

La web principal ya muestra listas filtrables de productos y reportes.

---

## 🛠️ Problemas comunes

- **`ImproperlyConfigured: settings.DATABASES...`** – Revisa `DATABASES`.
- **`ALLOWED_HOSTS`/`DEBUG`** – cuando `DEBUG=False`, añade tus dominios a `ALLOWED_HOSTS`.
- **`No installed app with label 'inventario'`** – añade `sys.path.append(str(BASE_DIR / 'apps'))` y `'inventario'` a `INSTALLED_APPS`.
- **Imágenes no suben (/PIL)** – instala `Pillow` con `pip install pillow`.

---

## 🧩 Contribuir

1. Crea una rama para tu feature:
   ```bash
   git checkout -b feature/nombre
   ```
2. Trabaja y haz commits claros:
   ```bash
   git commit -am "Añade X"
   ```
3. Empuja y abre un pull request:
   ```bash
   git push origin feature/nombre
   ```

Revisa que todas las pruebas pasen y que el código siga el estilo del proyecto.

---

## 📄 Licencia
Proyecto con fines académicos para el Instituto Tecnológico San Agustín.

---

Si necesitas ayuda adicional, contáctame o abre un issue en el repositorio. ¡Gracias por usar o contribuir!  

