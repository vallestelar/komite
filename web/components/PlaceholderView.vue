<script setup lang="ts">
const props = defineProps<{
  title: string;
  view: string;
}>();

const copy = computed(() => {
  const messages: Record<string, string> = {
    neighbors: "Gestión de vecinos, unidades, contactos y relaciones con comunidades para uso operativo y comunicacional.",
    committee: "Gestión de miembros del comité, cargos, periodos y contactos relevantes por comunidad.",
    incidents: "Gestión de incidencias reportadas por terreno, administradores o canales habilitados, con estado, prioridad y responsable.",
    tasks: "Seguimiento del trabajo asignado al equipo operativo de la administradora y a responsables por condominio.",
    inspections: "Inspecciones y checklists para supervisores, con observaciones, evidencias y resultado operativo.",
    files: "Repositorio de fotos, audios, documentos y respaldos asociados a incidencias, tareas, inspecciones e informes.",
    reports: "Borradores, revisión y publicación de informes para comités o comunidades según corresponda.",
    communications: "Comunicados preparados por la administradora para enviar o publicar a destinatarios aprobados.",
    audio: "Transcripción de audios de terreno para convertirlos en borradores de incidencias, tareas, informes o comunicados.",
    support: "Canal para crear tickets hacia Komite por dudas, problemas, solicitudes de soporte o necesidades de configuración.",
  };

  return messages[props.view] || "Esta opción está preparada en el menú y se implementará en una siguiente iteración.";
});
</script>

<template>
  <section class="panel placeholder-panel">
    <p class="eyebrow">Módulo preparado</p>
    <h2>{{ title }}</h2>
    <p class="placeholder-copy">{{ copy }}</p>
  </section>
</template>
