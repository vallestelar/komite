# Prompt para crear presentacion PowerPoint: Actores, aplicaciones y roles de Komite

Quiero que generes una presentacion PowerPoint profesional, clara y visual sobre el ecosistema de Komite. La presentacion debe explicar los actores que intervienen en la aplicacion, las distintas superficies del producto y los tipos de usuarios/roles, indicando quien usa cada cosa y que informacion puede ver.

## Contexto general

Komite es una plataforma para mejorar la gestion, comunicacion y trazabilidad en comunidades residenciales administradas por empresas administradoras. El sistema conecta a Komite como proveedor SaaS, a las empresas administradoras, a sus equipos internos, a supervisores/conserjes, al comite de administracion y a vecinos.

El objetivo de la presentacion es que una persona externa pueda entender rapidamente:

- Que aplicaciones o canales tiene Komite.
- Que actor usa cada canal.
- Que permisos o roles existen.
- Que ve cada tipo de usuario.
- Como se separa el uso comercial, operativo, mobile e interno.

## Estilo de la presentacion

- Tono: profesional, claro, ejecutivo y comercial.
- Audiencia: socios, potenciales clientes, equipo interno y stakeholders tecnicos.
- Estilo visual: moderno, sobrio, limpio, con iconos por actor y canal.
- Evitar tecnicismos excesivos.
- Usar diagramas simples, tablas comparativas y bullets breves.
- Usar colores de marca Komite: azul corporativo, naranja de acento y fondos claros.

## Estructura sugerida de slides

### Slide 1: Titulo

Titulo: Ecosistema Komite: actores, canales y roles

Subtitulo: Plataforma SaaS para administracion, comunicacion y gestion operativa de comunidades.

### Slide 2: Vision general del ecosistema

Mostrar un mapa simple con cuatro superficies principales:

1. Web comercial
2. Portal Administrador, o web app administrativa
3. App mobile
4. Backoffice interno Komite

Explicar que todas se conectan con una API central y una base de datos multi-tenant donde cada empresa cliente conserva sus datos separados por tenant.

### Slide 3: Web comercial

Explicar:

- Es la web publica de Komite.
- Su objetivo es presentar el producto, propuesta de valor, beneficios, funcionalidades y contacto comercial.
- La usan potenciales clientes, empresas administradoras interesadas, inversionistas o partners.
- No requiere login.
- No muestra datos operativos ni informacion interna de comunidades.

Actores:

- Visitante publico
- Potencial cliente
- Empresa administradora interesada

Uso principal:

- Conocer Komite.
- Solicitar informacion.
- Entender beneficios.
- Captar leads comerciales.

### Slide 4: Portal Administrador / Web app administrativa

Explicar:

- Es la aplicacion web privada para la empresa administradora cliente.
- La usan perfiles de oficina o gestion interna de la administradora.
- Permite trabajar sobre la cartera de condominios que gestiona esa empresa.
- Esta orientada a operacion, tareas, tickets, consultas, informes y seguimiento.

Actores:

- Project manager
- Ejecutivo/a
- Equipo administrativo de la empresa administradora

Uso principal:

- Gestionar operacion diaria.
- Consultar condominios asociados.
- Revisar tareas y tickets.
- Coordinar supervisores o acciones internas.
- Dar seguimiento a solicitudes y comunicaciones.

Importante:

- El Portal Administrador no es el backoffice interno de Komite.
- Cada empresa administradora solo debe ver sus propios datos.

### Slide 5: App mobile

Explicar:

- Es la aplicacion movil para la interaccion directa con la comunidad y la operacion en terreno.
- Puede ser usada por vecinos, miembros del comite, supervisores y conserjes.
- El acceso se organiza por condominio.
- Un usuario puede tener acceso a uno o varios condominios.
- Tambien puede existir acceso a "Todos" los condominios de su empresa si corresponde.

Actores:

- Vecino
- Comite
- Supervisor
- Conserje

Uso principal por tipo:

- Vecino: consultar informacion de su comunidad, recibir comunicaciones, reportar o seguir incidencias segun alcance.
- Comite: ver informacion relevante de la comunidad, participar en seguimiento y comunicacion con mayor visibilidad que un vecino.
- Supervisor: gestionar operacion en terreno, revisar tareas, incidencias, inspecciones o estados operativos.
- Conserje: registrar novedades, incidencias o eventos operativos desde terreno.

### Slide 6: Backoffice interno Komite

Explicar:

- Es la herramienta interna de Komite como proveedor SaaS.
- No es para empresas administradoras clientes.
- Sirve para administrar la plataforma, clientes, tenants, configuraciones y soporte.
- Solo pueden entrar usuarios activos que pertenecen a la empresa Komite.

Actores:

- Equipo interno Komite
- Administracion SaaS
- Soporte Komite
- Operacion interna Komite

Uso principal:

- Crear y gestionar empresas clientes.
- Crear y gestionar usuarios.
- Gestionar condominios de clientes si hace falta.
- Revisar tickets de soporte.
- Configurar bancos y catalogos globales.
- Supervisar actividad, auditoria y parametros generales.

### Slide 7: Resumen de canales y usuarios

Crear una tabla con columnas:

- Canal
- Usuario principal
- Requiere login
- Que ve
- Para que se usa

Contenido esperado:

| Canal | Usuario principal | Login | Que ve | Uso |
| --- | --- | --- | --- | --- |
| Web comercial | Visitantes y potenciales clientes | No | Informacion publica | Captacion y presentacion |
| Portal Administrador | Project manager y Ejecutivo/a | Si | Datos de su empresa/tenant | Gestion operativa |
| App mobile | Vecino, Comite, Supervisor, Conserje | Si | Condominios asignados | Comunidad y terreno |
| Backoffice Komite | Equipo Komite | Si | Todos los tenants segun administracion interna | Gestion SaaS |

### Slide 8: Tipos de usuario

Explicar los tipos de usuario desde el punto de vista funcional:

1. Usuario publico
   - No tiene cuenta.
   - Solo usa la web comercial.

2. Usuario de empresa administradora
   - Pertenece a una empresa cliente.
   - Puede entrar al Portal Administrador si tiene perfil habilitado.
   - Puede tener accesos mobile si tambien trabaja con condominios.

3. Usuario de comunidad
   - Accede principalmente desde app mobile.
   - Su visibilidad depende del condominio y rol asignado.

4. Usuario interno Komite
   - Pertenece a la empresa Komite.
   - Puede entrar al backoffice.
   - Gestiona configuracion, clientes y soporte de la plataforma.

### Slide 9: Perfiles del Portal Administrador

Explicar que el Portal Administrador usa perfiles simples:

1. Project manager
   - Perfil de gestion y coordinacion.
   - Supervisa operacion de la empresa administradora.
   - Puede coordinar tareas, revisar seguimiento, consultar indicadores y tener una vision mas global.

2. Ejecutivo/a
   - Perfil operativo administrativo.
   - Gestiona consultas, tareas, tickets y seguimiento diario.
   - Trabaja sobre la cartera de condominios de la empresa.

Importante:

- Estos perfiles aplican a la web app administrativa.
- No son roles de comunidad.
- No deben confundirse con los roles mobile.

### Slide 10: Roles de app mobile

Explicar que los roles mobile son por condominio y definen que experiencia ve el usuario en la app.

Roles:

1. Vecino
   - Usuario residente o propietario.
   - Ve informacion y servicios asociados a su comunidad/unidad.

2. Comite
   - Miembro del comite de administracion.
   - Tiene mayor visibilidad sobre temas comunitarios.
   - Participa en seguimiento y comunicacion con la administradora.

3. Supervisor
   - Pertenece a la empresa administradora.
   - Usa la app para operacion en terreno y seguimiento.
   - Puede acceder a varios condominios o a todos los asignados a su empresa.

4. Conserje
   - Usuario operativo de terreno o conserjeria.
   - Registra eventos, novedades o incidencias segun alcance definido.

### Slide 11: Matriz de visibilidad por usuario

Crear una matriz visual:

| Usuario | Web comercial | Portal Administrador | App mobile | Backoffice |
| --- | --- | --- | --- | --- |
| Visitante publico | Si | No | No | No |
| Project manager | Opcional | Si | Si, si tiene accesos mobile | No |
| Ejecutivo/a | Opcional | Si | Si, si tiene accesos mobile | No |
| Vecino | Opcional | No | Si | No |
| Comite | Opcional | No | Si | No |
| Supervisor | Opcional | No o segun perfil portal | Si | No |
| Conserje | Opcional | No | Si | No |
| Equipo Komite | Si | No como cliente | Opcional para pruebas | Si |

Notas:

- El Backoffice queda reservado a empleados de Komite.
- El Portal Administrador queda reservado a usuarios de la empresa administradora con perfil `project_manager`, `supervisor` o `ejecutivo`.
- La App mobile depende de accesos por condominio.

### Slide 12: Separacion de datos por tenant

Explicar:

- Cada empresa administradora es un tenant.
- Los datos operativos se asocian a una empresa.
- Los condominios pertenecen a una empresa.
- Los usuarios de una empresa solo deben ver datos de su tenant.
- Komite, desde el backoffice interno, puede administrar clientes y soporte a nivel plataforma.

Incluir un diagrama:

Komite SaaS
-> Empresa administradora A
   -> Condominios A1, A2, A3
   -> Usuarios A
-> Empresa administradora B
   -> Condominios B1, B2
   -> Usuarios B

### Slide 13: Flujo de acceso simplificado

Mostrar un flujo:

1. Usuario inicia sesion.
2. API valida credenciales y empresa.
3. Si es Portal Administrador, revisa perfil `project_manager`, `supervisor` o `ejecutivo`.
4. Si es mobile, carga condominios asignados.
5. Si tiene acceso a "Todos", se expanden los condominios activos de su empresa.
6. El usuario elige condominio cuando corresponde.
7. La aplicacion muestra solo lo que ese usuario puede ver.

### Slide 14: Mensaje clave

Resumen:

- Komite separa claramente cuatro mundos: comercial, administracion cliente, mobile comunitario/terreno y backoffice interno.
- Los roles se mantienen simples para reducir errores de permisos.
- El Portal Administrador se centra en Project manager y Ejecutivo/a.
- La App mobile se centra en Vecino, Comite, Supervisor y Conserje.
- El Backoffice es solo para empleados Komite.
- La arquitectura multi-tenant permite que varias empresas usen la misma plataforma sin mezclar datos.

### Slide 15: Cierre

Titulo: Komite organiza la operacion comunitaria sin mezclar responsabilidades

Mensaje final:

Una plataforma con canales separados, roles claros y visibilidad controlada para que cada actor vea solo lo que necesita.

## Requisitos de entrega

Genera una presentacion PowerPoint con:

- Entre 12 y 15 slides.
- Titulos claros.
- Iconos para cada actor y canal.
- Una matriz de visibilidad.
- Un diagrama de ecosistema.
- Un diagrama simple de flujo de acceso.
- Texto breve por slide, evitando parrafos largos.
- Estilo visual corporativo, moderno y facil de explicar en reunion.

