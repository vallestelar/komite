# Komite Front

Front web de Komite construido con Nuxt 3.

Esta aplicacion es el portal operativo para las empresas administradoras que son clientes de Komite. La usaran principalmente usuarios con perfil de Portal Administrador: project managers, supervisores y ejecutivos/as, segun permisos.

No es el backoffice interno de Komite como empresa. El backoffice interno debe quedar reservado para que Komite controle clientes, configuraciones globales, permisos de plataforma, usuarios de tenants, auditoria SaaS y parametros generales del servicio.

## Requisitos

- Node.js 22 o compatible.
- pnpm 11 o compatible.

> En este entorno `npm` no esta funcionando correctamente, por eso el proyecto se dejo preparado con `pnpm`.

## Instalacion

Desde la carpeta `web`:

```bash
pnpm install
```

Si pnpm pide aprobar builds de dependencias nativas:

```bash
pnpm approve-builds --all
pnpm install
```

## Ejecutar en desarrollo

```bash
pnpm run dev
```

Por defecto Nuxt levanta la aplicacion en:

```text
http://localhost:3000
```

## Compilar

```bash
pnpm run build
```

Para previsualizar el build:

```bash
pnpm run preview
```

## Configuracion de API

La URL base de la API se define con:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

Si no se define, el front usa:

```text
http://localhost:8000
```

Tambien se puede sobrescribir desde el navegador usando `localStorage`:

```js
localStorage.setItem("komite_api_base", "http://localhost:8000")
```

## Login y contexto activo

El login consume:

```text
POST /api/v1/auth/login
```

El flujo del portal es en dos pasos:

1. El usuario inicia sesion con email y password.
2. El backend devuelve la empresa asociada y los condominios permitidos para ese usuario.
3. El usuario selecciona el condominio activo.
4. Al confirmar, el portal guarda la sesion completa y entra a la aplicacion.

La sesion guarda token, usuario, empresa, condominios disponibles y condominio activo en `localStorage` y `sessionStorage`.

Todas las llamadas posteriores a la API envian el condominio activo en el header:

```text
X-Condominium: <condominium_id>
```

El backend debe validar que el usuario tenga permiso sobre ese condominio y usar este contexto para devolver informacion del tenant/condominio seleccionado.

## Estructura principal

- `app.vue`: entrada principal Nuxt.
- `pages/index.vue`: decide si muestra login o aplicacion segun la sesion.
- `components/LoginView.vue`: pantalla de inicio de sesion.
- `components/AppShell.vue`: layout principal con sidebar, topbar y menu del portal operativo.
- `components/DashboardView.vue`: dashboard inicial conectado a endpoints de resumen.
- `components/ToolsView.vue`: base del apartado Herramientas.
- `components/PlaceholderView.vue`: vista temporal para modulos preparados.
- `composables/useAuth.ts`: manejo de sesion, empresa y condominio activo.
- `composables/useApi.ts`: cliente base para llamadas a la API, incluyendo `X-Condominium`.
- `assets/css/main.css`: estilos globales del portal.

## Menu actual

El menu esta organizado para usuarios de la empresa administradora cliente:

- `company_profile` define el perfil del Portal Administrador: `project_manager`, `supervisor` o `ejecutivo`.
- Los roles mobile (`vecino`, `comite`, `supervisor`, `conserje`) determinan el acceso por condominio.
- Un acceso mobile con condominio `Todos` permite ver todos los condominios activos de la empresa del usuario.

- Inicio
- Cartera
- Operacion diaria
- Informes y comunicacion
- Herramientas
- Gestion interna

## Criterio funcional

Este front debe permitir que la administradora cliente trabaje su operacion diaria:

- Ver estado de su cartera de condominios.
- Gestionar incidencias, tareas, inspecciones y evidencias.
- Revisar y publicar informes.
- Preparar comunicados hacia comites o comunidades.
- Usar herramientas para procesar audios, planillas y resumenes.
- Gestionar su propio equipo operativo y accesos por condominio.

Lo que no debe vivir aqui:

- Alta y administracion de empresas cliente de Komite.
- Configuracion global de la plataforma.
- Roles globales SaaS de Komite.
- Auditoria interna de Komite como proveedor.
- Parametros comerciales, billing o control multi-tenant global.

El apartado **Herramientas** queda preparado para agregar funcionalidades de procesamiento de datos, importacion de planillas, transcripcion de audios y automatizaciones de apoyo para el equipo de la administradora.
