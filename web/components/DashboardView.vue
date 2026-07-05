<script setup lang="ts">
const emit = defineEmits<{
  openView: [view: string];
}>();

const { request } = useApi();
const { activeCondominium } = useAuth();

const metrics = reactive({
  incidents: 0,
  tasks: 0,
  reports: 0,
});

const lists = reactive({
  incidents: [] as Array<Record<string, unknown>>,
  tasks: [] as Array<Record<string, unknown>>,
  communications: [] as Array<Record<string, unknown>>,
  ai: [] as Array<Record<string, unknown>>,
});

const loading = ref(true);

const fetchPage = async (path: string) => {
  try {
    const data = await request<{ items?: Array<Record<string, unknown>>; meta?: { total?: number } }>(path);
    return {
      items: data.items || [],
      total: data.meta?.total || data.items?.length || 0,
    };
  } catch {
    return { items: [], total: 0 };
  }
};

const loadDashboard = async () => {
  loading.value = true;
  const [incidents, tasks, reports, communications, ai] = await Promise.all([
    fetchPage("/api/v1/incidents/?page=1&page_size=5"),
    fetchPage("/api/v1/tasks/?page=1&page_size=5"),
    fetchPage("/api/v1/reports/?page=1&page_size=5"),
    fetchPage("/api/v1/communications/?page=1&page_size=5"),
    fetchPage("/api/v1/ai-requests/?page=1&page_size=5"),
  ]);

  metrics.incidents = incidents.total;
  metrics.tasks = tasks.total;
  metrics.reports = reports.total;
  lists.incidents = incidents.items;
  lists.tasks = tasks.items;
  lists.communications = communications.items;
  lists.ai = ai.items;
  loading.value = false;
};

onMounted(loadDashboard);

const textValue = (item: Record<string, unknown>, key: string, fallback = "") => String(item[key] || fallback);
</script>

<template>
  <section class="panel">
    <div class="dashboard-hero">
      <div>
        <p class="eyebrow">Resumen operativo</p>
        <h2>Estado general de la cartera</h2>
        <p class="hero-copy">Vista de trabajo para administradores y project managers de la empresa administradora: pendientes, actividad reciente, informes y comunicaciones por condominio.</p>
      </div>
      <div class="hero-actions">
        <button class="button orange" type="button" @click="emit('openView', 'incidents')">
          <svg class="icon" aria-hidden="true"><use href="#icon-alert" /></svg>
          <span>Ver incidencias</span>
        </button>
        <button class="button ghost" type="button" @click="emit('openView', 'tools')">
          <svg class="icon" aria-hidden="true"><use href="#icon-tool" /></svg>
          <span>Herramientas</span>
        </button>
      </div>
    </div>

    <div class="metrics-grid" aria-busy="loading">
      <article class="metric"><span>Condominio activo</span><strong class="metric-name">{{ activeCondominium?.name || "Sin contexto" }}</strong><small>Contexto de consulta actual</small></article>
      <article class="metric"><span>Incidencias</span><strong>{{ metrics.incidents }}</strong><small>Registros operativos</small></article>
      <article class="metric"><span>Tareas</span><strong>{{ metrics.tasks }}</strong><small>Trabajo del equipo</small></article>
      <article class="metric"><span>Informes</span><strong>{{ metrics.reports }}</strong><small>Borradores y publicados</small></article>
    </div>

    <div class="dashboard-grid">
      <section>
        <h2>Incidencias recientes</h2>
        <div class="list">
          <div v-if="!lists.incidents.length" class="list-item"><span>Sin registros.</span></div>
          <div v-for="item in lists.incidents" :key="String(item.id)" class="list-item">
            <strong>{{ textValue(item, 'category', 'Registro') }}</strong>
            <span>{{ textValue(item, 'status') }}</span>
          </div>
        </div>
      </section>
      <section>
        <h2>Tareas recientes</h2>
        <div class="list">
          <div v-if="!lists.tasks.length" class="list-item"><span>Sin registros.</span></div>
          <div v-for="item in lists.tasks" :key="String(item.id)" class="list-item">
            <strong>{{ textValue(item, 'title', 'Registro') }}</strong>
            <span>{{ textValue(item, 'status') }}</span>
          </div>
        </div>
      </section>
      <section>
        <h2>Comunicaciones recientes</h2>
        <div class="list">
          <div v-if="!lists.communications.length" class="list-item"><span>Sin registros.</span></div>
          <div v-for="item in lists.communications" :key="String(item.id)" class="list-item">
            <strong>{{ textValue(item, 'title', 'Registro') }}</strong>
            <span>{{ textValue(item, 'status') }}</span>
          </div>
        </div>
      </section>
      <section>
        <h2>Procesos IA recientes</h2>
        <div class="list">
          <div v-if="!lists.ai.length" class="list-item"><span>Sin registros.</span></div>
          <div v-for="item in lists.ai" :key="String(item.id)" class="list-item">
            <strong>{{ textValue(item, 'purpose', 'Registro') }}</strong>
            <span>{{ textValue(item, 'status') }}</span>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>
