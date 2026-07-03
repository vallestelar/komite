# Komite API

API base de Komite construida con FastAPI, Tortoise ORM, Aerich y PostgreSQL.

## Requisitos

- Python 3.12+
- PostgreSQL
- Redis, para fases posteriores

## Configuracion inicial

Desde la carpeta `api`:

```powershell
cd api
copy .env.example .env
```

Edita `.env` con los datos reales de PostgreSQL:

```env
POSTGRES_DB=komite_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Entorno virtual

Crear entorno:

```powershell
python -m venv venv
```

Activar entorno:

```powershell
.\venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Si el entorno virtual falla con un mensaje parecido a `Unable to create process`, recrealo:

```powershell
deactivate
Rename-Item venv venv_old
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar API

Modo desarrollo:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backoffice integrado:

```text
http://localhost:8000/login
http://localhost:8000/backoffice
```

Abrir documentacion Swagger:

```text
http://localhost:8000/docs
```

Comprobar salud:

```text
http://localhost:8000/health
```

Probar solo la conexion a PostgreSQL:

```powershell
python scripts\check_db.py
```

Crear la base configurada en `.env` si no existe:

```powershell
python scripts\create_database.py
```

Si aparece `ConnectionDoesNotExistError`, revisa primero:

- Que PostgreSQL este iniciado.
- Que exista la base `komite_db`.
- Que usuario y password del `.env` sean correctos.
- Que `POSTGRES_HOST` sea `127.0.0.1` en Windows local.

## Depuracion en VS Code

Abre directamente la carpeta `api` en VS Code:

```powershell
code .
```

Configuraciones disponibles en `Run and Debug`:

- `Komite API - Debug`: recomendado para breakpoints estables.
- `Komite API - Debug con reload`: reinicia el servidor al cambiar archivos.

Tareas disponibles con `Terminal > Run Task`:

- `Instalar dependencias`
- `Ejecutar API`
- `Compilar Python`
- `Probar conexion BBDD`
- `Crear BBDD si no existe`
- `Seed auth`
- `Aerich init-db`
- `Aerich migrate`
- `Aerich upgrade`

## Base de datos y migraciones

## Modelo multi-tenant

KOMITE usa una unica base de datos compartida. La tabla `companies` representa el tenant.

- Las entidades principales de negocio guardan `company_id` directo.
- Las entidades que nacen desde un condominio, incidencia, tarea, inspeccion, informe o comunicacion calculan `company_id` automaticamente desde esa relacion.
- Los endpoints de lectura filtran por empresa y condominios permitidos cuando el usuario no es empleado de Komite.
- El backoffice queda reservado a empleados de Komite y puede operar sobre todos los tenants.
- `banks` y `roles` funcionan como catalogos globales del sistema.

## Roles y perfiles

El modelo de acceso se mantiene intencionalmente reducido:

- `users.company_profile`: perfil del Portal Administrador: `project_manager` o `ejecutivo`.
- `roles`: accesos mobile por condominio: `vecino`, `comite`, `supervisor` y `conserje`.
- En `user_condominiums`, `condominium_id = null` representa acceso a todos los condominios activos de la empresa del usuario.
- El backoffice de Komite exige usuario activo perteneciente a la empresa `Komite`.

Inicializar Aerich una sola vez:

```powershell
python -m aerich.cli init -t app.dbs.postgres.tortoise_config.TORTOISE_ORM
```

Inicializar la base de datos:

```powershell
python -m aerich.cli init-db
```

Crear una migracion despues de cambiar modelos:

```powershell
python -m aerich.cli migrate --name descripcion_del_cambio
```

Aplicar migraciones pendientes:

```powershell
python -m aerich.cli upgrade
```

Ver historial de migraciones:

```powershell
python -m aerich.cli history
```

## Login y token

Crear roles iniciales y usuario admin de desarrollo:

```powershell
python scripts\seed_auth.py
```

Credenciales por defecto, configurables en `.env`:

```env
SEED_ADMIN_EMAIL=admin@komite.cl
SEED_ADMIN_PASSWORD=admin1234
SEED_ADMIN_FULL_NAME=Administrador Komite
```

Solicitar token:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"admin@komite.cl","password":"admin1234"}'
```

Consultar usuario actual:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://localhost:8000/api/v1/auth/me `
  -Headers @{ Authorization = "Bearer TU_TOKEN" }
```

Crear un usuario desde consola:

```powershell
python scripts\create_user.py --email usuario@komite.cl --password demo1234 --full-name "Usuario Demo"
```

Crear un usuario desde la API:

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"admin@komite.cl","password":"admin1234"}'

$token = $login.access_token

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/users/ `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{
    "email": "nuevo@komite.cl",
    "password": "demo1234",
    "full_name": "Nuevo Usuario",
    "company_profile": "ejecutivo",
    "memberships": [
      {
        "condominium_id": null,
        "role_code": "supervisor"
      }
    ]
  }'
```

Crear usuario y asignarlo a un condominio:

```powershell
python scripts\create_user.py `
  --email supervisor@komite.cl `
  --password demo1234 `
  --full-name "Supervisor Demo" `
  --condominium-id ID_DEL_CONDOMINIO `
  --company-profile ejecutivo `
  --role-code supervisor
```

## CRUD de entidades

Todos los CRUD requieren token Bearer. Cada recurso tiene clases Pydantic
especificas para request/response: `EntidadCreate`, `EntidadUpdate`,
`EntidadOut` y `EntidadPage`.

Patron general:

```text
POST   /api/v1/{recurso}/
GET    /api/v1/{recurso}/?page=1&page_size=20&q=texto
GET    /api/v1/{recurso}/{id}
PATCH  /api/v1/{recurso}/{id}
DELETE /api/v1/{recurso}/{id}
```

Recursos disponibles:

```text
companies
condominiums
buildings
units
roles
users
user-condominiums
incidents
incident-events
tasks
task-checklists
inspection-templates
inspections
inspection-answers
reports
report-versions
communications
communication-recipients
attachments
audit-logs
ai-requests
notification-logs
```

Ejemplo creando un condominio:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/condominiums/ `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{
    "company_id": "ID_DE_LA_EMPRESA",
    "name": "Vista Sol",
    "address": "Av. Principal 123",
    "commune": "Santiago",
    "city": "Santiago",
    "region": "Metropolitana",
    "towers_count": 2,
    "units_count": 120
  }'
```

Ejemplo listando incidencias:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://localhost:8000/api/v1/incidents/?page=1&page_size=20&q=agua" `
  -Headers @{ Authorization = "Bearer $token" }
```

## Audio e IA

Configura OpenAI en `.env`:

```env
AI_PROVIDER=openai
AI_API_KEY=tu_api_key
TRANSCRIPTION_PROVIDER=local_whisper
LOCAL_WHISPER_MODEL=small
LOCAL_WHISPER_DEVICE=cpu
LOCAL_WHISPER_COMPUTE_TYPE=int8
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe
OPENAI_DRAFT_MODEL=gpt-5.5
UPLOAD_DIR=storage/uploads
MAX_AUDIO_UPLOAD_MB=25
```

Instala dependencias nuevas:

```powershell
pip install -r requirements.txt
```

Subir audio, transcribir y generar borrador profesional:

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"admin@komite.cl","password":"admin1234"}'

$token = $login.access_token

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/audio/transcriptions `
  -Headers @{ Authorization = "Bearer $token" } `
  -Form @{
    file = Get-Item "C:\ruta\audio.mp3"
    language = "es"
    generate_draft = "true"
  }
```

Para probar sin coste de OpenAI, deja `TRANSCRIPTION_PROVIDER=local_whisper` y envia
`generate_draft=false`. La transcripcion se hara localmente con `faster-whisper`.
La primera ejecucion puede tardar porque descarga/carga el modelo local.

El flujo guarda el archivo en `UPLOAD_DIR`, crea un registro en `attachments`,
registra trazas en `ai_requests`, transcribe el audio y opcionalmente genera un
borrador operativo con prompt.

## Docker

Construir imagen:

```powershell
docker build -t komite-api .
```

Ejecutar contenedor:

```powershell
docker run --env-file .env -p 8000:8000 komite-api
```

## Estructura principal

```text
api/
  app/
    api/v1/routes/        Rutas HTTP
    core/                 Configuracion y utilidades globales
    dbs/postgres/         Conexion, Tortoise y repositorio generico
    models/entities/      Modelos de base de datos
    schemas/              DTOs Pydantic
    services/             Servicios de aplicacion
  migrations/             Migraciones Aerich
```

## Modelos iniciales

La primera version incluye las tablas principales del MVP:

- `companies`
- `condominiums`
- `buildings`
- `units`
- `users`
- `roles`
- `user_condominiums`
- `incidents`
- `incident_events`
- `tasks`
- `task_checklists`
- `inspections`
- `inspection_templates`
- `inspection_answers`
- `reports`
- `report_versions`
- `communications`
- `communication_recipients`
- `attachments`
- `audit_logs`
- `ai_requests`
- `notification_logs`
