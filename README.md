# Sistema de Gestión de Inventario - Tienda El Solterito

Proyecto de desarrollo de una página web para la gestión de inventario de la tienda "El Solterito" en Montería.  
Desarrollado con Django + Tailwind CSS.

## Requisitos previos

Asegúrate de tener instalado en tu sistema:

- **Python** 3.8 o superior
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)
- **Navegador web** moderno

##  Instalación y puesta en marcha

Sigue estos pasos en orden para levantar el proyecto en tu máquina local.

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd solterito_inventario
```
Si no usas Git, simplemente descomprime la carpeta del proyecto y accede a ella desde la terminal.

### 2. Crear y activar un entorno virtual (recomendado)
   
En Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```
En Windows:

```bash
python -m venv venv
venv\Scripts\activate
```
3. Instalar dependencias
El archivo requirements.txt contiene todas las librerías necesarias.

```bash
pip install -r requirements.txt
```
Si no tienes requirements.txt, puedes generarlo después de instalar las dependencias manualmente:

```bash
pip install django pillow
pip freeze > requirements.txt
```
4. Configurar la base de datos
Aplica las migraciones para crear las tablas en la base de datos (SQLite por defecto).

```bash
python manage.py migrate
```
5. Crear un superusuario (para acceder al panel admin)
```bash
python manage.py createsuperuser
```
Sigue las instrucciones: ingresa nombre de usuario, correo y contraseña.
Ejemplo: admin, admin@example.com, admin123 (no uses contraseñas débiles en producción).

6. Ejecutar el servidor de desarrollo
```bash
python manage.py runserver
```
Verás un mensaje como:

```text
Starting development server at http://127.0.0.1:8000/
```
7. Acceder a la aplicación
Panel de administración: http://127.0.0.1:8000/admin
Inicia sesión con el superusuario que creaste.

Páginas públicas: (cuando las desarrollemos) estarán en la raíz, por ahora solo el admin está disponible.

Estructura del proyecto
```text
solterito_inventario/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── solterito_inventario/       # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── apps/                        # Aplicaciones Django
│   └── inventario/               # App de inventario
│       ├── models.py
│       ├── admin.py
│       ├── views.py
│       └── ...
├── static/                       # Archivos estáticos (CSS, JS, imágenes)
├── media/                         # Archivos subidos por usuarios (fotos de productos)
└── templates/                     # Plantillas HTML
    ├── base.html
    └── inventario/
```
🛠️ Uso básico (admin)
Ve al panel de administración (/admin).

Agrega Categorías (ej: "Lácteos", "Bebidas").

Agrega Productos con nombre, precio, stock, imagen, etc.

Registra Movimientos (entradas/salidas) para llevar el historial.

Posibles errores y soluciones
Error: django.core.exceptions.ImproperlyConfigured: settings.DATABASES is improperly configured.
Causa: Falta la configuración de base de datos en settings.py.

Solución: Verifica que DATABASES esté definido como en el archivo de ejemplo.

Error: CommandError: You must set settings.ALLOWED_HOSTS if DEBUG is False.
Causa: Tienes DEBUG = False pero no has definido ALLOWED_HOSTS.

Solución: En desarrollo, cambia DEBUG = True en settings.py.

Error: No installed app with label 'inventario'
Causa: La app no está registrada en INSTALLED_APPS o no se encuentra en el PYTHONPATH.

Solución: Verifica que en settings.py tengas:

python
import sys
sys.path.append(str(BASE_DIR / 'apps'))
INSTALLED_APPS = [..., 'inventario']
Error al subir imágenes: ModuleNotFoundError: No module named 'PIL'
Causa: Falta instalar Pillow.

Solución: Ejecuta pip install pillow.

Contribuir
Si deseas contribuir al proyecto:

Crea una rama con tu feature: git checkout -b feature/nueva-funcionalidad

Haz commit de tus cambios: git commit -m 'Agrega nueva funcionalidad'

Sube la rama: git push origin feature/nueva-funcionalidad

Abre un Pull Request.

📄 Licencia
Este proyecto es con fines académicos para el Instituto Tecnológico San Agustín.

