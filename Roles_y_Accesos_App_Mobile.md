# Roles y accesos en la app mobile Komite

Este documento explica como configurar usuarios para la app mobile y que vera cada usuario al iniciar sesion segun su rol global y sus accesos a condominios.

## Conceptos base

La app mobile trabaja con tres niveles:

```text
Tenant / Compania
  -> Modo de uso
      -> Condominio activo
          -> Unidad, si aplica
```

El tenant sale de la compania asignada al usuario (`users.company_id`). Despues del login, la app revisa los accesos del usuario en `user_condominiums` y decide que flujo mostrar.

## Rol global

El rol global vive en `users.global_role`. Sirve para permisos generales del sistema, pero en la app mobile actual no reemplaza los accesos a condominios.

Valores disponibles en el backoffice:

| Rol global | Uso esperado | Efecto actual en app mobile |
|---|---|---|
| Sin rol global | Usuario normal | La app decide solo por sus accesos a condominios. |
| `superadmin` | Administracion global del sistema | Puede habilitar modo Operacion sobre los condominios donde el usuario tenga acceso. Si no tiene accesos a condominios, no hay contexto mobile util. |
| `admin` | Administracion general | Actualmente no cambia el modo mobile por si solo. |
| `operator` | Operador general | Actualmente no cambia el modo mobile por si solo. |
| `viewer` | Lector general | Actualmente no cambia el modo mobile por si solo. |

Regla practica: para que la app mobile tenga un contexto concreto, el usuario debe tener al menos un acceso en "Accesos a condominios".

## Accesos a condominios

Cada acceso se configura con:

```text
Condominio
Rol
Unidad opcional
```

La app clasifica los roles por `role_code`.

### Roles de Comunidad

Estos roles llevan al modo Comunidad:

```text
vecino
comite
```

Uso esperado:

- `vecino`: residente asociado a una unidad.
- `comite`: miembro del comite; puede tener unidad o no.

### Roles de Operacion

Estos roles llevan al modo Operacion:

```text
administrador_empresa
administrador_condominio
supervisor
conserje
superadmin
```

Uso esperado:

- `supervisor`: usuario de terreno que gestiona inspecciones, tareas y reportes.
- `conserje`: usuario operativo del condominio.
- `administrador_condominio`: gestiona un condominio.
- `administrador_empresa`: gestiona condominios de la empresa, pero por ahora debe tener accesos asignados por condominio.
- `superadmin`: acceso operativo amplio, condicionado a tener contexto de condominio en mobile.

## Unidad

La unidad apunta a la tabla `units`. Sirve para vincular a un usuario con un departamento, casa, oficina o local dentro del condominio.

Ejemplo:

```text
Usuario: Claudia Fuentes
Condominio: Edificio Los Alerces
Rol: vecino
Unidad: 1204
```

Para roles operativos normalmente se deja sin unidad:

```text
Usuario: Antonio Vergara
Condominio: Edificio Los Alerces
Rol: supervisor
Unidad: Sin unidad
```

## Flujo despues del login

La app decide asi:

```text
Login correcto
  -> Lee company y condominiums desde la API
  -> Clasifica accesos por role_code
  -> Si tiene Comunidad y Operacion: muestra selector de modo
  -> Si solo tiene Comunidad:
       - 1 comunidad: entra directo
       - varias comunidades: muestra selector de comunidad
  -> Si solo tiene Operacion:
       - muestra selector de condominio operativo
```

## Casos de configuracion

### Caso 1: vecino con una sola comunidad

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / vecino / Unidad 1204
```

Resultado en app:

```text
Login
  -> Entra directo a modo Comunidad
  -> Condominio activo: Los Alerces / Unidad 1204
```

Veria el menu Comunidad:

```text
Inicio
Avisos
Incidencias
Documentos
Mas
```

### Caso 2: vecino con varias comunidades

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / vecino / Unidad 1204
  - Condominio Las Palmas / vecino / Unidad 804
```

Resultado en app:

```text
Login
  -> Selector de comunidad
      - Los Alerces / Unidad 1204
      - Las Palmas / Unidad 804
  -> Entra a modo Comunidad con la comunidad elegida
```

### Caso 3: miembro de comite

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / comite / Sin unidad
```

Resultado en app:

```text
Login
  -> Entra directo a modo Comunidad
  -> Condominio activo: Los Alerces
```

Veria informacion comunitaria del condominio, no herramientas operativas de terreno.

### Caso 4: supervisor operativo con un condominio

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / supervisor / Sin unidad
```

Resultado en app:

```text
Login
  -> Selector de condominio operativo
      - Los Alerces
  -> Entra a modo Operacion
```

Veria el menu Operacion:

```text
Panel
Tareas
Inspecciones
Reportar
Mas
```

### Caso 5: supervisor operativo con varios condominios

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / supervisor / Sin unidad
  - Condominio Las Palmas / supervisor / Sin unidad
```

Resultado en app:

```text
Login
  -> Selector de condominio operativo
      - Los Alerces
      - Las Palmas
  -> Entra a modo Operacion con el condominio elegido
```

Todas las pantallas operativas usan el condominio activo.

### Caso 6: usuario con Comunidad y Operacion

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / vecino / Unidad 1204
  - Condominio Los Alerces / supervisor / Sin unidad
```

Resultado en app:

```text
Login
  -> Selector de modo
      - Comunidad
      - Operacion
```

Si elige Comunidad:

```text
Condominio activo: Los Alerces / Unidad 1204
Menu: Comunidad
```

Si elige Operacion:

```text
Selector de condominio operativo
  -> Los Alerces
Menu: Operacion
```

### Caso 7: usuario de comite y supervisor en distintos condominios

Configuracion:

```text
Rol global: sin rol global
Accesos:
  - Condominio Los Alerces / comite / Sin unidad
  - Condominio Las Palmas / supervisor / Sin unidad
```

Resultado en app:

```text
Login
  -> Selector de modo
      - Comunidad
      - Operacion
```

Si elige Comunidad, trabaja sobre Los Alerces. Si elige Operacion, trabaja sobre Las Palmas.

### Caso 8: superadmin sin accesos a condominios

Configuracion:

```text
Rol global: superadmin
Accesos:
  - Ninguno
```

Resultado actual en app:

```text
Login
  -> No hay condominios disponibles para Comunidad ni Operacion
```

Este usuario puede ser valido para backoffice, pero no tiene contexto suficiente para la app mobile actual.

Recomendacion: asignar al menos un acceso de condominio si debe usar la app mobile.

### Caso 9: superadmin con acceso a un condominio

Configuracion:

```text
Rol global: superadmin
Accesos:
  - Condominio Los Alerces / vecino / Unidad 1204
```

Resultado actual en app:

```text
Login
  -> Selector de modo
      - Comunidad
      - Operacion
```

Por que ocurre: el acceso `vecino` habilita Comunidad, y el rol global `superadmin` habilita Operacion sobre los condominios donde el usuario ya tiene acceso.

### Caso 10: administrador de empresa

Configuracion recomendada actual:

```text
Rol global: admin o sin rol global
Accesos:
  - Condominio Los Alerces / administrador_empresa / Sin unidad
  - Condominio Las Palmas / administrador_empresa / Sin unidad
```

Resultado en app:

```text
Login
  -> Selector de condominio operativo
      - Los Alerces
      - Las Palmas
  -> Menu Operacion
```

Nota: aunque conceptualmente `administrador_empresa` podria operar todos los condominios del tenant, en la implementacion actual hay que asignarle accesos por condominio para que aparezcan en la app mobile.

## Configuracion recomendada para pruebas

### Antonio: Operacion

```text
Usuario: antoniomanuelvergara@gmail.com
Rol global: sin rol global
Accesos:
  - Condominio de prueba / supervisor / Sin unidad
```

Resultado:

```text
Login
  -> Selector de condominio operativo
  -> Modo Operacion
```

### Claudia: Comunidad

```text
Usuario: claudiafuentescabrera@gmail.com
Rol global: sin rol global
Accesos:
  - Condominio de prueba / vecino / Unidad correspondiente
```

Resultado:

```text
Login
  -> Modo Comunidad
```

Si Claudia no tiene unidad creada, se puede dejar "Sin unidad" temporalmente, pero para un caso real de vecino conviene crear/asignar la unidad.

## Reglas finales

- El rol global no sustituye los accesos a condominios.
- Comunidad se decide por roles `vecino` y `comite`.
- Operacion se decide por roles `administrador_empresa`, `administrador_condominio`, `supervisor`, `conserje`, `superadmin`.
- Un usuario puede tener varios accesos y por tanto ver selector de modo.
- La unidad solo aplica cuando necesitamos vincular al usuario a una vivienda/local concreto.
- Para operar varios condominios, se deben crear varios accesos operativos.
