# Checklist Tecnico por Sprints

Fecha: 2026-05-09
Proyecto: inventario_solterito

## Objetivo
Reducir riesgos de produccion, mejorar consistencia de inventario y estabilizar mantenimiento.

## Sprint 1 (Critico) - Seguridad y Operacion
Duracion sugerida: 2 a 3 dias

- [x] Configurar entorno por variables (development/production) en settings.
- [x] Exigir DJANGO_SECRET_KEY en produccion.
- [x] Activar hardening de seguridad en produccion:
  - HSTS
  - SSL redirect
  - SESSION_COOKIE_SECURE
  - CSRF_COOKIE_SECURE
  - Referrer policy
  - SECURE_PROXY_SSL_HEADER (si hay proxy)
- [x] Crear archivo .env.example con variables obligatorias y ejemplos.
- [x] Definir pipeline de despliegue que falle si DJANGO_ENV=production y faltan variables criticas.
- [x] Ejecutar `python manage.py check --deploy` en CI.

Criterio de salida:
- No warnings criticos de seguridad en despliegue objetivo.

## Sprint 2 (Alto) - Integridad de Inventario
Duracion sugerida: 2 dias

- [x] Mover actualizacion de stock a logica atomica en Movimiento.save().
- [x] Evitar salidas sin stock suficiente (falla de validacion transaccional).
- [x] Retirar doble actualizacion via signal legacy.
- [x] Bloquear edicion manual de stock en admin para mantener trazabilidad.
- [ ] Agregar pruebas de concurrencia basica para salidas simultaneas.
- [ ] Definir politica explicita para `tipo='ajuste'` (si suma, resta o setea stock).

Criterio de salida:
- No existen movimientos de salida que no afecten stock.
- Todas las modificaciones de stock quedan trazables por movimientos.

## Sprint 3 (Medio) - Calidad de Dependencias y CI
Duracion sugerida: 1 a 2 dias

- [x] Limpiar requirements.txt a dependencias reales del proyecto.
- [x] Incluir beautifulsoup4 para suite completa de pruebas.
- [x] Alinear versions entre requirements.txt, requirements_clean.txt y requirements_deploy.txt.
- [x] Agregar `pip install -r requirements.txt && python manage.py test` al CI.
- [ ] Evaluar upgrade de Django 3.2 LTS a rama soportada (plan de migracion incremental).

Criterio de salida:
- Instalacion reproducible sin paquetes de SO.
- Test suite ejecutable en entorno limpio.

## Sprint 4 (Medio/Bajo) - Refactor y Observabilidad
Duracion sugerida: 2 dias

- [x] Eliminar imports duplicados detectados.
- [ ] Agregar logging estructurado en endpoints POS (venta/compra):
  - usuario
  - numero de transaccion
  - items
  - resultado
- [ ] Medir tiempos de respuesta en reportes y dashboard.
- [ ] Revisar indices de BD para filtros frecuentes (fecha, estado, proveedor, forma_pago).

Criterio de salida:
- Mejor trazabilidad de errores y mejor mantenibilidad de codigo.

## Riesgos Residuales
- Reportes con consultas pesadas pueden degradar rendimiento al crecer datos.
- Persisten decisiones de negocio por definir para movimientos de tipo ajuste.
- Django 3.2 requiere estrategia de upgrade para soporte futuro.

## Comandos de Verificacion Rapida
- `python manage.py test apps.inventario.tests`
- `python manage.py test`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py check --deploy`
