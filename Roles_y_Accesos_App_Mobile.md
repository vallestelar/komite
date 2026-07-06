# Roles y accesos en la app mobile Komite

Este documento explica el modelo actual de usuarios, perfiles y accesos para la app mobile Komite. Tambien aclara la diferencia entre Portal Administrador, app mobile y backoffice interno.

## Resumen actual

Komite separa los permisos en tres conceptos distintos:

```text
Empresa / tenant
  -> Perfil Portal Administrador, si aplica
  -> Accesos a condominios app mobile
      -> Rol mobile
      -> Unidad, si aplica
```

El rol global fue eliminado. Ya no se usa `users.global_role`.

## Empresa / tenant

Cada usuario puede pertenecer a una empresa mediante `users.company_id`.

La empresa sirve para:

- Separar datos entre tenants.
- Saber a que administradora pertenece el usuario.
- Determinar que condominios puede expandir un acceso mobile marcado como `Todos`.
- Restringir el backoffice interno a usuarios activos de la empresa `Komite`.

## Perfil Portal Administrador

El campo `users.company_profile` se usa para el Portal Administrador, es decir, la web app administrativa de la empresa administradora cliente.

Valores actuales:

| Perfil Portal Administrador | Uso esperado |
|---|---|
| `project_manager` | Gestion y coordinacion de la operacion de la empresa administradora. |
| `supervisor` | Supervision operativa desde el Portal Administrador, seguimiento de trabajo en terreno y control de actividades. |
| `ejecutivo` | Gestion operativa administrativa, seguimiento, consultas y tareas. |
| Sin perfil | El usuario no tiene acceso funcional al Portal Administrador por perfil. |

Importante:

- Este perfil aplica a la web app administrativa.
- No es un rol mobile.
- No debe confundirse con `vecino`, `comite`, `supervisor` o `conserje`.
- El perfil Portal Administrador `supervisor` no debe confundirse con el rol mobile `supervisor`; comparten nombre funcional, pero viven en campos distintos.
- Conserje pertenece al ambito mobile/operativo, no al perfil del portal.

## Backoffice interno Komite

El backoffice interno es solo para Komite como proveedor SaaS.

Puede entrar un usuario que cumpla:

```text
Usuario activo
Empresa asignada: Komite
Empresa Komite activa
```

Ya no existe condicion por rol global. Cualquier usuario activo de la empresa `Komite` puede entrar al backoffice interno.

Uso esperado del backoffice:

- Gestionar empresas clientes.
- Gestionar condominios.
- Gestionar usuarios.
- Gestionar tickets de soporte.
- Gestionar bancos y catalogos globales.
- Revisar datos generales de la plataforma.

## Accesos a condominios app mobile

Los accesos mobile viven en `user_condominiums`.

Cada acceso contiene:

```text
Empresa
Usuario
Condominio o Todos
Rol mobile
Unidad opcional
Estado
```

La app mobile usa estos accesos para decidir que contexto mostrar al usuario.

## Condominio especifico o Todos

En el backoffice, dentro de usuarios, el bloque se llama:

```text
Accesos a condominios app mobile
```

En el combo de condominio existen dos formas de configuracion.

### 1. Condominio especifico

Ejemplo:

```text
Condominio: Vista Sol
Rol: supervisor
Unidad: Sin unidad
```

Resultado:

```text
El usuario ve Vista Sol en la app mobile con rol supervisor.
```

### 2. Todos

Ejemplo:

```text
Condominio: Todos
Rol: supervisor
Unidad: bloqueada / Sin unidad
```

Resultado:

```text
El usuario ve todos los condominios activos de su empresa en la app mobile.
```

Reglas de `Todos`:

- Se guarda con `condominium_id = null`.
- La unidad queda bloqueada.
- La unidad siempre debe quedar vacia.
- Requiere que el usuario tenga empresa asignada.
- Al iniciar sesion, la API expande ese acceso a todos los condominios activos de la empresa del usuario.

## Roles mobile

Los roles mobile disponibles son:

```text
vecino
comite
supervisor
conserje
```

Se dividen en dos grupos funcionales.

## Roles de Comunidad

Estos roles llevan al modo Comunidad:

```text
vecino
comite
```

### Vecino

Uso esperado:

- Residente, propietario o usuario asociado a una comunidad.
- Normalmente deberia tener unidad asignada.
- Ve informacion y funcionalidades de su comunidad.

Ejemplo:

```text
Condominio: Vista Sol
Rol: vecino
Unidad: 1204
```

### Comite

Uso esperado:

- Miembro del comite de administracion.
- Puede tener unidad o no.
- Tiene una vision comunitaria mas amplia que un vecino.

Ejemplo:

```text
Condominio: Vista Sol
Rol: comite
Unidad: Sin unidad
```

## Roles de Operacion

Estos roles llevan al modo Operacion:

```text
supervisor
conserje
```

### Supervisor

Uso esperado:

- Usuario de la empresa administradora.
- Gestiona operacion en terreno.
- Puede revisar tareas, incidencias, inspecciones y seguimiento operativo.
- Puede tener un condominio especifico o acceso a `Todos`.

Ejemplo:

```text
Condominio: Todos
Rol: supervisor
Unidad: Sin unidad
```

### Conserje

Uso esperado:

- Usuario operativo de terreno o conserjeria.
- Registra novedades, eventos o incidencias.
- Normalmente trabaja sobre uno o varios condominios concretos.

Ejemplo:

```text
Condominio: Vista Sol
Rol: conserje
Unidad: Sin unidad
```

## Unidad

La unidad apunta a la tabla `units`.

Sirve para vincular al usuario con un departamento, casa, oficina o local dentro de un condominio.

Ejemplo de vecino:

```text
Usuario: Claudia Fuentes
Condominio: Vista Sol
Rol: vecino
Unidad: 1204
```

Ejemplo operativo:

```text
Usuario: Antonio Vergara
Condominio: Vista Sol
Rol: supervisor
Unidad: Sin unidad
```

Regla practica:

- Para `vecino`, conviene asignar unidad en casos reales.
- Para `comite`, la unidad puede ser opcional.
- Para `supervisor` y `conserje`, normalmente se deja sin unidad.
- Para `Todos`, la unidad queda bloqueada y debe ser nula.

## Flujo despues del login mobile

La app decide asi:

```text
Login correcto
  -> API devuelve empresa y condominios permitidos
  -> Si existe acceso Todos:
       -> API lo expande a todos los condominios activos de la empresa
  -> App clasifica accesos por rol mobile
  -> Si tiene Comunidad y Operacion:
       -> muestra selector de modo
  -> Si solo tiene Comunidad:
       -> entra o selecciona comunidad
  -> Si solo tiene Operacion:
       -> entra o selecciona condominio operativo
```

Nota actual del Portal Administrador:

Si un usuario tiene doble rol en un mismo condominio, por ejemplo `supervisor` y `comite`, el selector de condominio del Portal Administrador debe mostrar el condominio una sola vez y solo por nombre.

## Casos de configuracion

### Caso 1: vecino con una sola comunidad

Configuracion:

```text
Empresa: Administradora cliente
Perfil Portal Administrador: Sin perfil
Accesos mobile:
  - Condominio Vista Sol / vecino / Unidad 1204
```

Resultado:

```text
App mobile
  -> Modo Comunidad
  -> Condominio activo: Vista Sol
  -> Unidad: 1204
```

### Caso 2: vecino con varias comunidades

Configuracion:

```text
Accesos mobile:
  - Condominio Vista Sol / vecino / Unidad 1204
  - Condominio Espacio Uno III / vecino / Unidad 804
```

Resultado:

```text
App mobile
  -> Selector de comunidad
      - Vista Sol / Unidad 1204
      - Espacio Uno III / Unidad 804
```

### Caso 3: miembro de comite

Configuracion:

```text
Accesos mobile:
  - Condominio Vista Sol / comite / Sin unidad
```

Resultado:

```text
App mobile
  -> Modo Comunidad
  -> Condominio activo: Vista Sol
```

### Caso 4: supervisor con un condominio

Configuracion:

```text
Accesos mobile:
  - Condominio Vista Sol / supervisor / Sin unidad
```

Resultado:

```text
App mobile
  -> Modo Operacion
  -> Condominio activo: Vista Sol
```

### Caso 5: supervisor con todos los condominios de su empresa

Configuracion:

```text
Empresa: Administradora cliente
Accesos mobile:
  - Todos / supervisor / Sin unidad
```

Resultado:

```text
Login
  -> API busca todos los condominios activos de la empresa
  -> App muestra esos condominios como opciones operativas
  -> Usuario trabaja en modo Operacion
```

### Caso 6: conserje con un condominio

Configuracion:

```text
Accesos mobile:
  - Condominio Vista Sol / conserje / Sin unidad
```

Resultado:

```text
App mobile
  -> Modo Operacion
  -> Condominio activo: Vista Sol
```

### Caso 7: usuario con Comunidad y Operacion en el mismo condominio

Configuracion:

```text
Accesos mobile:
  - Condominio Vista Sol / comite / Sin unidad
  - Condominio Vista Sol / supervisor / Sin unidad
```

Resultado en app mobile:

```text
Login
  -> Selector de modo
      - Comunidad
      - Operacion
```

Si elige Comunidad:

```text
Condominio activo: Vista Sol
Rol funcional: comite
```

Si elige Operacion:

```text
Condominio activo: Vista Sol
Rol funcional: supervisor
```

Resultado en Portal Administrador:

```text
Selector de condominio:
  - Vista Sol
```

El condominio aparece una sola vez, sin mostrar el rol.

### Caso 8: usuario de Portal Administrador sin mobile

Configuracion:

```text
Empresa: Administradora cliente
Perfil Portal Administrador: project_manager
Accesos mobile:
  - Ninguno
```

Resultado:

```text
Portal Administrador:
  -> Puede entrar segun perfil.

App mobile:
  -> No tiene condominios habilitados.
```

### Caso 9: usuario interno Komite para backoffice

Configuracion:

```text
Empresa: Komite
Estado usuario: active
Perfil Portal Administrador: opcional
Accesos mobile: opcional
```

Resultado:

```text
Backoffice:
  -> Puede entrar.

Portal Administrador:
  -> No es su canal principal.

App mobile:
  -> Solo tendra contexto si se le asignan accesos mobile.
```

## Que ve cada tipo de usuario

| Usuario | Portal Administrador | App mobile Comunidad | App mobile Operacion | Backoffice |
|---|---:|---:|---:|---:|
| `project_manager` | Si | Solo si tiene rol mobile `vecino` o `comite` | Solo si tiene rol mobile `supervisor` o `conserje` | No, salvo que pertenezca a Komite |
| `supervisor` | Si | Solo si tiene rol mobile `vecino` o `comite` | Solo si tiene rol mobile `supervisor` o `conserje` | No, salvo que pertenezca a Komite |
| `ejecutivo` | Si | Solo si tiene rol mobile `vecino` o `comite` | Solo si tiene rol mobile `supervisor` o `conserje` | No, salvo que pertenezca a Komite |
| `vecino` | No por rol mobile | Si | No | No |
| `comite` | No por rol mobile | Si | No | No |
| `supervisor` | No por rol mobile | No | Si | No |
| `conserje` | No por rol mobile | No | Si | No |
| Empleado Komite activo | No necesariamente | Solo si tiene accesos mobile | Solo si tiene accesos mobile | Si |

## Configuracion recomendada para pruebas

### Usuario de operacion

```text
Usuario: antoniomanuelvergara@gmail.com
Empresa: Administradora cliente
Perfil Portal Administrador: project_manager, supervisor o ejecutivo, si debe entrar al portal
Accesos mobile:
  - Todos / supervisor / Sin unidad
```

Resultado:

```text
Portal Administrador:
  -> Entra si tiene perfil.

App mobile:
  -> Modo Operacion
  -> Puede elegir entre condominios activos de su empresa.
```

### Usuario de comunidad

```text
Usuario: claudiafuentescabrera@gmail.com
Empresa: Administradora cliente
Perfil Portal Administrador: Sin perfil
Accesos mobile:
  - Condominio de prueba / vecino / Unidad correspondiente
```

Resultado:

```text
App mobile:
  -> Modo Comunidad
  -> Condominio y unidad asignados.
```

### Usuario de comite

```text
Usuario: miembrocomite@demo.cl
Empresa: Administradora cliente
Perfil Portal Administrador: Sin perfil
Accesos mobile:
  - Condominio de prueba / comite / Sin unidad
```

Resultado:

```text
App mobile:
  -> Modo Comunidad
  -> Vista de comite.
```

### Usuario interno Komite

```text
Usuario: admin@komite.cl
Empresa: Komite
Estado: active
Perfil Portal Administrador: opcional
Accesos mobile: opcional
```

Resultado:

```text
Backoffice:
  -> Puede entrar.
```

## Reglas finales

- No existe rol global.
- El Portal Administrador usa `company_profile`: `project_manager`, `supervisor` o `ejecutivo`.
- La app mobile usa roles por condominio: `vecino`, `comite`, `supervisor`, `conserje`.
- Comunidad se decide por `vecino` y `comite`.
- Operacion se decide por `supervisor` y `conserje`.
- `Todos` equivale a todos los condominios activos de la empresa del usuario.
- `Todos` se guarda con `condominium_id = null`.
- `Todos` no permite unidad.
- Un usuario puede tener varios accesos y por tanto ver selector de modo.
- El backoffice interno es solo para usuarios activos de la empresa `Komite`.
- El Portal Administrador no debe mostrar duplicado un condominio aunque el usuario tenga doble rol sobre el mismo.

