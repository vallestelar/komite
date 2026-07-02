# Komite - Diseño funcional del producto

## 1. Visión general

**Komite** es una plataforma para mantener informado al comité de administración, a los vecinos y al equipo interno de la administradora sobre todo lo que ocurre en los condominios.

No reemplaza sistemas administrativos como Edifito. Komite se enfoca en la operación diaria, la trazabilidad, la comunicación y la generación automática de informes.

La idea central es:

```text
Empleado / Conserje / Supervisor / Administrador
        ↓
Carga información en Komite
        ↓
Komite organiza, clasifica y redacta con IA
        ↓
Comité y vecinos reciben información clara y oportuna
```

---

## 2. Problema que resuelve

En muchos condominios existe una brecha entre lo que la administración hace y lo que el comité o los vecinos perciben.

Problemas habituales:

- El comité no sabe en qué estado están las tareas.
- Los vecinos sienten que no se les informa.
- Los supervisores reportan por WhatsApp de forma desordenada.
- Las fotos, audios y mensajes quedan perdidos en chats.
- Los informes se redactan manualmente.
- No existe historial claro de incidencias, mantenciones y compromisos.

Komite busca convertir la operación diaria en información estructurada, verificable y comunicable.

---

## 3. Propuesta de valor

**Komite transforma mensajes, audios, fotos y tareas internas en informes, comunicaciones y trazabilidad para condominios.**

Frases comerciales posibles:

- **Komite: todo lo que ocurre en tu condominio, informado a tiempo.**
- **Komite: transparencia operativa para comités y comunidades.**
- **Komite: de la gestión diaria al informe automático.**

---

## 4. Usuarios del sistema

### 4.1 Empleados del condominio

Ejemplos:

- Conserjes.
- Auxiliares.
- Personal de aseo.
- Mantención interna.

Uso principal:

- Reportar incidencias.
- Subir fotos.
- Registrar novedades.
- Informar trabajos realizados.

---

### 4.2 Supervisores

Uso principal:

- Crear inspecciones.
- Validar incidencias.
- Completar checklists.
- Subir evidencias.
- Generar informes de terreno.
- Marcar tareas como resueltas.

---

### 4.3 Administradores

Uso principal:

- Revisar la operación de todos los condominios.
- Aprobar informes generados por IA.
- Comunicar al comité o vecinos.
- Asignar tareas.
- Revisar indicadores.
- Controlar pendientes.

---

### 4.4 Comité de administración

Uso principal:

- Ver tablero del condominio.
- Revisar incidencias abiertas.
- Ver informes mensuales.
- Revisar mantenciones realizadas.
- Consultar historial.
- Aprobar o comentar ciertas solicitudes.

---

### 4.5 Vecinos

Uso principal:

- Recibir comunicados.
- Consultar novedades del condominio.
- Reportar incidencias, si se habilita.
- Ver estados generales publicados por la administración.

---

### 4.6 Empleados internos de la administradora

Uso principal en backoffice:

- Gestionar condominios.
- Gestionar usuarios y roles.
- Revisar todas las tareas.
- Preparar comunicaciones.
- Controlar indicadores globales.
- Revisar actividad de supervisores.

---

## 5. Plataformas necesarias

Komite debería tener tres grandes interfaces.

### 5.1 App móvil y tablet

Dirigida a:

- Supervisores.
- Conserjes.
- Personal de terreno.
- Comité.
- Vecinos.

Uso recomendado:

- Móvil para reportes rápidos.
- Tablet para supervisores en terreno.
- Tablet para reuniones de comité.

---

### 5.2 Web pública / portal de acceso

Dirigida a:

- Vecinos.
- Comité.
- Usuarios que no quieran instalar app.

Funcionalidades:

- Iniciar sesión.
- Ver comunicados.
- Ver informes publicados.
- Revisar estado del condominio.
- Consultar historial visible.

---

### 5.3 Backoffice web interno

Dirigido a:

- Administradora.
- Administradores.
- Supervisores senior.
- Personal interno.

Funcionalidades:

- Gestión global de condominios.
- Gestión de usuarios.
- Gestión de incidencias.
- Gestión de tareas.
- Generación y aprobación de informes.
- Envío de comunicaciones.
- Panel de métricas.

---

## 6. Arquitectura funcional propuesta

Basada en la arquitectura del proyecto entregado, Komite puede mantener una estructura similar:

```text
NIC Chile
    ↓
Cloudflare DNS + SSL
    ↓
AWS Lightsail Ubuntu
    ↓
Nginx Reverse Proxy
    ↓
Docker Compose
    ├── Frontend Web / Backoffice Nuxt (3000)
    ├── API FastAPI (8000)
    ├── PostgreSQL
    ├── Redis
    ├── Servicio IA / Workers
    ├── Servicio de notificaciones
    └── Servicio de integración Telegram / WhatsApp futuro
```

---

## 7. Arquitectura por componentes

### 7.1 Frontend web

Tecnología sugerida:

- Nuxt.
- Vue.
- Tailwind o similar.

Responsabilidad:

- Portal web.
- Backoffice.
- Panel comité.
- Panel vecinos.
- Dashboard administrador.

---

### 7.2 App móvil / tablet

Opciones recomendadas:

#### Opción A: Flutter

Ventajas:

- Una base de código para Android, iOS y tablet.
- Buen rendimiento.
- Muy adecuado para uso en terreno.

#### Opción B: React Native

Ventajas:

- Ecosistema amplio.
- Fácil integración con APIs.

Recomendación inicial:

**Flutter**, porque el proyecto tendrá bastante uso móvil, captura de fotos, audios, notificaciones y formularios offline.

---

### 7.3 API principal

Tecnología sugerida:

- FastAPI.
- Python.
- Tortoise ORM.
- Aerich para migraciones.

Responsabilidad:

- Autenticación.
- Condominios.
- Usuarios.
- Tareas.
- Incidencias.
- Informes.
- Comunicaciones.
- Archivos.
- Integración con IA.
- Permisos.

---

### 7.4 Base de datos

Tecnología:

- PostgreSQL.

Responsabilidad:

- Datos estructurados.
- Usuarios.
- Condominios.
- Tareas.
- Incidencias.
- Informes.
- Comunicaciones.
- Auditoría.

---

### 7.5 Redis

Uso recomendado:

- Colas de procesamiento.
- Estados temporales.
- Jobs en segundo plano.
- Cache de dashboards.
- Procesamiento de IA.

---

### 7.6 Servicio de IA

Puede estar integrado al backend o separado como worker.

Responsabilidades:

- Transcribir audios.
- Clasificar mensajes.
- Resumir novedades.
- Generar informes.
- Redactar comunicados.
- Transformar lenguaje informal en texto profesional.

Modelos posibles:

- OpenAI.
- Mistral.
- Claude.
- Gemini.

Recomendación:

- Empezar con API externa.
- No entrenar modelo propio al inicio.
- Usar plantillas rígidas para controlar la salida.

---

### 7.7 Servicio de archivos

Debe guardar:

- Fotos.
- Audios.
- PDFs.
- Documentos.
- Evidencias.

Opciones:

- Volumen local en Lightsail para MVP.
- S3 o compatible S3 para producción más robusta.

---

### 7.8 Servicio de notificaciones

Canales:

- Push móvil.
- Correo electrónico.
- Telegram.
- WhatsApp Business API en fase posterior.

---

## 8. Módulos funcionales

## 8.1 Módulo de condominios

Permite gestionar cada comunidad.

Campos principales:

- Nombre del condominio.
- Dirección.
- Torres.
- Cantidad de unidades.
- Comité asociado.
- Administrador responsable.
- Supervisores asignados.
- Canales de comunicación habilitados.

Funciones:

- Crear condominio.
- Editar datos.
- Asignar usuarios.
- Configurar reglas de comunicación.
- Configurar categorías de incidencias.

---

## 8.2 Módulo de usuarios y roles

Roles iniciales:

- Superadmin Komite.
- Administrador empresa.
- Administrador condominio.
- Supervisor.
- Conserje / empleado.
- Comité.
- Vecino.

Permisos por rol:

| Rol | Crear incidencia | Aprobar informe | Ver comité | Ver vecinos | Gestionar usuarios |
|---|---:|---:|---:|---:|---:|
| Superadmin | Sí | Sí | Sí | Sí | Sí |
| Administrador empresa | Sí | Sí | Sí | Sí | Sí |
| Administrador condominio | Sí | Sí | Sí | Sí | Parcial |
| Supervisor | Sí | No | Parcial | No | No |
| Conserje | Sí | No | No | No | No |
| Comité | No / opcional | No | Sí | Parcial | No |
| Vecino | Opcional | No | No | Sí | No |

---

## 8.3 Módulo de incidencias

Una incidencia es cualquier hecho reportado en el condominio.

Ejemplos:

- Falla de ascensor.
- Fuga de agua.
- Problema eléctrico.
- Reclamo por ruido.
- Portón detenido.
- Sensor sin funcionamiento.

Campos:

- Condominio.
- Categoría.
- Prioridad.
- Estado.
- Descripción original.
- Descripción profesional generada por IA.
- Fotos.
- Audios.
- Responsable.
- Fecha de creación.
- Fecha compromiso.
- Fecha de cierre.

Estados:

```text
Nueva
En revisión
Asignada
En proceso
Pendiente proveedor
Resuelta
Informada
Cerrada
```

---

## 8.4 Módulo de tareas

Las tareas son acciones concretas derivadas de incidencias, mantenciones o solicitudes del comité.

Ejemplo:

```text
Tarea: Revisar bomba N°2
Responsable: Supervisor técnico
Fecha límite: 30/06/2026
Checklist:
□ Revisar presión
□ Revisar ruido
□ Revisar tablero
□ Adjuntar fotos
```

Funciones:

- Crear tarea manual.
- Crear tarea desde incidencia.
- Asignar responsable.
- Agregar checklist.
- Adjuntar evidencia.
- Cambiar estado.
- Generar informe al cerrar.

---

## 8.5 Módulo de inspecciones

Pensado para supervisores.

Tipos:

- Revisión de bombas.
- Revisión de ascensores.
- Revisión de iluminación.
- Revisión de piscina.
- Revisión de estacionamientos.
- Revisión de sala de basura.
- Revisión general semanal.

Cada inspección puede tener:

- Checklist.
- Fotos obligatorias.
- Observaciones.
- Firma o confirmación.
- Geolocalización opcional.
- Informe automático.

---

## 8.6 Módulo de informes

Tipos de informes:

- Informe de incidencia.
- Informe de mantención.
- Informe de inspección.
- Informe mensual de gestión.
- Informe para comité.
- Informe para vecinos.

Flujo:

```text
Supervisor carga información
        ↓
IA genera borrador
        ↓
Administrador revisa
        ↓
Administrador aprueba
        ↓
Komite publica o envía
```

Estructura de informe:

```text
Título
Condominio
Fecha
Responsable
Resumen ejecutivo
Detalle de lo realizado
Observaciones
Recomendaciones
Evidencias fotográficas
Estado final
Próximos pasos
```

---

## 8.7 Módulo de comunicaciones

Permite enviar información al comité y a vecinos.

Canales:

- Publicación en portal/app.
- Push.
- Correo.
- Telegram.
- WhatsApp en fase posterior.

Tipos:

- Comunicado general.
- Comunicado urgente.
- Informe publicado.
- Aviso de mantención.
- Aviso de corte de servicio.
- Resumen mensual.

Reglas sugeridas:

| Evento | Comité | Vecinos |
|---|---|---|
| Falla crítica | Sí | Sí |
| Mantención programada | Sí | Sí |
| Tarea menor interna | Opcional | No |
| Informe mensual | Sí | Opcional |
| Reclamo individual | Sí, si corresponde | No |

---

## 8.8 Módulo de comité

Panel especial para miembros del comité.

Vista principal:

```text
Condominio
Incidencias abiertas
Tareas en proceso
Mantenciones realizadas
Próximas mantenciones
Comunicados publicados
Informes disponibles
```

Funciones:

- Ver estado general.
- Comentar incidencias.
- Descargar informes.
- Revisar historial.
- Ver compromisos pendientes.

---

## 8.9 Módulo de vecinos

Vista más simple y controlada.

Funciones:

- Ver comunicados.
- Ver novedades publicadas.
- Recibir notificaciones.
- Reportar incidencias, si se habilita.
- Consultar documentos públicos.

Importante:

El vecino no debe ver toda la gestión interna. Solo la información aprobada para comunidad.

---

## 8.10 Módulo de historial del condominio

Todo evento relevante queda registrado en una línea de tiempo.

Ejemplo:

```text
28/06/2026 - Mantención preventiva de bombas
27/06/2026 - Reparación luminaria Torre B
26/06/2026 - Falla portón vehicular resuelta
25/06/2026 - Informe mensual publicado
```

Debe permitir buscar por:

- Fecha.
- Categoría.
- Responsable.
- Condominio.
- Palabra clave.
- Estado.

---

## 8.11 Módulo de IA

Funciones principales:

### Clasificación automática

Entrada:

```text
"Hay agua saliendo por el shaft del piso 3"
```

Salida:

```text
Categoría: Agua / filtración
Prioridad: Alta
Requiere aviso: Sí
Destinatarios sugeridos: administrador y supervisor
```

### Redacción de informes

Entrada informal:

```text
"Se revisaron bombas, bomba 1 ok, bomba 2 con ruido, no hay fuga. Recomiendo mantención."
```

Salida formal:

```text
Durante la inspección del sistema de bombas se verificó el funcionamiento general del equipo. La bomba N°1 se encuentra operativa, mientras que la bomba N°2 presenta un ruido leve. No se detectaron filtraciones visibles. Se recomienda coordinar mantención preventiva.
```

### Redacción de comunicados

Versiones:

- Formal para correo.
- Breve para push.
- Directa para WhatsApp/Telegram.
- Técnica para comité.
- Simple para vecinos.

### Resúmenes mensuales

La IA debe generar:

- Resumen ejecutivo.
- Incidencias relevantes.
- Mantenciones realizadas.
- Pendientes.
- Recomendaciones.

---

## 9. Flujo principal del sistema

### 9.1 Reporte desde supervisor

```text
Supervisor abre app
    ↓
Selecciona condominio
    ↓
Crea inspección o incidencia
    ↓
Adjunta foto/audio/texto
    ↓
Komite clasifica
    ↓
Komite genera borrador
    ↓
Administrador revisa
    ↓
Se informa al comité o vecinos
```

---

### 9.2 Reporte desde conserje

```text
Conserje reporta novedad
    ↓
Supervisor recibe alerta
    ↓
Supervisor valida
    ↓
Se crea tarea
    ↓
Se resuelve
    ↓
Se genera evidencia
```

---

### 9.3 Informe mensual

```text
Fin de mes
    ↓
Komite recopila tareas, incidencias y mantenciones
    ↓
IA genera informe mensual
    ↓
Administrador revisa
    ↓
Se publica al comité
```

---

## 10. Integraciones de comunicación

### 10.1 Telegram para MVP

Recomendado para:

- Supervisores.
- Empleados internos.
- Comité piloto.

Ventajas:

- API gratuita.
- Fácil recepción de mensajes.
- Soporte de fotos, audios y documentos.
- Ideal para validar el flujo de IA.

---

### 10.2 WhatsApp Business API futuro

Recomendado para:

- Vecinos.
- Comunicaciones sensibles.
- Respuestas a mensajes entrantes.

Uso sugerido:

- Primero como canal de recepción.
- Luego como canal de respuesta controlada.
- Comunicados masivos solo cuando tenga sentido.

---

### 10.3 Correo electrónico

Uso recomendado:

- Informes formales.
- Comunicados extensos.
- Documentos adjuntos.
- Resúmenes mensuales.

---

### 10.4 Push móvil

Uso recomendado:

- Avisos rápidos.
- Alertas internas.
- Notificación al comité.
- Recordatorios.

---

## 11. Backoffice web

El backoffice debe ser el centro de control de la administradora.

### Pantallas principales

1. Dashboard general.
2. Condominios.
3. Incidencias.
4. Tareas.
5. Inspecciones.
6. Informes.
7. Comunicaciones.
8. Usuarios.
9. Roles y permisos.
10. Configuración de IA.
11. Configuración de canales.
12. Auditoría.

---

## 12. App móvil/tablet

### Pantallas para supervisores

1. Inicio con tareas del día.
2. Selección de condominio.
3. Crear incidencia.
4. Crear inspección.
5. Capturar foto.
6. Grabar audio.
7. Checklist.
8. Tareas asignadas.
9. Historial del condominio.
10. Enviar informe a revisión.

---

### Pantallas para comité

1. Dashboard del condominio.
2. Incidencias abiertas.
3. Tareas relevantes.
4. Informes.
5. Comunicados.
6. Historial.
7. Comentarios o solicitudes.

---

### Pantallas para vecinos

1. Comunicados.
2. Novedades.
3. Alertas.
4. Reportar incidencia.
5. Documentos públicos.
6. Perfil.

---

## 13. Modelo de datos inicial

Tablas sugeridas:

```text
companies
condominiums
buildings
units
users
roles
user_condominiums
incidents
incident_events
tasks
task_checklists
inspections
inspection_templates
inspection_answers
reports
report_versions
communications
communication_recipients
attachments
audit_logs
ai_requests
notification_logs
```

---

## 14. Estados y trazabilidad

Cada acción importante debe guardar:

- Usuario.
- Fecha.
- Condominio.
- Acción realizada.
- Estado anterior.
- Estado nuevo.
- Evidencia adjunta.

Ejemplo:

```text
28/06/2026 12:30
Supervisor Juan cerró la tarea "Revisión de bombas".
Adjuntó 4 fotografías.
IA generó informe preliminar.
Administrador aprobó a las 13:10.
```

---

## 15. Seguridad y permisos

Requisitos:

- Login con JWT.
- Roles por condominio.
- Separación estricta de datos entre condominios.
- Auditoría de acciones.
- Control de acceso a documentos.
- Aprobación humana antes de comunicaciones masivas.

Regla clave:

```text
Un usuario solo puede ver información de los condominios donde está asignado.
```

---

## 16. MVP recomendado

Para partir, no construiría todo.

El MVP debería incluir:

1. Gestión de condominios.
2. Usuarios y roles básicos.
3. App móvil/tablet para supervisores.
4. Registro de incidencias con foto/audio/texto.
5. Tareas con estados.
6. Generación de informe con IA.
7. Aprobación manual del administrador.
8. Panel web para comité.
9. Publicación de comunicados en portal/app.
10. Envío por correo.
11. Integración Telegram para uso interno.

Dejaría para fase 2:

- WhatsApp Business API.
- Notificaciones push avanzadas.
- App completa para vecinos.
- Firma digital.
- Analítica avanzada.
- Integración con Edifito.

---

## 17. Fases del proyecto

### Fase 1 - MVP operativo

Objetivo:

Validar que supervisores puedan alimentar el sistema y que la IA genere informes útiles.

Incluye:

- Backoffice.
- App supervisor.
- Incidencias.
- Tareas.
- Informes IA.
- Comité con panel básico.

---

### Fase 2 - Comunicación y vecinos

Objetivo:

Convertir Komite en canal de información para la comunidad.

Incluye:

- App/portal vecinos.
- Comunicados.
- Push.
- Correo.
- Segmentación por torre/unidad.

---

### Fase 3 - Automatización avanzada

Objetivo:

Reducir trabajo administrativo repetitivo.

Incluye:

- WhatsApp Business API.
- Telegram bot completo.
- Informes mensuales automáticos.
- Reglas de comunicación.
- Respuestas sugeridas.

---

### Fase 4 - Inteligencia operativa

Objetivo:

Transformar datos históricos en decisiones.

Incluye:

- KPIs.
- Predicción de problemas recurrentes.
- Ranking de proveedores.
- Cumplimiento de mantenciones.
- Comparativa entre condominios.

---

## 18. Arquitectura técnica sugerida

```text
komite/
├── api/
│   ├── app/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── condominiums/
│   │   │   ├── users/
│   │   │   ├── incidents/
│   │   │   ├── tasks/
│   │   │   ├── inspections/
│   │   │   ├── reports/
│   │   │   ├── communications/
│   │   │   ├── attachments/
│   │   │   └── ai/
│   │   ├── core/
│   │   └── main.py
│   ├── migrations/
│   └── Dockerfile
│
├── web/
│   ├── pages/
│   ├── components/
│   ├── layouts/
│   └── Dockerfile
│
├── mobile/
│   ├── lib/
│   ├── android/
│   └── ios/
│
├── docker-compose.yml
├── deploy.sh
├── .env.example
└── README.md
```

---

## 19. Contenedores sugeridos

```text
Docker Compose
    ├── web              Nuxt Backoffice / Portal
    ├── api              FastAPI
    ├── postgres         PostgreSQL
    ├── redis            Redis
    ├── worker           Procesamiento IA / jobs
    ├── nginx            Opcional si se gestiona dentro de Docker
    └── telegram-bot     Opcional, puede ser parte del worker
```

---

## 20. Dominios sugeridos

```text
komite.cl
app.komite.cl
api.komite.cl
admin.komite.cl
```

Para un primer despliegue:

```text
app.komite.cl       → Web / portal / backoffice
api.komite.cl       → API FastAPI
```

---

## 21. Variables de entorno sugeridas

```env
APP_NAME=Komite
ENVIRONMENT=production

POSTGRES_DB=komite_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

NUXT_PUBLIC_API_BASE=https://api.komite.cl/api/v1

AI_PROVIDER=openai_or_mistral
AI_API_KEY=change_me
AI_MODEL=change_me

TELEGRAM_BOT_TOKEN=change_me

SMTP_HOST=change_me
SMTP_PORT=587
SMTP_USER=change_me
SMTP_PASSWORD=change_me
SMTP_FROM=no-reply@komite.cl
```

---

## 22. Reglas de IA

Para evitar errores, la IA debe trabajar bajo reglas estrictas.

Reglas:

1. No inventar hechos.
2. No agregar información que no esté en el reporte original.
3. Diferenciar entre hecho, observación y recomendación.
4. Generar siempre borradores revisables.
5. Guardar el texto original junto al texto generado.
6. Indicar nivel de confianza si la información es ambigua.
7. Pedir validación humana para comunicaciones sensibles.

---

## 23. Ejemplo completo de uso

### Entrada del supervisor

```text
Audio:
"Estamos en sala de bombas de Vista Sol. Revisamos bomba uno y bomba dos. Bomba uno normal. Bomba dos con ruido leve. No vimos fuga. Recomiendo pedir mantención preventiva."
```

### Komite genera incidencia/tarea

```text
Categoría: Bombas
Prioridad: Media
Estado: En revisión
Responsable sugerido: Supervisor técnico
Requiere comunicación: Comité sí, vecinos no necesariamente
```

### Komite genera informe

```text
Informe de revisión de bombas

Condominio: Vista Sol
Fecha: 28/06/2026
Responsable: Supervisor asignado

Resumen:
Se realizó una revisión del sistema de bombas del condominio. La bomba N°1 se encuentra funcionando normalmente. La bomba N°2 presenta un ruido leve durante su operación.

Observaciones:
- No se detectaron filtraciones visibles.
- Se recomienda coordinar mantención preventiva.

Estado:
Revisión realizada con observación pendiente.
```

### Komite propone mensaje al comité

```text
Estimados miembros del comité:

Informamos que se realizó una revisión del sistema de bombas del condominio. La bomba N°1 se encuentra funcionando normalmente y la bomba N°2 presenta un ruido leve, por lo que se recomienda coordinar una mantención preventiva.

No se detectaron filtraciones visibles.

Saludos,
Administración.
```

---

## 24. Diferenciadores de Komite

1. No compite con Edifito: complementa la operación diaria.
2. Convierte reportes informales en informes profesionales.
3. Da trazabilidad al comité.
4. Reduce la dependencia de WhatsApp desordenado.
5. Permite evidencias fotográficas y audios.
6. Crea historial consultable por condominio.
7. Genera reportes mensuales automáticamente.
8. Permite medir desempeño de la administración.
9. Centraliza tareas, informes y comunicaciones.
10. Da sensación de transparencia y control.

---

## 25. Indicadores clave

KPIs iniciales:

- Incidencias abiertas.
- Incidencias cerradas.
- Tiempo promedio de resolución.
- Tareas vencidas.
- Tareas por supervisor.
- Mantenciones realizadas.
- Comunicaciones enviadas.
- Informes aprobados.
- Incidencias por categoría.
- Condominios con más pendientes.

---

## 26. Riesgos del proyecto

### Riesgo 1: Sobrecargar a empleados

Solución:

- Formularios muy simples.
- Uso de audio y foto.
- Mínimos campos obligatorios.

### Riesgo 2: Que la IA invente información

Solución:

- Plantillas cerradas.
- Aprobación humana.
- Texto original siempre visible.

### Riesgo 3: Baja adopción de vecinos

Solución:

- Primero comité y supervisores.
- Luego vecinos con portal simple.
- WhatsApp solo en fase posterior.

### Riesgo 4: Demasiado alcance inicial

Solución:

- MVP enfocado en supervisores, informes y comité.

---

## 27. Recomendación final

El mejor punto de partida para Komite es:

```text
App supervisor + Backoffice administrador + Panel comité + IA de informes
```

No empezaría por vecinos ni por WhatsApp.

Primero validaría que la administradora pueda demostrar al comité:

- Qué se hizo.
- Cuándo se hizo.
- Quién lo hizo.
- Qué evidencia existe.
- Qué queda pendiente.

Ese es el corazón del producto.

Cuando ese flujo funcione, se añade comunicación masiva, app vecinos y WhatsApp Business.
