<script setup lang="ts">
defineProps<{
  view: string;
}>();

const tools = [
  {
    title: "Procesar audio",
    icon: "mic",
    status: "Preparado",
    copy: "Transcribir audios de terreno y convertirlos en borradores de incidencia, tarea, informe o comunicado.",
  },
  {
    title: "Importar planillas",
    icon: "table",
    status: "Preparado",
    copy: "Cargar planillas de novedades, unidades, mantenciones o pendientes para normalizarlas antes de trabajarlas.",
  },
  {
    title: "Resumen mensual",
    icon: "spark",
    status: "Preparado",
    copy: "Agrupar incidencias, tareas, mantenciones e inspecciones para preparar informes de gestion revisables.",
  },
];
</script>

<template>
  <section class="panel placeholder-panel">
    <p class="eyebrow">Herramientas</p>
    <h2>Centro de apoyo para la administradora</h2>
    <p class="placeholder-copy">
      Funciones pensadas para reducir trabajo repetitivo del equipo del cliente: procesar informacion, ordenar evidencias y preparar borradores antes de publicar o enviar.
    </p>

    <div class="tool-grid" style="margin-top: 18px">
      <article v-for="tool in tools" :key="tool.title" class="tool-card">
        <span class="tool-icon">
          <svg class="icon" aria-hidden="true"><use :href="`#icon-${tool.icon}`" /></svg>
        </span>
        <div>
          <h3>{{ tool.title }}</h3>
          <p class="card-copy">{{ tool.copy }}</p>
        </div>
        <span class="status-pill">{{ tool.status }}</span>
      </article>
    </div>
  </section>
</template>
