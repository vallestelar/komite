<script setup lang="ts">
type OperationalEvent = {
  id: string;
  title: string;
  description?: string | null;
  planned_date: string;
  planned_start_time?: string | null;
  planned_end_time?: string | null;
  assigned_profile?: string | null;
  assigned_user_id?: string | null;
  assigned_user_name?: string | null;
  assigned_user_email?: string | null;
  priority: string;
  status: string;
  source_type?: string | null;
  section_name?: string | null;
  asset_name?: string | null;
  template_item_id?: string | null;
};

type OperationalStaff = {
  user_id: string;
  full_name: string;
  email?: string | null;
  portal_profile: string;
  responsibility?: string | null;
  is_primary: boolean;
};

type OperationalPlanResponse = {
  condominium_id: string;
  condominium_name: string;
  year: number;
  month?: number | null;
  items: OperationalEvent[];
  staff: OperationalStaff[];
  summary: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    overdue: number;
  };
};

const { request } = useApi();
const { activeCondominium, token } = useAuth();

const events = ref<OperationalEvent[]>([]);
const staff = ref<OperationalStaff[]>([]);
const summary = reactive({
  total: 0,
  pending: 0,
  in_progress: 0,
  completed: 0,
  overdue: 0,
});
const loading = ref(false);
const errorMessage = ref("");
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(String(new Date().getMonth() + 1));
const selectedStatus = ref("");
const search = ref("");
const savingAssignment = ref("");
const agendaView = ref<"list" | "week">("list");
const selectedWeekStart = ref<Date | null>(null);
const showIncidentForm = ref(false);
const showTaskForm = ref(false);
const savingIncident = ref(false);
const savingTask = ref(false);
const incidentForm = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  assigned_user_id: "",
  priority: "medium",
});
const taskForm = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  assigned_user_id: "",
  priority: "medium",
});

const monthOptions = [
  [1, "Enero"],
  [2, "Febrero"],
  [3, "Marzo"],
  [4, "Abril"],
  [5, "Mayo"],
  [6, "Junio"],
  [7, "Julio"],
  [8, "Agosto"],
  [9, "Septiembre"],
  [10, "Octubre"],
  [11, "Noviembre"],
  [12, "Diciembre"],
] as const;

const statusOptions = [
  ["", "Todos los estados"],
  ["pending", "Pendiente"],
  ["in_progress", "En curso"],
  ["completed", "Completado"],
  ["cancelled", "Cancelado"],
] as const;

const yearOptions = computed(() => {
  const current = new Date().getFullYear();
  return [current - 1, current, current + 1, current + 2];
});

const normalizedSearch = computed(() => normalize(search.value));

const searchedEvents = computed(() => events.value.filter((event) => {
  if (!normalizedSearch.value) return true;
  const text = normalize(`${event.title} ${event.description || ""} ${event.section_name || ""} ${event.asset_name || ""} ${event.assigned_profile || ""} ${event.assigned_user_name || ""}`);
  return text.includes(normalizedSearch.value);
}));

const groupedEvents = computed(() => {
  const groups = new Map<string, OperationalEvent[]>();
  for (const event of visibleEvents.value) {
    groups.set(event.planned_date, [...(groups.get(event.planned_date) || []), event]);
  }
  return Array.from(groups.entries()).map(([dateKey, items]) => ({ dateKey, items }));
});

const defaultWeekStartDate = computed(() => {
  const year = Number(selectedYear.value);
  const month = selectedMonth.value ? Number(selectedMonth.value) : new Date().getMonth() + 1;
  const today = new Date();
  const base = today.getFullYear() === year && today.getMonth() + 1 === month
    ? new Date(today.getFullYear(), today.getMonth(), today.getDate())
    : new Date(year, month - 1, 1);
  const mondayOffset = (base.getDay() + 6) % 7;
  base.setDate(base.getDate() - mondayOffset);
  base.setHours(0, 0, 0, 0);
  return base;
});

const weekStartDate = computed(() => selectedWeekStart.value || defaultWeekStartDate.value);

const weekRangeLabel = computed(() => {
  const start = new Date(weekStartDate.value);
  const end = new Date(weekStartDate.value);
  end.setDate(start.getDate() + 6);
  const formatter = new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short", year: "numeric" });
  return `${formatter.format(start)} - ${formatter.format(end)}`;
});

const visibleEvents = computed(() => {
  const start = new Date(weekStartDate.value);
  const end = new Date(weekStartDate.value);
  end.setDate(start.getDate() + 6);
  const startKey = toDateKey(start);
  const endKey = toDateKey(end);
  return searchedEvents.value.filter((event) => event.planned_date >= startKey && event.planned_date <= endKey);
});

const weekDays = computed(() => Array.from({ length: 7 }, (_, index) => {
  const value = new Date(weekStartDate.value);
  value.setDate(weekStartDate.value.getDate() + index);
  const dateKey = toDateKey(value);
  return {
    dateKey,
    label: new Intl.DateTimeFormat("es-CL", { weekday: "short" }).format(value),
    day: new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short" }).format(value),
    items: visibleEvents.value.filter((event) => event.planned_date === dateKey),
  };
}));

const moveWeek = (offset: number) => {
  const next = new Date(weekStartDate.value);
  next.setDate(next.getDate() + offset * 7);
  next.setHours(0, 0, 0, 0);
  selectedWeekStart.value = next;
  selectedYear.value = next.getFullYear();
  selectedMonth.value = String(next.getMonth() + 1);
};

const resetWeekSelection = () => {
  selectedWeekStart.value = null;
};

const goToCurrentWeek = () => {
  const today = new Date();
  selectedYear.value = today.getFullYear();
  selectedMonth.value = String(today.getMonth() + 1);
  selectedWeekStart.value = null;
};

const loadPlan = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.set("year", String(selectedYear.value));
    if (selectedMonth.value) params.set("month", selectedMonth.value);
    if (selectedStatus.value) params.set("status", selectedStatus.value);
    const data = await request<OperationalPlanResponse>(`/api/v1/portal/operational-plan/?${params}`);
    events.value = data.items || [];
    staff.value = data.staff || [];
    summary.total = data.summary?.total || 0;
    summary.pending = data.summary?.pending || 0;
    summary.in_progress = data.summary?.in_progress || 0;
    summary.completed = data.summary?.completed || 0;
    summary.overdue = data.summary?.overdue || 0;
  } catch (error) {
    events.value = [];
    staff.value = [];
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const assignEvent = async (event: OperationalEvent, assignedUserId: string) => {
  savingAssignment.value = event.id;
  errorMessage.value = "";
  try {
    const updated = await request<OperationalEvent>(`/api/v1/portal/operational-plan/events/${event.id}/assignment`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assigned_user_id: assignedUserId || null }),
    });
    events.value = events.value.map((item) => item.id === updated.id ? updated : item);
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingAssignment.value = "";
  }
};

const openIncidentForm = () => {
  incidentForm.title = "";
  incidentForm.description = "";
  incidentForm.planned_date = toDateKey(new Date());
  incidentForm.planned_start_time = "";
  incidentForm.assigned_user_id = "";
  incidentForm.priority = "medium";
  showIncidentForm.value = true;
};

const closeIncidentForm = () => {
  if (savingIncident.value) return;
  showIncidentForm.value = false;
};

const openTaskForm = () => {
  taskForm.title = "";
  taskForm.description = "";
  taskForm.planned_date = toDateKey(new Date());
  taskForm.planned_start_time = "";
  taskForm.assigned_user_id = "";
  taskForm.priority = "medium";
  showTaskForm.value = true;
};

const closeTaskForm = () => {
  if (savingTask.value) return;
  showTaskForm.value = false;
};

const addCreatedEventToAgenda = (created: OperationalEvent) => {
  events.value = [...events.value, created].sort((left, right) => {
    const dateCompare = left.planned_date.localeCompare(right.planned_date);
    return dateCompare || left.title.localeCompare(right.title);
  });
  summary.total += 1;
  summary.pending += 1;
  selectedYear.value = Number(created.planned_date.slice(0, 4));
  selectedMonth.value = String(Number(created.planned_date.slice(5, 7)));
  const createdDate = new Date(`${created.planned_date}T00:00:00`);
  const mondayOffset = (createdDate.getDay() + 6) % 7;
  createdDate.setDate(createdDate.getDate() - mondayOffset);
  selectedWeekStart.value = createdDate;
};

const createManualTask = async () => {
  if (!taskForm.title.trim()) {
    errorMessage.value = "Indica el título de la tarea.";
    return;
  }
  savingTask.value = true;
  errorMessage.value = "";
  try {
    const created = await request<OperationalEvent>("/api/v1/portal/operational-plan/manual-tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: taskForm.title.trim(),
        description: taskForm.description.trim() || null,
        planned_date: taskForm.planned_date,
        planned_start_time: taskForm.planned_start_time || null,
        assigned_user_id: taskForm.assigned_user_id || null,
        priority: taskForm.priority,
      }),
    });
    addCreatedEventToAgenda(created);
    showTaskForm.value = false;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingTask.value = false;
  }
};

const createUnplannedIncident = async () => {
  if (!incidentForm.title.trim()) {
    errorMessage.value = "Indica el título de la incidencia.";
    return;
  }
  savingIncident.value = true;
  errorMessage.value = "";
  try {
    const created = await request<OperationalEvent>("/api/v1/portal/operational-plan/unplanned-incidents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: incidentForm.title.trim(),
        description: incidentForm.description.trim() || null,
        planned_date: incidentForm.planned_date,
        planned_start_time: incidentForm.planned_start_time || null,
        assigned_user_id: incidentForm.assigned_user_id || null,
        priority: incidentForm.priority,
      }),
    });
    addCreatedEventToAgenda(created);
    showIncidentForm.value = false;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingIncident.value = false;
  }
};

const formatDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
};

const shortDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short" }).format(new Date(year, month - 1, day));
};

const toDateKey = (value: Date) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const normalize = (value: string) => value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo cargar el plan operativo.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

const statusLabel = (status: string | null | undefined) => {
  if (status === "pending") return "Pendiente";
  if (status === "in_progress") return "En curso";
  if (status === "completed" || status === "done") return "Completado";
  if (status === "cancelled") return "Cancelado";
  return status || "Sin estado";
};

const statusBadgeClass = (status: string | null | undefined) => {
  if (status === "pending") return "is-pending";
  if (status === "in_progress") return "is-progress";
  if (status === "completed" || status === "done") return "is-active";
  if (status === "cancelled") return "is-inactive";
  return "is-neutral";
};

const priorityLabel = (priority: string | null | undefined) => {
  if (priority === "urgent") return "Urgente";
  if (priority === "high") return "Alta";
  if (priority === "medium") return "Media";
  if (priority === "low") return "Baja";
  return priority || "Sin prioridad";
};

const priorityClass = (priority: string | null | undefined) => {
  if (priority === "urgent") return "is-urgent";
  if (priority === "high") return "is-high";
  if (priority === "low") return "is-low";
  return "is-medium";
};

const profileLabel = (profile: string | null | undefined) => {
  if (profile === "project_manager") return "Project manager";
  if (profile === "supervisor") return "Supervisor";
  if (profile === "ejecutivo" || profile === "executive") return "Ejecutivo/a";
  if (profile === "conserje") return "Conserje";
  return profile || "Sin responsable";
};

const sourceLabel = (sourceType: string | null | undefined) => {
  if (sourceType === "unplanned_incident") return "Incidencia no programada";
  if (sourceType === "manual_task") return "Tarea manual";
  if (sourceType === "maintenance_template") return "Planificada";
  if (sourceType === "inspection_template") return "Planificada";
  return sourceType || "Planificada";
};

const isUnplannedIncident = (event: OperationalEvent) => event.source_type === "unplanned_incident";
const isManualTask = (event: OperationalEvent) => event.source_type === "manual_task";

const staffOptionLabel = (member: OperationalStaff) => {
  const profile = profileLabel(member.portal_profile);
  const position = member.responsibility ? ` · ${member.responsibility}` : "";
  return `${member.full_name} · ${profile}${position}`;
};

const assigneeLabel = (event: OperationalEvent) => event.assigned_user_name || "Sin persona asignada";

watch([selectedYear, selectedMonth, selectedStatus], loadPlan);
watch([() => activeCondominium.value?.id, token], loadPlan);
onMounted(loadPlan);
</script>

<template>
  <section class="panel operational-panel">
    <div class="dashboard-hero operational-hero">
      <div>
        <p class="eyebrow">Agenda operativa</p>
        <h2>Plan operativo del condominio</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary operational-summary">
        <article>
          <span>Total</span>
          <strong>{{ summary.total }}</strong>
        </article>
        <article>
          <span>Pendientes</span>
          <strong>{{ summary.pending }}</strong>
        </article>
        <article class="is-overdue">
          <span>Vencidos</span>
          <strong>{{ summary.overdue }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div class="operational-toolbar">
      <label>
        Año
        <select v-model.number="selectedYear" @change="resetWeekSelection">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
        </select>
      </label>
      <label>
        Mes
        <select v-model="selectedMonth" @change="resetWeekSelection">
          <option value="">Todo el año</option>
          <option v-for="[month, label] in monthOptions" :key="month" :value="String(month)">{{ label }}</option>
        </select>
      </label>
      <label>
        Estado
        <select v-model="selectedStatus">
          <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
        </select>
      </label>
      <label>
        Buscar
        <input v-model="search" type="search" placeholder="Buscar tarea, sección o responsable" />
      </label>
      <button class="button ghost" type="button" :disabled="loading" @click="loadPlan">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <div class="operational-view-row">
      <div class="view-toggle" role="group" aria-label="Vista de agenda">
        <button class="button compact" :class="agendaView === 'list' ? 'navy' : 'ghost'" type="button" @click="agendaView = 'list'">
          <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
          <span>Listado</span>
        </button>
        <button class="button compact" :class="agendaView === 'week' ? 'navy' : 'ghost'" type="button" @click="agendaView = 'week'">
          <svg class="icon" aria-hidden="true"><use href="#icon-calendar" /></svg>
          <span>Semana</span>
        </button>
      </div>
      <div class="operational-actions">
        <button class="button manual-task-action" type="button" @click="openTaskForm">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nueva tarea</span>
        </button>
        <button class="button incident-action" type="button" @click="openIncidentForm">
          <svg class="icon" aria-hidden="true"><use href="#icon-alert" /></svg>
          <span>Nueva incidencia</span>
        </button>
      </div>
    </div>

    <div class="week-navigation">
      <button class="button ghost compact" type="button" @click="moveWeek(-1)">
        <svg class="icon" aria-hidden="true"><use href="#icon-chevron-left" /></svg>
        <span>Semana anterior</span>
      </button>
      <strong>{{ weekRangeLabel }}</strong>
      <button class="button ghost compact" type="button" @click="goToCurrentWeek">
        <svg class="icon" aria-hidden="true"><use href="#icon-calendar" /></svg>
        <span>Semana actual</span>
      </button>
      <button class="button ghost compact" type="button" @click="moveWeek(1)">
        <span>Semana siguiente</span>
        <svg class="icon" aria-hidden="true"><use href="#icon-chevron-right" /></svg>
      </button>
    </div>

    <div class="metrics-grid operational-metrics">
      <article class="metric"><span>En curso</span><strong>{{ summary.in_progress }}</strong><small>Actualmente gestionándose</small></article>
      <article class="metric"><span>Completados</span><strong>{{ summary.completed }}</strong><small>Eventos cerrados</small></article>
      <article class="metric"><span>Mostrados</span><strong>{{ visibleEvents.length }}</strong><small>Tras aplicar búsqueda</small></article>
      <article class="metric"><span>Condominio</span><strong class="metric-name">{{ activeCondominium?.name || "Sin contexto" }}</strong><small>Contexto activo</small></article>
    </div>

    <div v-if="agendaView === 'week'" class="week-board" aria-label="Vista semanal de agenda operativa">
      <section v-for="day in weekDays" :key="day.dateKey" class="week-column">
        <header>
          <span>{{ day.label }}</span>
          <strong>{{ day.day }}</strong>
        </header>
        <div class="week-column-body">
          <article
            v-for="event in day.items"
            :key="event.id"
            class="week-task-card"
            :class="{ 'is-unplanned': isUnplannedIncident(event), 'is-manual': isManualTask(event) }"
          >
            <h3>{{ event.title }}</h3>
            <span class="status-badge week-status" :class="statusBadgeClass(event.status)">
              <span aria-hidden="true"></span>
              {{ statusLabel(event.status) }}
            </span>
            <p v-if="isUnplannedIncident(event)" class="week-source">{{ sourceLabel(event.source_type) }}</p>
            <p class="week-condominium">{{ activeCondominium?.name || "Sin condominio" }}</p>
            <p>{{ assigneeLabel(event) }}</p>
          </article>
          <p v-if="!day.items.length" class="week-empty">Sin tareas</p>
        </div>
      </section>
    </div>

    <div v-else-if="groupedEvents.length" class="operational-agenda">
      <section v-for="group in groupedEvents" :key="group.dateKey" class="operational-day">
        <header>
          <div>
            <span>{{ shortDate(group.dateKey) }}</span>
            <h3>{{ formatDate(group.dateKey) }}</h3>
          </div>
          <strong>{{ group.items.length }} eventos</strong>
        </header>
        <div class="operational-events">
          <article
            v-for="event in group.items"
            :key="event.id"
            class="operational-event"
            :class="{ 'is-manual': isManualTask(event) }"
          >
            <div class="event-date-dot" aria-hidden="true"></div>
            <div class="event-content">
              <div class="event-title-row">
                <div>
                  <p class="event-section">{{ sourceLabel(event.source_type) }} · {{ event.section_name || "Sin sección" }}</p>
                  <h3>{{ event.title }}</h3>
                </div>
                <span class="status-badge" :class="statusBadgeClass(event.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(event.status) }}
                </span>
              </div>
              <p v-if="event.description" class="event-description">{{ event.description }}</p>
              <div class="event-meta">
                <span v-if="event.asset_name">
                  <svg class="icon" aria-hidden="true"><use href="#icon-building" /></svg>
                  {{ event.asset_name }}
                </span>
                <span>
                  <svg class="icon" aria-hidden="true"><use href="#icon-users" /></svg>
                  {{ profileLabel(event.assigned_profile) }}
                </span>
                <label class="event-assignee">
                  <svg class="icon" aria-hidden="true"><use href="#icon-user" /></svg>
                  <select
                    :value="event.assigned_user_id || ''"
                    :disabled="savingAssignment === event.id || !staff.length"
                    :title="event.assigned_user_name || 'Asignar responsable'"
                    @change="assignEvent(event, ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="">Sin persona asignada</option>
                    <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                      {{ staffOptionLabel(member) }}
                    </option>
                  </select>
                </label>
                <span class="priority-pill" :class="priorityClass(event.priority)">
                  {{ priorityLabel(event.priority) }}
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-calendar" /></svg>
      </span>
      <h2>Sin eventos operativos</h2>
      <p class="placeholder-copy">Genera la planificación desde el plan de mantenciones para visualizarla aquí.</p>
    </div>
    <div v-if="showIncidentForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="incident-form-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="createUnplannedIncident">
        <div>
          <p class="eyebrow">Agenda operativa</p>
          <h2 id="incident-form-title">Nueva incidencia no programada</h2>
          <p class="placeholder-copy">Se añadirá como tarea pendiente dentro de la planificación del condominio activo.</p>
        </div>

        <div class="entity-form-grid">
          <label>
            Título
            <input v-model="incidentForm.title" type="text" maxlength="180" placeholder="Ej. Fuga de agua en sala de bombas" required />
          </label>
          <label>
            Fecha
            <input v-model="incidentForm.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="incidentForm.planned_start_time" type="time" />
          </label>
          <label>
            Prioridad
            <select v-model="incidentForm.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label>
            Responsable
            <select v-model="incidentForm.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="incidentForm.description" rows="4" placeholder="Describe brevemente qué ocurrió y qué se necesita resolver."></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingIncident" @click="closeIncidentForm">
            Cancelar
          </button>
          <button class="button incident-action" type="submit" :disabled="savingIncident">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingIncident ? "Guardando..." : "Añadir a la agenda" }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="showTaskForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="task-form-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="createManualTask">
        <div>
          <p class="eyebrow">Agenda operativa</p>
          <h2 id="task-form-title">Nueva tarea manual</h2>
          <p class="placeholder-copy">Se añadirá como tarea pendiente dentro de la planificación del condominio activo.</p>
        </div>

        <div class="entity-form-grid">
          <label>
            Título
            <input v-model="taskForm.title" type="text" maxlength="180" placeholder="Ej. Revisar sala de bombas" required />
          </label>
          <label>
            Fecha
            <input v-model="taskForm.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="taskForm.planned_start_time" type="time" />
          </label>
          <label>
            Prioridad
            <select v-model="taskForm.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label>
            Responsable
            <select v-model="taskForm.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="taskForm.description" rows="4" placeholder="Describe brevemente qué debe realizarse."></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingTask" @click="closeTaskForm">
            Cancelar
          </button>
          <button class="button navy" type="submit" :disabled="savingTask">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingTask ? "Guardando..." : "Añadir a la agenda" }}</span>
          </button>
        </div>
      </form>
    </div>
  </section>
</template>
