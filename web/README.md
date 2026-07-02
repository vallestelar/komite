# Komite Front

Front web de Komite construido con Nuxt 3.

Esta aplicacion es el portal operativo para las empresas administradoras que son clientes de Komite. La usaran principalmente administradores, project managers, supervisores senior y equipo interno de la administradora para gestionar su cartera de condominios.

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

## Login

El login consume:

```text
POST /api/v1/auth/login
```

La sesion guarda el token y usuario en `localStorage`, `sessionStorage` y cookies simples.

## Estructura principal

- `app.vue`: entrada principal Nuxt.
- `pages/index.vue`: decide si muestra login o aplicacion segun la sesion.
- `components/LoginView.vue`: pantalla de inicio de sesion.
- `components/AppShell.vue`: layout principal con sidebar, topbar y menu del portal operativo.
- `components/DashboardView.vue`: dashboard inicial conectado a endpoints de resumen.
- `components/ToolsView.vue`: base del apartado Herramientas.
- `components/PlaceholderView.vue`: vista temporal para modulos preparados.
- `composables/useAuth.ts`: manejo de sesion.
- `composables/useApi.ts`: cliente base para llamadas a la API.
- `assets/css/main.css`: estilos globales del portal.

## Menu actual

El menu esta organizado para usuarios de la empresa administradora cliente:

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
