# Plan Integral de Mejora UX/UI, Flujo de Trabajo y Casos de Uso

Fecha: 2026-05-16  
Proyecto: El Solterito - Sistema de Inventario

## 1. Objetivo

Definir mejoras concretas para que la aplicación sea más rápida, clara y segura en el uso diario de tres perfiles operativos:

- Administrador
- Vendedor
- Bodeguero

Este documento aterriza recomendaciones en escenarios reales de trabajo, incluyendo casos normales, errores frecuentes y eventos excepcionales.

## 2. Alcance y enfoque

Este análisis cubre:

- UX de navegación, formularios, tablas y POS
- UI visual y consistencia por patrón
- Flujo operativo por rol y por jornada laboral
- Manejo de errores, confirmaciones y retroalimentación al usuario
- Priorización de mejoras en fases

No cubre:

- Reescritura completa del frontend
- Cambios de arquitectura mayor fuera de Django templates

## 3. Mapa de usuarios y objetivos diarios

## 3.1 Administrador

Objetivos diarios:

- Supervisar KPIs de inventario, ventas y compras
- Configurar catálogo y categorías
- Ajustar permisos y resolver incidencias
- Revisar reportes y tendencias

Dolores frecuentes:

- Mucha información sin jerarquía de urgencia
- Falta de workflows guiados para tareas complejas
- Dificultad para auditar cambios rápidos

## 3.2 Vendedor

Objetivos diarios:

- Registrar ventas rápido y sin fricción
- Consultar producto y stock disponible
- Aplicar descuentos válidos sin errores
- Cerrar transacciones sin bloquear la caja

Dolores frecuentes:

- Interrupciones por validaciones tardías
- Pérdida de tiempo al corregir líneas del carrito
- Falta de confirmaciones contextualizadas en errores críticos

## 3.3 Bodeguero

Objetivos diarios:

- Reponer inventario mediante compras
- Ver movimientos y stock crítico
- Crear productos y asociarlos a proveedor
- Asegurar consistencia del inventario físico

Dolores frecuentes:

- Dudas sobre qué producto compra cada proveedor
- Riesgo de registrar compras con datos incompletos
- Falta de atajos para tareas repetitivas de reposición

## 4. Jornada diaria y eventos reales

## 4.1 Inicio de turno

Evento:

- Usuario ingresa al sistema, revisa estado y empieza operación.

Riesgos:

- El dashboard no prioriza alertas accionables por rol.
- El usuario debe navegar varias vistas para detectar pendientes.

Mejora propuesta:

- Dashboard por rol con bloque "Qué hacer ahora".
- Tarjetas de acción inmediata con CTA único:
- Vendedor: "Iniciar venta" y "Productos sin stock para vender".
- Bodeguero: "Reponer stock crítico" y "Compras pendientes".
- Administrador: "Revisar alertas" y "Ver desempeño del día".

## 4.2 Venta rápida en hora pico

Evento:

- Vendedor registra múltiples ventas seguidas con teclado/escáner.

Riesgos:

- Errores de digitación en cantidad o selección accidental.
- Falta de protección frente a doble click o recarga de página.
- Mensajes de error poco accionables en operaciones concurrentes.

Mejora propuesta:

- Estado visual de "procesando" robusto y anti doble envío.
- Guardado temporal del carrito en localStorage con expiración corta.
- Mensajes de error accionables:
- "Stock cambió de X a Y. Ajustar cantidad ahora".
- Resaltado automático del ítem conflictivo.
- Sonido breve opcional para confirmación de venta y error crítico.

## 4.3 Compra rápida y reposición

Evento:

- Bodeguero selecciona proveedor, busca productos, ajusta precio/cantidad y confirma.

Riesgos:

- Compra de producto no habitual del proveedor.
- Precio atípico sin alerta.
- Omisión de notas operativas relevantes.

Mejora propuesta:

- Lista inicial de proveedor con badge "principal" y "frecuencia de compra".
- Alerta de variación de precio contra últimas compras del mismo producto.
- Campo de nota sugerida por plantilla:
- "Motivo compra", "urgencia", "fecha recepción física".

## 4.4 Alta de producto nuevo

Evento:

- Bodeguero/Admin crea producto con stock inicial y proveedor.

Riesgos:

- Falta de proveedor principal o categoría incorrecta.
- Duplicado por nombre similar.
- Precio mal digitado por falta de formato.

Mejora propuesta:

- Validación temprana de posibles duplicados por similitud de nombre.
- Máscaras y formato monetario en vivo.
- Wizard de 2 pasos:
- Paso 1: Identidad del producto.
- Paso 2: Configuración comercial y stock inicial.
- Confirmación final con resumen antes de guardar.

## 4.5 Ajustes y movimientos manuales

Evento:

- Administrador/Bodeguero registra entrada/salida/ajuste por contingencias.

Riesgos:

- Ajustes sin motivo suficiente para auditoría.
- Selección equivocada de tipo de movimiento.

Mejora propuesta:

- Campos de motivo con categorías predefinidas:
- "Merma", "Daño", "Conteo físico", "Corrección".
- Requerir evidencia mínima opcional (nota más detallada) para ajustes mayores.
- Vista previa de impacto en stock antes de confirmar.

## 4.6 Cierre de turno

Evento:

- Responsable revisa resumen diario y pendientes.

Riesgos:

- No existe checklist de cierre.
- Falta de trazabilidad rápida de anomalías.

Mejora propuesta:

- Módulo "Cierre de turno" con checklist:
- Ventas completadas vs canceladas.
- Movimientos manuales del día.
- Productos críticos sin reposición.
- Exportación rápida a PDF de resumen operativo.

## 5. Casos de uso clave con mejoras concretas

## 5.1 CU-01 Vender producto con stock suficiente

Flujo ideal:

- Buscar producto
- Agregar al carrito
- Seleccionar cliente y pago
- Confirmar

Mejoras:

- Autoselección del primer resultado al escanear código exacto.
- Confirmación visual compacta sin modal bloqueante.
- Reenfoque automático al buscador tras guardar.

## 5.2 CU-02 Intento de venta sin stock

Flujo actual:

- Rechaza con mensaje de error.

Mejoras:

- Mostrar opción directa "Ver sustitutos" o "Notificar reposición".
- Mostrar última fecha de reposición para contexto.

## 5.3 CU-03 Compra por proveedor con lista inicial

Flujo actual:

- Selecciona proveedor y carga productos relacionados.

Mejoras:

- Segmentos rápidos:
- "Más comprados"
- "Últimos comprados"
- "Sin compra en 30 días"
- Filtro por rango de precio dentro del proveedor.

## 5.4 CU-04 Crear producto y registrar compra automática

Flujo actual:

- Se crea producto y se registra orden + movimiento automáticamente si hay stock inicial.

Mejoras:

- Mensaje final con resumen enlazable:
- ID producto
- Nro orden generada
- Stock resultante
- Atajo: "Crear otro producto con mismo proveedor/categoría".

## 5.5 CU-05 Consultar detalle de producto

Flujo actual:

- Muestra información y últimos movimientos.

Mejoras:

- Línea de tiempo visual de movimientos con colores y motivos.
- Mini gráfico de tendencia de stock (7/30 días).
- Acciones contextuales por rol claramente separadas.

## 6. Matriz de permisos UX recomendada

Objetivo:

- Evitar confusión por acciones visibles que luego fallan por permisos.

Reglas UX:

- Si una acción no está permitida, no mostrar botón.
- Si se muestra modo lectura, indicar claramente "Solo consulta".

Acciones recomendadas por rol:

- Vendedor:
- Ver productos y detalle.
- Crear ventas rápidas.
- Consultar historial de ventas.

- Bodeguero:
- Ver/crear/editar productos.
- Crear compras rápidas.
- Registrar movimientos permitidos.
- Gestionar proveedores.

- Administrador:
- Todo lo anterior.
- Reportes y cancelaciones sensibles.
- Ajustes avanzados de inventario.

## 7. Heurísticas UX/UI transversales

## 7.1 Claridad visual

- Aumentar jerarquía en encabezados con subtítulos orientados a tarea.
- Reducir ruido visual en tablas de alta densidad.
- Unificar iconografía por intención: ver, editar, mover, eliminar.

## 7.2 Retroalimentación inmediata

- Todo guardado debe devolver confirmación visible y contextual.
- Todo error debe incluir causa y acción sugerida.
- Evitar mensajes genéricos sin próximo paso.

## 7.3 Prevención de errores

- Validaciones en cliente antes de enviar.
- Confirmación para acciones irreversibles.
- Formatos guiados para dinero, porcentajes y cantidades.

## 7.4 Eficiencia operativa

- Atajos de teclado consistentes en todos los módulos operativos.
- Foco inteligente en inputs principales.
- Acciones repetitivas con "repetir última configuración".

## 7.5 Accesibilidad

- Contraste WCAG AA en botones críticos y badges de estado.
- Navegación completa por teclado.
- Etiquetas y mensajes compatibles con lectores de pantalla.

## 8. Mejoras específicas de UI por pantalla

## 8.1 Dashboard

- Agregar panel "Alertas accionables" al inicio.
- Mostrar tarjetas distintas por rol.
- Añadir estado operativo de hoy:
- Ventas completadas
- Compras completadas
- Alertas críticas abiertas

## 8.2 Lista de productos

- Guardar filtros en URL y en sesión del usuario.
- Columna de estado con tooltip explicativo.
- Acciones en fila con orden fijo y tooltips más descriptivos.

## 8.3 Detalle de producto

- Encabezado con resumen rápido:
- Stock actual
- Stock mínimo
- Proveedor principal
- Último movimiento
- Bloque "riesgo" si stock está crítico.

## 8.4 POS venta

- Modo "escáner continuo" opcional.
- Bloque de totales siempre visible al hacer scroll.
- Confirmación optimizada para caja rápida en pantallas pequeñas.

## 8.5 POS compra

- Indicadores de historial del proveedor por producto.
- Alerta de precios fuera de rango histórico.
- Plantillas de nota por tipo de compra.

## 9. Eventos excepcionales y respuestas UX

## 9.1 Error de red o timeout

Respuesta deseada:

- Banner persistente: "No se pudo completar. Reintentar".
- Mantener formulario/carrito intacto.
- Botón "reintentar" sin recargar toda la pantalla.

## 9.2 Conflicto de concurrencia (stock cambió)

Respuesta deseada:

- Mostrar producto afectado y stock actual.
- Sugerir ajustes automáticos de cantidad.
- Permitir confirmar parcial cuando aplique.

## 9.3 Sesión expirada

Respuesta deseada:

- Aviso previo de expiración inminente.
- Reautenticación ligera y retorno al flujo anterior.

## 9.4 Errores de validación de negocio

Respuesta deseada:

- Mensajes por campo y resumen superior.
- Foco automático en primer error.
- Preservación total de datos ingresados.

## 10. Plan de implementación por fases

## Fase 1 (Quick Wins, 1-2 semanas)

- Mensajes de error/éxito más accionables.
- Mejoras de foco y atajos en POS.
- Confirmaciones robustas anti doble envío.
- Dashboard con panel de alertas por rol.
- Mejoras de tooltips y etiquetas en acciones.

Impacto esperado:

- Menos errores operativos.
- Menor tiempo por transacción.

## Fase 2 (Flujo y productividad, 2-4 semanas)

- Wizard de alta de producto.
- Persistencia de filtros y preferencias de vista.
- Línea de tiempo en detalle de producto.
- Segmentación avanzada en compra por proveedor.

Impacto esperado:

- Mayor consistencia de datos.
- Reducción de retrabajo en bodega.

## Fase 3 (Analítica operativa y robustez, 4-6 semanas)

- Cierre de turno guiado.
- Alertas inteligentes de anomalías.
- Métricas de eficiencia por rol.
- Manejo avanzado de contingencias de red/concurrencia.

Impacto esperado:

- Trazabilidad sólida.
- Mejor toma de decisiones gerenciales.

## 11. KPIs para medir éxito

- Tiempo promedio de venta POS
- Tiempo promedio de compra POS
- Porcentaje de operaciones con error
- Reintentos por transacción
- Productos en estado crítico sin acción > 48h
- Tasa de uso de atajos de teclado
- Satisfacción de usuario interno (encuesta corta semanal)

Meta recomendada a 60 días:

- Reducir errores operativos en 30%
- Reducir tiempo de venta en 20%
- Reducir tiempo de compra en 20%

## 12. Checklist funcional de aceptación UX

- Cada rol ve solo acciones permitidas y útiles
- Ningún formulario pierde datos ante error
- Cada error sugiere acción correctiva
- Todas las operaciones críticas previenen doble envío
- POS es utilizable solo con teclado
- Flujos críticos completables en móvil y desktop
- Dashboard prioriza pendientes accionables del día

## 13. Recomendación final

La app ya tiene una base funcional sólida para operación real. El siguiente salto de calidad no depende de agregar más módulos, sino de pulir la experiencia operativa en los momentos de presión: ventas en hora pico, reposición urgente y resolución de errores sin frenar la tienda.

La prioridad debe centrarse en:

- claridad por rol
- velocidad de ejecución
- prevención de errores
- feedback accionable en tiempo real

Con este enfoque, la plataforma se vuelve más simple para el usuario diario y más confiable para el negocio.

## 14. Catálogo de eventos del día a día y respuesta UX esperada

Este catálogo sirve como guía de diseño para que cada evento de operación tenga respuesta clara en interfaz y flujo.

## 14.1 Eventos de autenticación y acceso

- Login exitoso:
- Mostrar saludo por rol y acceso directo a tarea principal.

- Credenciales inválidas:
- Mensaje claro sin lenguaje técnico y foco en campo usuario.

- Usuario sin permisos:
- Pantalla 403 amigable con ruta permitida sugerida.

- Sesión por expirar:
- Aviso no intrusivo con opción "extender sesión".

## 14.2 Eventos de navegación diaria

- Cambio entre módulos frecuentes:
- Recordar último filtro por módulo.

- Volver atrás desde detalle:
- Conservar paginación y filtros previos.

- Menú lateral en móvil:
- Cierre automático tras navegación y confirmación visual.

## 14.3 Eventos sobre productos

- Búsqueda sin resultados:
- Mostrar sugerencias de corrección y categorías relacionadas.

- Producto en stock crítico:
- Badge + CTA inmediato para reposición.

- Producto sin proveedor principal:
- Alerta suave en detalle y sugerencia de completar dato.

- Intento de eliminar producto con historial:
- Mensaje explicando alternativa: desactivar en vez de eliminar.

- Duplicidad por código de barras:
- Mensaje de conflicto con enlace al producto existente.

## 14.4 Eventos sobre inventario y movimientos

- Registro de entrada:
- Confirmar nuevo stock resultante en toast.

- Registro de salida:
- Mostrar advertencia si queda por debajo de mínimo.

- Ajuste manual:
- Requerir motivo y mostrar vista previa de impacto.

- Salida con stock insuficiente:
- Bloquear acción con opción de ajuste de cantidad sugerida.

- Alto volumen de movimientos en poco tiempo:
- Filtros rápidos "Última hora", "Hoy", "Ayer".

## 14.5 Eventos de ventas POS

- Escaneo exitoso:
- Confirmación visual y sonora opcional.

- Producto repetido en carrito:
- Incremento automático de cantidad y resaltado de fila.

- Descuento superior al permitido:
- Ajuste automático a límite y aviso explicativo.

- Cambio de stock durante la venta:
- Revalidar línea afectada sin perder el resto del carrito.

- Confirmación de venta:
- Mostrar resumen compacto con número de venta y total.

- Cancelación de venta:
- Confirmación explícita por impacto en stock e historial.

## 14.6 Eventos de compras POS

- Proveedor no seleccionado:
- Bloquear búsqueda con mensaje contextual.

- Lista inicial cargada por proveedor:
- Ordenar por afinidad histórica y proveedor principal.

- Precio de compra fuera de rango:
- Alerta de variación con referencia histórica.

- Confirmación de compra:
- Mostrar número de orden y total, con acceso a detalle.

- Compra interrumpida por error de red:
- Mantener carrito y permitir reintento inmediato.

## 14.7 Eventos de reportes y supervisión

- Carga lenta de reportes:
- Skeleton UI y mensaje de progreso.

- Filtros sin datos:
- Mostrar insight "sin datos" y sugerencia de rango alterno.

- Detección de anomalías:
- Bloque de alertas con explicación y prioridad.

## 14.8 Eventos administrativos

- Creación de cliente/proveedor:
- Mensaje de éxito con opción "crear otro".

- Edición de datos sensibles:
- Registrar auditoría visible para admin.

- Operación irreversible:
- Doble confirmación para acciones críticas.

## 14.9 Eventos de usabilidad transversal

- Error en formulario:
- Foco en primer campo inválido + resumen superior.

- Operación larga:
- Estado de carga consistente con bloqueo parcial.

- Operación exitosa:
- Confirmación breve, clara y no bloqueante.

- Atajo de teclado ejecutado:
- Feedback discreto que confirme la acción.

## 14.10 Eventos de contingencia técnica

- API responde 500:
- Mensaje amable + logging de incidente + opción reintentar.

- Timeout de API:
- Mantener estado local y permitir recuperación sin recarga.

- Datos parcialmente guardados:
- Mostrar estado y pasos de reconciliación.

- Caída temporal de conexión:
- Banner persistente y cola de reintentos en operaciones no críticas.

## 15. Auditoría de cumplimiento actual (estado real de la app)

Escala usada:

- Cumple: implementado y usable en operación.
- Parcial: existe base funcional, pero faltan piezas clave UX/UI.
- No cumple: no existe o no está operativo según lo definido en este plan.

Resultado general estimado:

- Cumple: 11 de 34
- Parcial: 13 de 34
- No cumple: 10 de 34
- Cobertura global aproximada: 45%

## 15.1 Diagnóstico por bloques

## A. Roles y permisos UX

- Mostrar solo acciones permitidas por rol: Cumple
- Modo lectura claro para vistas restringidas: Parcial
- Mensajes de 403 amigables con rutas sugeridas: No cumple

## B. POS venta

- Flujo base de venta rápida: Cumple
- Validación de stock en backend transaccional: Cumple
- Prevención fuerte de doble envío: Parcial
- Persistencia temporal de carrito (recuperación): No cumple
- Manejo UX de conflicto por concurrencia con sugerencia automática: Parcial
- Feedback sonoro opcional / confirmación operativa: No cumple

## C. POS compra

- Flujo base de compra rápida: Cumple
- Lista inicial por proveedor: Cumple
- Priorización visual por historial/frecuencia: Parcial
- Alerta de precio fuera de rango histórico: No cumple
- Reintento robusto sin perder carrito ante falla de red: Parcial

## D. Productos e inventario

- Crear producto con proveedor principal: Cumple
- Registro automático de compra y movimiento al crear con stock inicial: Cumple
- Wizard de alta de producto (2 pasos): No cumple
- Detección temprana de duplicados por similitud de nombre: No cumple
- Línea de tiempo visual de movimientos en detalle: No cumple
- Tendencia de stock 7/30 días en detalle: No cumple

## E. Dashboard y supervisión

- Dashboard operativo base con métricas: Cumple
- Priorización por rol ("qué hacer ahora"): Parcial
- Panel de alertas accionables por urgencia: Parcial
- Cierre de turno guiado: No cumple

## F. Errores, confirmaciones y resiliencia UX

- Mensajes de éxito/error visibles (toast): Cumple
- Mensajes accionables por causa exacta: Parcial
- Preservación de datos en formularios con error: Parcial
- Banner persistente ante desconexión / timeout: No cumple
- Reautenticación ligera al expirar sesión y retorno de contexto: No cumple

## G. Eficiencia operativa

- Atajos de teclado en POS: Cumple
- Foco inteligente en campos clave: Parcial
- Repetir última configuración (acciones repetitivas): No cumple

## H. Accesibilidad y consistencia UI

- Consistencia visual general (cards/buttons/tables): Cumple
- Navegación completa por teclado (todas las pantallas): Parcial
- Validación formal WCAG AA (contraste y foco): No cumple
- Soporte claro para lectores de pantalla: Parcial

## 15.2 Hallazgos críticos (prioridad alta)

- No existe estrategia sólida de recuperación ante fallo de red en POS.
- Falta protección UX completa contra doble envío en operaciones críticas.
- No hay flujo de cierre de turno para control operativo diario.
- No existe capa de alertas inteligentes de riesgo/urgencia por rol.

## 15.3 Backlog priorizado (implementación recomendada)

## Prioridad P0 (inmediato: 1-2 semanas)

- Fortalecer anti doble envío en POS venta/compra (botón, lock, idempotencia UI).
- Banner y reintento para fallos de red en POS sin perder carrito.
- Mensajes de error accionables por item conflictivo (stock/precio/cantidad).
- Panel inicial en dashboard con "Qué hacer ahora" por rol.

## Prioridad P1 (2-4 semanas)

- Persistencia temporal de carrito en POS (localStorage con expiración).
- Wizard de alta de producto (2 pasos + resumen de confirmación).
- Vista de detalle de producto con línea de tiempo de movimientos.
- Alerta de variación de precio en compra rápida.

## Prioridad P2 (4-6 semanas)

- Cierre de turno guiado con checklist y exportable.
- Métricas operativas por rol y alertas de anomalías.
- Mejora de accesibilidad integral (teclado, foco, contraste, ARIA).

## 15.4 Definición de "listo" por mejora UX

Una mejora se considera lista solo si cumple todos estos criterios:

- Tiene comportamiento consistente en desktop y móvil.
- Maneja errores de red y validación sin pérdida de datos.
- Tiene feedback claro (estado, éxito, error, próximo paso).
- Respeta permisos por rol sin mostrar acciones inútiles.
- Incluye validación funcional con usuario de negocio (admin, vendedor o bodeguero).

## 16. Siguiente paso recomendado

Para pasar de diagnóstico a ejecución, el siguiente entregable debe ser:

- "Plan técnico por sprint" con tareas concretas por archivo (views, templates, JS, estilos), criterio de aceptación y pruebas por cada mejora P0/P1.

Con ese plan, la evolución UX/UI deja de ser conceptual y se vuelve una hoja de ruta implementable.

## 17. Plan técnico por sprint (ejecutable)

Convenciones:

- Estimación en puntos: 1 (bajo), 2 (medio), 3 (alto).
- Cada sprint debe cerrar con demo por rol y evidencia de pruebas.

## Sprint 0 - Preparación y baseline (2-3 días)

Objetivo:

- Preparar base técnica para medir mejoras UX sin romper flujos actuales.

Tareas por archivo:

- apps/inventario/views.py
- Agregar logging estructurado en endpoints POS para errores y tiempos.

- static/js/app.js
- Crear utilidades comunes de UX: lock de botón, manejo de fetch con timeout, banner de red.

- templates/base.html
- Incluir contenedor global para banner de conectividad.

Pruebas:

- python manage.py check
- Flujo manual: simular red lenta y validar banner.

Criterio de aceptación:

- Existe capa común para errores de red y bloqueo de acciones críticas.

## Sprint 1 - P0 operativo POS y dashboard (1-2 semanas)

Objetivo:

- Reducir errores transaccionales y mejorar reacción del usuario en operación diaria.

Tareas por archivo:

- templates/inventario/venta_rapida.html
- Implementar lock anti doble envío al confirmar.
- Integrar reintento controlado cuando falle la API.
- Mostrar mensajes por item conflictivo (stock o validación).

- templates/inventario/compra_rapida.html
- Implementar lock anti doble envío al confirmar.
- Integrar reintento sin perder carrito.
- Mostrar mensaje de error específico por producto.

- apps/inventario/views.py
- Estandarizar payload de error POS con código y detalle por item.
- Agregar campo sugerencia en errores de concurrencia.

- templates/inventario/dashboard.html
- Agregar bloque "Qué hacer ahora" por rol.
- Agregar alertas accionables del día con CTA directo.

Pruebas:

- python manage.py check
- Prueba manual vendedor: dos clics rápidos en confirmar venta, no duplica.
- Prueba manual bodeguero: caída de red durante compra, carrito permanece.
- Prueba manual por rol: dashboard muestra CTAs correctos.

Criterio de aceptación:

- No hay doble envío en POS.
- Errores POS siempre devuelven acción sugerida legible.
- Dashboard presenta prioridades distintas por rol.

## Sprint 2 - P1 productividad y calidad de dato (2-4 semanas)

Objetivo:

- Subir velocidad operativa y reducir retrabajo en alta y reposición.

Tareas por archivo:

- templates/inventario/venta_rapida.html
- Persistencia temporal de carrito con expiración.

- templates/inventario/compra_rapida.html
- Persistencia temporal de carrito con expiración.
- Indicador visual de variación de precio respecto a histórico.

- apps/inventario/views.py
- Endpoint de referencia de precio histórico por producto y proveedor.
- Endpoint para detectar similitud de nombre en alta de producto.

- templates/inventario/crear_producto.html
- Convertir formulario en wizard de 2 pasos.
- Vista previa final antes de confirmar.

- apps/inventario/forms.py
- Validación adicional para duplicidad por similitud y mensaje sugerido.

Pruebas:

- python manage.py check
- Test manual: cerrar y reabrir pestaña en POS, recuperar carrito vigente.
- Test manual: alta producto con nombre similar, mostrar advertencia.

Criterio de aceptación:

- El usuario puede recuperar carrito sin pérdida tras recarga.
- Alta de producto tiene flujo guiado con confirmación de resumen.

## Sprint 3 - P1 visibilidad de inventario (2 semanas)

Objetivo:

- Mejorar decisiones de reposición con contexto visual en producto.

Tareas por archivo:

- templates/inventario/detalle_producto.html
- Agregar timeline de movimientos con codificación visual por tipo.
- Agregar mini tendencia de stock (7 y 30 días).

- apps/inventario/views.py
- Construir datos agregados de tendencia por día para detalle.

- static/js/app.js
- Utilidad de render ligero para serie de tendencia.

Pruebas:

- python manage.py check
- Validación manual en productos con y sin movimientos.

Criterio de aceptación:

- Cada detalle de producto muestra trazabilidad reciente clara y tendencia simple.

## Sprint 4 - P2 cierre, accesibilidad y robustez (4-6 semanas)

Objetivo:

- Cerrar brechas de control operativo y experiencia inclusiva.

Tareas por archivo:

- apps/inventario/views.py
- Agregar vista de cierre de turno con resumen y checklist.

- templates/inventario
- Crear pantalla de cierre de turno y componentes de checklist.
- Mejorar atributos ARIA, focos visibles y navegación por teclado.

- static/css/estilo.css
- Ajustes de contraste y estilos de foco WCAG AA.

Pruebas:

- python manage.py check
- Auditoría manual de teclado en navegación principal.
- Revisión de contraste en componentes críticos.

Criterio de aceptación:

- Existe cierre de turno funcional.
- Navegación por teclado y contraste alcanzan estándar objetivo en pantallas principales.

## 18. Matriz de pruebas por rol

## Administrador

- Ver panel de alertas y CTA de riesgo.
- Ejecutar ajustes y validar trazabilidad.
- Revisar reportes y cierre de turno.

## Vendedor

- Completar venta con atajos únicamente por teclado.
- Forzar stock insuficiente y validar mensaje accionable.
- Recuperar carrito tras recarga.

## Bodeguero

- Completar compra rápida con proveedor y lista inicial.
- Validar alerta de precio fuera de rango.
- Crear producto con wizard y compra automática asociada.

## 19. Riesgos de implementación y mitigación

- Riesgo: introducir regresiones en POS por cambios de JS.
- Mitigación: activar cambios por flag simple de template y validar en staging.

- Riesgo: sobrecargar vistas con lógica UX.
- Mitigación: mover utilidades a funciones auxiliares y mantener endpoints delgados.

- Riesgo: inconsistencia visual entre pantallas.
- Mitigación: reutilizar clases del sistema de estilos y evitar estilos inline nuevos.

## 20. Criterios de salida por sprint

- Sprint aprobado solo si:
- Se cumplen criterios de aceptación del sprint.
- No rompe permisos por rol.
- Se ejecuta check técnico sin errores.
- Queda evidencia de demo funcional por rol.

## 21. Orden recomendado de ejecución inmediata

- Día 1-2: Sprint 0 completo.
- Semana 1: Sprint 1 POS venta + compra.
- Semana 2: Sprint 1 dashboard + cierre de pendientes.
- Semana 3-4: Sprint 2.
- Semana 5-6: Sprint 3.
- Semana 7-8: Sprint 4.

Con este plan, el proyecto pasa de diagnóstico UX a implementación incremental medible, reduciendo riesgo y mejorando operación real desde la primera semana.