# Komite

Komite es una plataforma para administradoras de condominios. El repositorio
incluye:

- `marketing`: landing publica servida con Nginx.
- `web`: portal operativo Nuxt para clientes.
- `api`: API FastAPI, backoffice, migraciones y servicios.
- `postgres`: base de datos PostgreSQL.
- `redis`: soporte para servicios auxiliares.

## Requisitos

- Docker Desktop o Docker Engine con Docker Compose.
- Git.

Para desarrollo local del front sin Docker:

- Node.js compatible con Nuxt 3.
- `pnpm`.

Para desarrollo local de la API sin Docker:

- Python 3.12+.
- PostgreSQL y Redis locales.

## Configuracion inicial

Desde la raiz del proyecto:

```powershell
copy .env.production.example .env
```

Edita `.env` y cambia, como minimo:

```env
POSTGRES_PASSWORD=una_password_fuerte
JWT_SECRET_KEY=un_secreto_largo_y_aleatorio
SEED_ADMIN_PASSWORD=una_password_admin_fuerte
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

El archivo `.env` contiene secretos reales y no debe subirse al repositorio.

## Levantar toda la aplicacion con Docker

```powershell
docker compose up -d --build
```

Verificar servicios:

```powershell
docker compose ps
```

URLs locales:

```text
Marketing:  http://localhost:3001
Portal web: http://localhost:3000
API docs:   http://localhost:8000/docs
Backoffice: http://localhost:8000/login
Health API: http://localhost:8000/health
```

## Inicializar base de datos

Aplicar migraciones:

```powershell
docker compose exec -T api aerich upgrade
```

Crear roles y usuario administrador inicial:

```powershell
docker compose exec api python scripts/seed_auth.py
```

Las credenciales iniciales salen del `.env`:

```env
SEED_ADMIN_EMAIL=admin@komite.cl
SEED_ADMIN_PASSWORD=change_me_admin_password
```

## Comandos utiles

Ver logs de todos los servicios:

```powershell
docker compose logs -f
```

Ver logs de un servicio:

```powershell
docker compose logs -f api
docker compose logs -f web
docker compose logs -f marketing
```

Recrear despues de cambios:

```powershell
docker compose up -d --build
```

Detener servicios sin borrar datos:

```powershell
docker compose down
```

No uses `docker compose down -v` salvo que quieras borrar la base de datos y
los volumenes locales.

## Desarrollo local del portal web

```powershell
cd web
pnpm install
pnpm run dev
```

El portal queda en:

```text
http://localhost:3000
```

La API se configura con:

```env
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

## Desarrollo local de la API

```powershell
cd api
copy .env.example .env
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentacion:

```text
http://localhost:8000/docs
```

Mas detalle de API, migraciones y usuarios esta en `api/README.md`.

## Marketing

La web publica esta en `marketing/` y se sirve como sitio estatico con Nginx.
En Docker queda expuesta en:

```text
http://localhost:3001
```

Para cambios simples basta editar:

```text
marketing/index.html
marketing/assets/
```
