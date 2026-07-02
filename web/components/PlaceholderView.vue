<script setup lang="ts">
const props = defineProps<{
  title: string;
  view: string;
}>();

const copy = computed(() => {
  const messages: Record<string, string> = {
    audio: "Aqui se integrara el flujo de procesamiento de audio con IA desde el nuevo front Nuxt.",
    condominiums: "Listado y formularios de condominios se migraran desde el backoffice actual.",
    incidents: "Gestion de incidencias preparada para conectarse a los endpoints operativos.",
    tasks: "Seguimiento de tareas preparado para las ejecutivas y administracion.",
    inspections: "Modulo reservado para inspecciones y plantillas de revision.",
    reports: "Modulo reservado para informes, borradores y publicaciones.",
    communications: "Modulo reservado para comunicaciones hacia comite y vecinos.",
    committee: "Modulo reservado para miembros del comite, cargos y vigencias.",
    neighbors: "Modulo reservado para vecinos, unidades y datos de contacto.",
    companies: "Modulo reservado para empresas administradoras.",
    users: "Modulo reservado para usuarios, roles y accesos por condominio.",
    roles: "Modulo reservado para permisos y perfiles de uso.",
    settings: "Modulo reservado para parametros, integraciones y reglas operativas.",
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
