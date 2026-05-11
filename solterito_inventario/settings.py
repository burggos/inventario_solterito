import os
import sys
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_bool_env(name, default=False):
    return os.environ.get(name, str(default)).lower() in ('true', '1', 'yes', 'on')


def _get_list_env(name, default=''):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]

# Redirecciones de autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'inventario:dashboard'
LOGOUT_REDIRECT_URL = 'login'


sys.path.append(str(BASE_DIR / 'apps'))

# Entorno
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development').lower()
IS_PRODUCTION = DJANGO_ENV == 'production'

# SECRET_KEY
if IS_PRODUCTION and not os.environ.get('DJANGO_SECRET_KEY'):
    raise ImproperlyConfigured('Define DJANGO_SECRET_KEY en producción.')
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-insecure-secret-key-change-me')

# DEBUG
DEBUG = _get_bool_env('DJANGO_DEBUG', default=not IS_PRODUCTION)

default_hosts = '127.0.0.1,localhost,0.0.0.0,testserver,.pythonanywhere.com'
ALLOWED_HOSTS = _get_list_env('DJANGO_ALLOWED_HOSTS', default=default_hosts)

default_csrf_origins = 'https://*.pythonanywhere.com'
CSRF_TRUSTED_ORIGINS = _get_list_env('DJANGO_CSRF_TRUSTED_ORIGINS', default=default_csrf_origins)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventario',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'solterito_inventario.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'solterito_inventario.wsgi.application'

# Base de datos
database_url = os.environ.get('DATABASE_URL') or os.environ.get('DJANGO_DATABASE_URL')
DB_ENGINE = os.environ.get('DJANGO_DB_ENGINE', 'sqlite').lower()

if database_url:
    DATABASES = {
        'default': dj_database_url.parse(database_url, conn_max_age=600, ssl_require=IS_PRODUCTION)
    }
elif DB_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DJANGO_DB_NAME', ''),
            'USER': os.environ.get('DJANGO_DB_USER', ''),
            'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', ''),
            'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
            'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
        }
    }
else:
    sqlite_path = Path(os.environ.get('DJANGO_SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')))
    try:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # En algunos builders (ej. Render), /var/data no es escribible durante build.
        # El disco se monta en runtime, por lo que no debemos romper la carga de settings.
        pass
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Seguridad de despliegue (solo producción)
if IS_PRODUCTION:
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _get_bool_env('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
    SECURE_HSTS_PRELOAD = _get_bool_env('DJANGO_SECURE_HSTS_PRELOAD', default=True)
    SECURE_SSL_REDIRECT = _get_bool_env('DJANGO_SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = _get_bool_env('DJANGO_SESSION_COOKIE_SECURE', default=True)
    CSRF_COOKIE_SECURE = _get_bool_env('DJANGO_CSRF_COOKIE_SECURE', default=True)
    SECURE_REFERRER_POLICY = os.environ.get('DJANGO_SECURE_REFERRER_POLICY', 'same-origin')

    # Necesario cuando hay proxy (ej. PythonAnywhere / reverse proxy)
    if _get_bool_env('DJANGO_USE_X_FORWARDED_PROTO', default=True):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')