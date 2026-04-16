# Sistema de Gestión de Inventario - Tienda El Solterito

Proyecto Django para gestionar productos, categorías y movimientos de inventario en la tienda "El Solterito".

Esta versión del proyecto está limpia y lista para uso local. Se eliminó el entorno virtual, los módulos de Node y archivos de notas temporales que no forman parte del código fuente.

---

## 📌 Características principales

- Django como backend
- Interfaces con Tailwind CSS desde CDN
- Gestión de productos, categorías y movimientos
- Reportes básicos y lista de productos
- Login/Logout para acceso autenticado

---

## ✅ Requisitos

- Python 3.8+
- pip
- Navegador moderno

---

## 🚀 Instalación y ejecución

1. Crea y activa un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instala dependencias:

```bash
pip install -r requirements.txt
```

3. Aplica migraciones:

```bash
python manage.py migrate
```

4. Crea un superusuario (opcional):

```bash
python manage.py createsuperuser
```

5. Inicia el servidor:

```bash
python manage.py runserver
```

6. Abre el navegador en `http://127.0.0.1:8000/`

---

## 🧱 Estructura del proyecto

```text
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
│   ├── css/
│   ├── js/
│   └── ...
├── media/
└── templates/
    ├── base.html
    └── inventario/
```

---

## ℹ️ Notas

- El frontend utiliza Tailwind CSS cargado desde CDN, por lo que no se requiere instalación de npm para el uso actual.
- `db.sqlite3` se mantiene en el repositorio como base de datos local de desarrollo.
- Ya no existen carpetas `node_modules/` ni `venv/` en este repositorio limpio.

---

## 🧪 Pruebas

Ejecuta las pruebas de Django con:

```bash
python manage.py test
```

---

## 📄 Licencia

Proyecto con fines académicos.
