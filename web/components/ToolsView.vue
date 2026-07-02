<script setup lang="ts">
defineProps<{
  view: string;
}>();

const tools = [
  {
    title: "Procesamiento de datos",
    icon: "spark",
    status: "Preparado",
    copy: "Base para automatizar limpieza, clasificacion y transformacion de datos operativos.",
  },
  {
    title: "Planillas",
    icon: "table",
    status: "Preparado",
    copy: "Espacio reservado para cargar, validar y normalizar archivos de trabajo de las ejecutivas.",
  },
  {
    title: "Audio IA",
    icon: "mic",
    status: "Conectable",
    copy: "Acceso futuro a transcripcion y generacion de borradores desde audios de terreno.",
  },
];
</script>

<template>
  <section class="panel placeholder-panel">
    <p class="eyebrow">Herramientas</p>
    <h2>Centro de apoyo operativo</h2>
    <p class="placeholder-copy">
      Este apartado queda listo para sumar funcionalidades que faciliten procesamiento de datos, revision de archivos y tareas repetitivas.
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
