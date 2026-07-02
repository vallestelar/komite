<script setup lang="ts">
const props = defineProps<{
  title: string;
  view: string;
}>();

const copy = computed(() => {
  const messages: Record<string, string> = {
    condominiums: "Cartera de condominios que gestiona la empresa cliente, con responsables, estado operativo y datos clave por comunidad.",
    maintenance: "Planificacion y seguimiento de mantenciones preventivas, correctivas y compromisos recurrentes por condominio.",
    history: "Linea de tiempo consultable con incidencias, tareas, inspecciones, informes y comunicaciones relevantes.",
    incidents: "Gestion de incidencias reportadas por terreno, administradores o canales habilitados, con estado, prioridad y responsable.",
    tasks: "Seguimiento del trabajo asignado al equipo operativo de la administradora y a responsables por condominio.",
    inspections: "Inspecciones y checklists para supervisores, con observaciones, evidencias y resultado operativo.",
    evidence: "Repositorio de fotos, audios, documentos y respaldos asociados a incidencias, tareas e informes.",
    reports: "Borradores, revision y publicacion de informes para comites o comunidades segun corresponda.",
    communications: "Comunicados preparados por la administradora para enviar o publicar a destinatarios aprobados.",
    recipients: "Directorio de destinatarios de comunicacion: comites, contactos clave y segmentos comunitarios, sin darles acceso a este portal.",
    "publication-rules": "Reglas que definen que informacion puede publicarse, a quien se envia y que requiere aprobacion previa.",
    team: "Usuarios internos de la empresa administradora que trabajan en la cartera: administradores, project managers y supervisores.",
    accesses: "Accesos operativos de usuarios del cliente por condominio y responsabilidad.",
    settings: "Preferencias propias de la empresa administradora dentro de Komite, no configuracion global de la plataforma.",
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
