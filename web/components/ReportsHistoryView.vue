<script setup lang="ts">
type ReportHistoryItem = {
  id: string;
  source: string;
  source_label: string;
  title: string;
  status: string;
  status_label: string;
  category: string;
  category_label: string;
  issued_at?: string | null;
  created_at?: string | null;
  format?: string | null;
  summary?: string | null;
  metadata?: Record<string, unknown>;
};

type HistoryResponse = {
  items?: ReportHistoryItem[];
  meta?: { total?: number; page?: number; page_size?: number; pages?: number };
  summary?: { total?: number; reports?: number; certificates?: number; communications?: number };
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const items = ref<ReportHistoryItem[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const search = ref("");
const sourceFilter = ref("");
const statusFilter = ref("");
const page = ref(1);
const pageSize = 20;
const meta = reactive({ total: 0, page: 1, page_size: pageSize, pages: 1 });
const summary = reactive({ total: 0, reports: 0, certificates: 0, communications: 0 });

let searchTimer: ReturnType<typeof setTimeout> | null = null;

const statusOptions = computed(() => {
  const values = new Map<string, string>();
  items.value.forEach((item) => values.set(item.status, item.status_label));
  return Array.from(values.entries()).sort((left, right) => left[1].localeCompare(right[1]));
});

const loadHistory = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams({
      page: String(page.value),
      page_size: String(pageSize),
    });
    if (search.value.trim()) params.set("q", search.value.trim());
    if (sourceFilter.value) params.set("source", sourceFilter.value);
    if (statusFilter.value) params.set("status", statusFilter.value);
    const data = await request<HistoryResponse>(`/api/v1/portal/reports/history?${params.toString()}`);
    items.value = data.items || [];
    Object.assign(meta, { total: data.meta?.total || 0, page: data.meta?.page || 1, page_size: data.meta?.page_size || pageSize, pages: data.meta?.pages || 1 });
    Object.assign(summary, { total: data.summary?.total || 0, reports: data.summary?.reports || 0, certificates: data.summary?.certificates || 0, communications: data.summary?.communications || 0 });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "No se pudo cargar el historial.";
  } finally {
    loading.value = false;
  }
};

const formatDate = (value?: string | null) => {
  if (!value) return "Sin fecha";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Sin fecha";
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
};

const formatLabel = (value?: string | null) => String(value || "").toUpperCase() || "REGISTRO";

const statusClass = (status: string) => ({
  "is-active": ["published", "issued", "sent", "validated", "ready_to_send"].includes(status),
  "is-pending": ["draft", "scheduled"].includes(status),
  "is-neutral": !["published", "issued", "sent", "validated", "ready_to_send", "draft", "scheduled"].includes(status),
});

const changePage = (nextPage: number) => {
  page.value = Math.min(Math.max(1, nextPage), meta.pages || 1);
  loadHistory();
};

watch([sourceFilter, statusFilter], () => {
  page.value = 1;
  loadHistory();
});

watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    page.value = 1;
    loadHistory();
  }, 300);
});

watch(() => activeCondominium.value?.id, () => {
  page.value = 1;
  loadHistory();
});

onMounted(loadHistory);
</script>

<template>
  <section class="panel reports-history-panel">
    <div class="dashboard-hero reports-history-hero">
      <div>
        <p class="eyebrow">Informes</p>
        <h2>Historial del condominio</h2>
        <p class="hero-copy">Bandeja consolidada de certificados emitidos, informes operacionales, informes de proveedores y comunicados del condominio activo.</p>
      </div>
      <div class="committee-summary">
        <article><span>Total</span><strong>{{ summary.total }}</strong></article>
        <article><span>Informes</span><strong>{{ summary.reports }}</strong></article>
        <article><span>Certificados</span><strong>{{ summary.certificates }}</strong></article>
        <article><span>Comunicados</span><strong>{{ summary.communications }}</strong></article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div class="reports-toolbar">
      <label>
        Buscar
        <input v-model="search" type="search" placeholder="Buscar por título, tipo, estado o detalle" />
      </label>
      <label>
        Tipo
        <select v-model="sourceFilter">
          <option value="">Todos</option>
          <option value="report">Informes y certificados</option>
          <option value="communication">Comunicados</option>
        </select>
      </label>
      <label>
        Estado
        <select v-model="statusFilter">
          <option value="">Todos</option>
          <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
        </select>
      </label>
    </div>

    <div class="edifito-table-wrap entity-table-wrap">
      <table class="edifito-table entity-table reports-history-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Tipo</th>
            <th>Título</th>
            <th>Estado</th>
            <th>Formato</th>
            <th>Detalle</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="`${item.source}-${item.id}`">
            <td>{{ formatDate(item.issued_at || item.created_at) }}</td>
            <td>
              <strong>{{ item.category_label }}</strong>
            </td>
            <td>{{ item.title }}</td>
            <td>
              <span class="status-badge" :class="statusClass(item.status)">
                <span aria-hidden="true"></span>
                {{ item.status_label }}
              </span>
            </td>
            <td>{{ formatLabel(item.format) }}</td>
            <td>{{ item.summary || item.metadata?.filename || "Sin detalle" }}</td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td class="empty-row" colspan="6">Sin registros para mostrar.</td>
          </tr>
          <tr v-if="loading">
            <td class="empty-row" colspan="6">Cargando historial...</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="tools-pagination">
      <button class="button ghost compact icon-action" type="button" :disabled="meta.page <= 1" @click="changePage(meta.page - 1)">
        <svg class="icon" aria-hidden="true"><use href="#icon-chevron-left" /></svg>
      </button>
      <span class="tools-page-label">Página {{ meta.page }} de {{ meta.pages }}</span>
      <button class="button ghost compact icon-action" type="button" :disabled="meta.page >= meta.pages" @click="changePage(meta.page + 1)">
        <svg class="icon" aria-hidden="true"><use href="#icon-chevron-right" /></svg>
      </button>
    </div>
  </section>
</template>

<style scoped>
.reports-history-panel {
  display: grid;
  gap: 18px;
}

.reports-toolbar {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(180px, 240px) minmax(180px, 240px);
  gap: 12px;
  align-items: end;
}

.reports-history-table td:nth-child(3),
.reports-history-table td:nth-child(6) {
  min-width: 220px;
}

.reports-history-panel :deep(.entity-table-wrap) {
  overflow-x: hidden;
}

.reports-history-table {
  table-layout: fixed;
  width: 100%;
}

.reports-history-table th,
.reports-history-table td {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reports-history-table th:nth-child(1),
.reports-history-table td:nth-child(1) {
  width: 155px;
}

.reports-history-table th:nth-child(2),
.reports-history-table td:nth-child(2) {
  width: 190px;
}

.reports-history-table th:nth-child(4),
.reports-history-table td:nth-child(4) {
  width: 110px;
}

.reports-history-table th:nth-child(5),
.reports-history-table td:nth-child(5) {
  width: 88px;
}

@media (max-width: 860px) {
  .reports-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
