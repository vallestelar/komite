<script setup lang="ts">
type OperationalEvent = {
  id: string;
  title: string;
  description?: string | null;
  planned_date: string;
  planned_start_time?: string | null;
  estimated_duration_hours?: number | null;
  estimated_duration_minutes?: number | null;
  assigned_profile?: string | null;
  assigned_user_id?: string | null;
  assigned_user_name?: string | null;
  priority: string;
  status: string;
  event_type?: string | null;
  source_type?: string | null;
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
  items: OperationalEvent[];
  staff: OperationalStaff[];
};

const { request } = useApi();
const { activeCondominium, token } = useAuth();

const tasks = ref<OperationalEvent[]>([]);
const staff = ref<OperationalStaff[]>([]);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(String(new Date().getMonth() + 1));
const selectedStatus = ref("");
const search = ref("");
const editingTask = ref<OperationalEvent | null>(null);
const showTaskForm = ref(false);
const form = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  estimated_duration_hours: "",
  assigned_user_id: "",
  priority: "medium",
  status: "pending",
  event_type: "task",
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

const eventTypeOptions = [
  ["task", "Tarea"],
  ["administrative", "Administrativa"],
  ["meeting", "Reunión"],
  ["inspection", "Inspección"],
  ["maintenance", "Mantención"],
] as const;

const yearOptions = computed(() => {
  const current = new Date().getFullYear();
  return [current - 1, current, current + 1, current + 2];
});

const visibleTasks = computed(() => {
  const query = normalize(search.value);
  return tasks.value.filter((task) => {
    if (!query) return true;
    return normalize(`${task.title} ${task.description || ""} ${task.assigned_user_name || ""}`).includes(query);
  });
});

const pendingCount = computed(() => tasks.value.filter((task) => task.status === "pending").length);
const overdueCount = computed(() => {
  const today = new Date().toISOString().slice(0, 10);
  return tasks.value.filter((task) => !["completed", "done", "cancelled"].includes(task.status) && task.planned_date < today).length;
});

const loadTasks = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.set("year", String(selectedYear.value));
    if (selectedMonth.value) params.set("month", selectedMonth.value);
    if (selectedStatus.value) params.set("status", selectedStatus.value);
    const data = await request<OperationalPlanResponse>(`/api/v1/portal/operational-plan/?${params}`);
    tasks.value = (data.items || []).filter((item) => item.event_type ? ["task", "administrative", "meeting"].includes(item.event_type) : item.source_type === "manual_task");
    staff.value = data.staff || [];
  } catch (error) {
    tasks.value = [];
    staff.value = [];
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.title = "";
  form.description = "";
  form.planned_date = new Date().toISOString().slice(0, 10);
  form.planned_start_time = "";
  form.estimated_duration_hours = "";
  form.assigned_user_id = "";
  form.priority = "medium";
  form.status = "pending";
  form.event_type = "task";
};

const openCreate = () => {
  editingTask.value = null;
  resetForm();
  showTaskForm.value = true;
};

const openEdit = (task: OperationalEvent) => {
  editingTask.value = task;
  form.title = task.title;
  form.description = task.description || "";
  form.planned_date = task.planned_date;
  form.planned_start_time = task.planned_start_time || "";
  form.estimated_duration_hours = task.estimated_duration_hours ? String(task.estimated_duration_hours) : "";
  form.assigned_user_id = task.assigned_user_id || "";
  form.priority = task.priority || "medium";
  form.status = task.status || "pending";
  form.event_type = task.event_type || "task";
  showTaskForm.value = true;
};

const closeForm = () => {
  if (saving.value) return;
  showTaskForm.value = false;
  editingTask.value = null;
};

const saveTask = async () => {
  if (!form.title.trim()) {
    errorMessage.value = "Indica el título de la tarea.";
    return;
  }
  saving.value = true;
  errorMessage.value = "";
  try {
    const endpoint = editingTask.value
      ? `/api/v1/portal/operational-plan/manual-tasks/${editingTask.value.id}`
      : "/api/v1/portal/operational-plan/manual-tasks";
    const method = editingTask.value ? "PATCH" : "POST";
    const payload: Record<string, unknown> = {
      title: form.title.trim(),
      description: form.description.trim() || null,
      planned_date: form.planned_date,
      planned_start_time: form.planned_start_time || null,
      estimated_duration_hours: form.estimated_duration_hours ? Number(form.estimated_duration_hours) : null,
      assigned_user_id: form.assigned_user_id || null,
      priority: form.priority,
      event_type: form.event_type,
    };
    if (editingTask.value) payload.status = form.status;
    const saved = await request<OperationalEvent>(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    tasks.value = editingTask.value
      ? tasks.value.map((task) => task.id === saved.id ? saved : task)
      : [...tasks.value, saved];
    tasks.value = [...tasks.value].sort((left, right) => {
      const dateCompare = left.planned_date.localeCompare(right.planned_date);
      return dateCompare || left.title.localeCompare(right.title);
    });
    selectedYear.value = Number(saved.planned_date.slice(0, 4));
    selectedMonth.value = String(Number(saved.planned_date.slice(5, 7)));
    showTaskForm.value = false;
    editingTask.value = null;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    saving.value = false;
  }
};

const formatDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(year, month - 1, day));
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudieron cargar las tareas.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

const normalize = (value: string) => value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();

const statusLabel = (status: string | null | undefined) => {
  if (status === "pending") return "Pendiente";
  if (status === "in_progress") return "En curso";
  if (status === "completed" || status === "done") return "Completada";
  if (status === "cancelled") return "Cancelada";
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
  return priority || "Media";
};

const priorityClass = (priority: string | null | undefined) => {
  if (priority === "urgent") return "is-urgent";
  if (priority === "high") return "is-high";
  if (priority === "low") return "is-low";
  return "is-medium";
};

const eventTypeLabel = (eventType: string | null | undefined) => {
  if (eventType === "administrative") return "Administrativa";
  if (eventType === "assembly") return "Asamblea";
  if (eventType === "meeting") return "Reunión";
  if (eventType === "inspection") return "Inspección";
  if (eventType === "maintenance") return "Mantención";
  if (eventType === "incident") return "Incidencia";
  return "Tarea";
};

const profileLabel = (profile: string | null | undefined) => {
  if (profile === "project_manager") return "Project manager";
  if (profile === "supervisor") return "Supervisor";
  if (profile === "ejecutivo" || profile === "executive") return "Ejecutivo/a";
  return profile || "Sin perfil";
};

const staffOptionLabel = (member: OperationalStaff) => {
  const position = member.responsibility ? ` · ${member.responsibility}` : "";
  return `${member.full_name} · ${profileLabel(member.portal_profile)}${position}`;
};

watch([selectedYear, selectedMonth, selectedStatus], loadTasks);
watch([() => activeCondominium.value?.id, token], loadTasks);
onMounted(loadTasks);
</script>

<template>
  <section class="panel tasks-panel">
    <div class="dashboard-hero tasks-hero">
      <div>
        <p class="eyebrow">Tareas</p>
        <h2>Planificación manual</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary operational-summary">
        <article>
          <span>Total</span>
          <strong>{{ tasks.length }}</strong>
        </article>
        <article>
          <span>Pendientes</span>
          <strong>{{ pendingCount }}</strong>
        </article>
        <article class="is-overdue">
          <span>Vencidas</span>
          <strong>{{ overdueCount }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div class="operational-toolbar tasks-toolbar">
      <label>
        Año
        <select v-model.number="selectedYear">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
        </select>
      </label>
      <label>
        Mes
        <select v-model="selectedMonth">
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
        <input v-model="search" type="search" placeholder="Buscar tarea o responsable" />
      </label>
      <button class="button ghost" type="button" :disabled="loading" @click="loadTasks">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <div class="operational-view-row">
      <p class="placeholder-copy">Crea tareas puntuales para organizar el trabajo del día o de la semana sin depender todavía de una plantilla.</p>
      <button class="button orange" type="button" @click="openCreate">
        <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
        <span>Nueva tarea</span>
      </button>
    </div>

    <div v-if="visibleTasks.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Tarea</th>
            <th>Responsable</th>
            <th>Tipo</th>
            <th>Prioridad</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in visibleTasks" :key="task.id">
            <td>
              <strong>{{ formatDate(task.planned_date) }}</strong>
              <small v-if="task.planned_start_time">{{ task.planned_start_time }}</small>
              <small v-if="task.estimated_duration_hours">{{ task.estimated_duration_hours }} h</small>
            </td>
            <td>
              <strong>{{ task.title }}</strong>
              <small>{{ task.description || "Sin descripción" }}</small>
            </td>
            <td>{{ task.assigned_user_name || "Sin persona asignada" }}</td>
            <td>
              <span class="status-pill">{{ eventTypeLabel(task.event_type) }}</span>
            </td>
            <td>
              <span class="priority-pill" :class="priorityClass(task.priority)">{{ priorityLabel(task.priority) }}</span>
            </td>
            <td>
              <span class="status-badge" :class="statusBadgeClass(task.status)">
                <span aria-hidden="true"></span>
                {{ statusLabel(task.status) }}
              </span>
            </td>
            <td>
              <button class="button navy icon-only" type="button" title="Editar tarea" @click="openEdit(task)">
                <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-checks" /></svg>
      </span>
      <h2>Sin tareas manuales</h2>
      <p class="placeholder-copy">Crea la primera tarea manual para planificar trabajo puntual del condominio activo.</p>
    </div>

    <div v-if="showTaskForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="task-form-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="saveTask">
        <div>
          <p class="eyebrow">Tareas</p>
          <h2 id="task-form-title">{{ editingTask ? "Editar tarea" : "Nueva tarea manual" }}</h2>
          <p class="placeholder-copy">La tarea quedará disponible en esta pantalla y también en la agenda operativa.</p>
        </div>

        <div class="entity-form-grid">
          <label>
            Título
            <input v-model="form.title" type="text" maxlength="180" placeholder="Ej. Revisar sala de bombas" required />
          </label>
          <label>
            Fecha
            <input v-model="form.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="form.planned_start_time" type="time" />
          </label>
          <label>
            Duración estimada (horas)
            <input v-model="form.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 0.5" />
          </label>
          <label>
            Prioridad
            <select v-model="form.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label>
            Tipo
            <select v-model="form.event_type">
              <option v-for="[value, label] in eventTypeOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label v-if="editingTask">
            Estado
            <select v-model="form.status">
              <option value="pending">Pendiente</option>
              <option value="in_progress">En curso</option>
              <option value="completed">Completada</option>
              <option value="cancelled">Cancelada</option>
            </select>
          </label>
          <label>
            Responsable
            <select v-model="form.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="form.description" rows="4"></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="saving" @click="closeForm">Cancelar</button>
          <button class="button navy" type="submit" :disabled="saving">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ saving ? "Guardando..." : editingTask ? "Guardar cambios" : "Añadir a la agenda" }}</span>
          </button>
        </div>
      </form>
    </div>
  </section>
</template>
