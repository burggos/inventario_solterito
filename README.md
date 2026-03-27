# Sistema de Gestión de Inventario - Tienda El Solterito

Aplicación web desarrollada con Django para la gestión de inventario de la tienda **El Solterito**. Permite administrar productos, categorías y movimientos de stock de forma sencilla.

El proyecto utiliza:

* Django 4.x (backend)
* Tailwind CSS (frontend)
* SQLite por defecto (configurable a otros motores)

Está diseñado para ejecutarse tanto en entornos locales como en servidores.

---

## Requisitos

Antes de iniciar, asegúrese de contar con:

* Python 3.8 o superior
* pip (gestor de paquetes de Python)
* Git (opcional)
* Navegador web moderno

Opcional:

* Herramientas de gestión de entornos como Poetry o Pipenv

---

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/burggos/inventario_solterito.git
cd inventario_solterito
```

### 2. Crear y activar entorno virtual

```bash
python3 -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Si el archivo `requirements.txt` no existe:

```bash
pip install django pillow
pip freeze > requirements.txt
```

---

### 4. Configuración del proyecto

* Revise el archivo `settings.py`
* Configure la base de datos si no usará SQLite
* Ajuste `ALLOWED_HOSTS` en entornos de producción
* Configure variables de entorno si es necesario

---

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

---

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

---

### 7. (Opcional) Cargar datos iniciales

```bash
python manage.py loaddata initial_data.json
```

---

### 8. Ejecutar el servidor

```bash
python manage.py runserver
```

Acceda desde:

```
http://127.0.0.1:8000/
```

---

### 9. Ejecutar pruebas

```bash
python manage.py test
```

---

## Estructura del proyecto

```
inventario_solterito/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── solterito_inventario/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── apps/
│   └── inventario/
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       ├── tests.py
│       └── ...
├── static/
├── media/
└── templates/
```

Descripción general:

* `manage.py`: herramienta de administración de Django
* `apps/inventario`: lógica principal del sistema
* `static/`: archivos estáticos (CSS, JS, imágenes)
* `media/`: archivos subidos por usuarios
* `templates/`: vistas HTML

---

## Uso del sistema

1. Acceda al panel administrativo en `/admin`
2. Inicie sesión con el superusuario
3. Cree categorías de productos
4. Registre productos con su información (precio, stock, etc.)
5. Gestione movimientos de inventario (entradas y salidas)

El sistema incluye listados y reportes básicos de productos.

---

## Problemas comunes

**Error de base de datos**

* Verifique la configuración en `DATABASES` dentro de `settings.py`

**Problemas con ALLOWED_HOSTS**

* Asegúrese de definir los dominios cuando `DEBUG=False`

**Aplicación no reconocida**

* Confirme que `'inventario'` esté en `INSTALLED_APPS`

**Problemas con imágenes**

* Instale Pillow:

```bash
pip install pillow
```

---

## Contribución

1. Crear una nueva rama:

```bash
git checkout -b feature/nueva-funcionalidad
```

2. Realizar cambios y commits:

```bash
git commit -m "Descripción clara del cambio"
```

3. Subir cambios:

```bash
git push origin feature/nueva-funcionalidad
```

4. Abrir un Pull Request

---

## Licencia

Proyecto desarrollado con fines académicos para el Instituto Tecnológico San Agustín.

---

## Soporte

Para reportar errores o solicitar mejoras, utilice la sección de *issues* del repositorio.
