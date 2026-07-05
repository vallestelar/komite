<script setup lang="ts">
const props = defineProps<{
  title: string;
  view: string;
}>();

const copy = computed(() => {
  const messages: Record<string, string> = {
    neighbors: "Gestion de vecinos, unidades, contactos y relaciones con comunidades para uso operativo y comunicacional.",
    committee: "Gestion de miembros del comite, cargos, periodos y contactos relevantes por comunidad.",
    incidents: "Gestion de incidencias reportadas por terreno, administradores o canales habilitados, con estado, prioridad y responsable.",
    tasks: "Seguimiento del trabajo asignado al equipo operativo de la administradora y a responsables por condominio.",
    inspections: "Inspecciones y checklists para supervisores, con observaciones, evidencias y resultado operativo.",
    files: "Repositorio de fotos, audios, documentos y respaldos asociados a incidencias, tareas, inspecciones e informes.",
    reports: "Borradores, revision y publicacion de informes para comites o comunidades segun corresponda.",
    communications: "Comunicados preparados por la administradora para enviar o publicar a destinatarios aprobados.",
    audio: "Transcripcion de audios de terreno para convertirlos en borradores de incidencias, tareas, informes o comunicados.",
    support: "Canal para crear tickets hacia Komite por dudas, problemas, solicitudes de soporte o necesidades de configuracion.",
  };

  return messages[props.view] || "Esta opcion esta preparada en el menu y se implementara en una siguiente iteracion.";
});
</script>

<template>
  <section class="panel placeholder-panel">
    <p class="eyebrow">Modulo preparado</p>
    <h2>{{ title }}</h2>
    <p class="placeholder-copy">{{ copy }}</p>
  </section>
</template>
