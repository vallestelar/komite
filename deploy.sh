#!/bin/bash

set -e

cd /opt/komite

echo "Actualizando codigo desde GitHub..."
git pull origin main

echo "Reconstruyendo y levantando contenedores..."
docker compose up -d --build

echo "Ejecutando migraciones Aerich..."
docker compose exec -T api aerich upgrade || echo "No se ejecutaron migraciones o no habia cambios."

echo "Limpiando imagenes antiguas..."
docker image prune -f

echo "Estado de contenedores:"
docker compose ps

echo "Deploy finalizado."
