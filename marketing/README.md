# Komite Marketing

Landing publica de Komite. Es un sitio estatico compuesto por un HTML
autocontenido, assets y fuentes locales, servido en produccion con Nginx dentro
de Docker.

## Estructura

```text
marketing/
  index.html
  assets/
    komite-logo.png
    logo.png
    interactions.js
    fonts/
  Dockerfile
```

## Abrir en local sin servidor

Puedes abrir directamente este archivo en el navegador:

```text
marketing/index.html
```

Esto sirve para revisar cambios simples de contenido y estilos.

## Levantar con servidor local

Desde la raiz del repositorio:

```powershell
python -m http.server 3002 --directory marketing
```

Luego abre:

```text
http://localhost:3002
```

Si no tienes `python` disponible en Windows, prueba:

```powershell
py -m http.server 3002 --directory marketing
```

## Levantar con Docker

Desde la raiz del repositorio:

```powershell
docker compose up -d --build marketing
```

La landing queda disponible en:

```text
http://localhost:3001
```

Ver logs:

```powershell
docker compose logs -f marketing
```

Detener solo marketing:

```powershell
docker compose stop marketing
```

## Editar contenido

- Texto y secciones: `index.html`.
- Colores, layout y responsive: estilos embebidos en `index.html`.
- Movimiento e interacciones: `assets/interactions.js`.
- Imagenes y logos: `assets/`.

Despues de cambiar archivos, refresca el navegador. Si estas usando Docker y
no ves los cambios, reconstruye el servicio:

```powershell
docker compose up -d --build marketing
```
