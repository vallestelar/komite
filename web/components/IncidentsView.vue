<script setup lang="ts">
type OperationalEvent = {
  id: string;
  title: string;
  description?: string | null;
  planned_date: string;
  planned_start_time?: string | null;
  estimated_duration_hours?: number | null;
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

const incidents = ref<OperationalEvent[]>([]);
const staff = ref<OperationalStaff[]>([]);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(String(new Date().getMonth() + 1));
const selectedStatus = ref("");
const search = ref("");
const editingIncident = ref<OperationalEvent | null>(null);
const showIncidentForm = ref(false);
const form = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  estimated_duration_hours: "",
  assigned_user_id: "",
  priority: "medium",
  status: "pending",
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

const visibleIncidents = computed(() => {
  const query = normalize(search.value);
  return incidents.value.filter((incident) => {
    if (!query) return true;
    return normalize(`${incident.title} ${incident.description || ""} ${incident.assigned_user_name || ""}`).includes(query);
  });
});

const loadIncidents = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.set("year", String(selectedYear.value));
    if (selectedMonth.value) params.set("month", selectedMonth.value);
    if (selectedStatus.value) params.set("status", selectedStatus.value);
    const data = await request<OperationalPlanResponse>(`/api/v1/portal/operational-plan/?${params}`);
    incidents.value = (data.items || []).filter((item) => item.event_type ? item.event_type === "incident" : item.source_type === "unplanned_incident");
    staff.value = data.staff || [];
  } catch (error) {
    incidents.value = [];
    staff.value = [];
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  editingIncident.value = null;
  form.title = "";
  form.description = "";
  form.planned_date = new Date().toISOString().slice(0, 10);
  form.planned_start_time = "";
  form.estimated_duration_hours = "";
  form.assigned_user_id = "";
  form.priority = "medium";
  form.status = "pending";
};

const openCreate = () => {
  resetForm();
  showIncidentForm.value = true;
};

const openEdit = (incident: OperationalEvent) => {
  editingIncident.value = incident;
  form.title = incident.title;
  form.description = incident.description || "";
  form.planned_date = incident.planned_date;
  form.planned_start_time = incident.planned_start_time || "";
  form.estimated_duration_hours = incident.estimated_duration_hours ? String(incident.estimated_duration_hours) : "";
  form.assigned_user_id = incident.assigned_user_id || "";
  form.priority = incident.priority || "medium";
  form.status = incident.status || "pending";
  showIncidentForm.value = true;
};

const closeForm = () => {
  if (saving.value) return;
  editingIncident.value = null;
  showIncidentForm.value = false;
};

const saveIncident = async () => {
  if (!form.title.trim()) {
    errorMessage.value = "Indica el título de la incidencia.";
    return;
  }
  saving.value = true;
  errorMessage.value = "";
  try {
    const endpoint = editingIncident.value
      ? `/api/v1/portal/operational-plan/unplanned-incidents/${editingIncident.value.id}`
      : "/api/v1/portal/operational-plan/unplanned-incidents";
    const updated = await request<OperationalEvent>(endpoint, {
      method: editingIncident.value ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: form.title.trim(),
        description: form.description.trim() || null,
        planned_date: form.planned_date,
        planned_start_time: form.planned_start_time || null,
        estimated_duration_hours: optionalNumber(form.estimated_duration_hours),
        assigned_user_id: form.assigned_user_id || null,
        priority: form.priority,
        status: form.status,
      }),
    });
    incidents.value = editingIncident.value
      ? incidents.value.map((incident) => incident.id === updated.id ? updated : incident)
      : [...incidents.value, updated];
    editingIncident.value = null;
    showIncidentForm.value = false;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    saving.value = false;
  }
};

const optionalNumber = (value: string) => {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const formatDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(year, month - 1, day));
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudieron cargar las incidencias.";
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
  return priority || "Media";
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
  return profile || "Sin perfil";
};

const staffOptionLabel = (member: OperationalStaff) => {
  const position = member.responsibility ? ` · ${member.responsibility}` : "";
  return `${member.full_name} · ${profileLabel(member.portal_profile)}${position}`;
};

watch([selectedYear, selectedMonth, selectedStatus], loadIncidents);
watch([() => activeCondominium.value?.id, token], loadIncidents);
onMounted(loadIncidents);
</script>

<template>
  <section class="panel incidents-panel">
    <div class="dashboard-hero incidents-hero">
      <div>
        <p class="eyebrow">Incidencias</p>
        <h2>Incidencias no programadas</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary">
        <article>
          <span>Total</span>
          <strong>{{ incidents.length }}</strong>
        </article>
        <article>
          <span>Mostradas</span>
          <strong>{{ visibleIncidents.length }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div class="operational-toolbar incidents-toolbar">
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
        <input v-model="search" type="search" placeholder="Buscar incidencia o responsable" />
      </label>
      <button class="button ghost" type="button" :disabled="loading" @click="loadIncidents">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <div class="operational-view-row">
      <p class="placeholder-copy">Registra incidencias no programadas para incorporarlas a la agenda del condominio activo.</p>
      <button class="button incident-action" type="button" @click="openCreate">
        <svg class="icon" aria-hidden="true"><use href="#icon-alert" /></svg>
        <span>Nueva incidencia</span>
      </button>
    </div>

    <div v-if="visibleIncidents.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Incidencia</th>
            <th>Responsable</th>
            <th>Prioridad</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="incident in visibleIncidents" :key="incident.id">
            <td>
              <strong>{{ formatDate(incident.planned_date) }}</strong>
              <small v-if="incident.planned_start_time">{{ incident.planned_start_time }}</small>
            </td>
            <td>
              <strong>{{ incident.title }}</strong>
              <small>{{ incident.description || "Sin descripción" }}</small>
            </td>
            <td>{{ incident.assigned_user_name || "Sin persona asignada" }}</td>
            <td>
              <span class="priority-pill" :class="priorityClass(incident.priority)">{{ priorityLabel(incident.priority) }}</span>
            </td>
            <td>
              <span class="status-badge" :class="statusBadgeClass(incident.status)">
                <span aria-hidden="true"></span>
                {{ statusLabel(incident.status) }}
              </span>
            </td>
            <td>
              <button class="button navy icon-only" type="button" title="Editar" @click="openEdit(incident)">
                <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-alert" /></svg>
      </span>
      <h2>Sin incidencias no programadas</h2>
      <p class="placeholder-copy">Las incidencias creadas desde la agenda aparecerán aquí para su seguimiento y edición.</p>
    </div>

    <div v-if="showIncidentForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="incident-edit-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="saveIncident">
        <div class="modal-title-row">
          <div>
          <p class="eyebrow">Incidencias</p>
          <h2 id="incident-edit-title">{{ editingIncident ? "Editar incidencia" : "Nueva incidencia" }}</h2>
          <p class="placeholder-copy">Actualiza la planificación, estado o responsable de esta incidencia.</p>
        </div>

          <button class="button ghost icon-only" type="button" :disabled="saving" title="Cerrar" @click="closeForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label>
            Título
            <input v-model="form.title" type="text" maxlength="180" required />
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
            Duracion estimada (horas)
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
            Estado
            <select v-model="form.status">
              <option value="pending">Pendiente</option>
              <option value="in_progress">En curso</option>
              <option value="completed">Completado</option>
              <option value="cancelled">Cancelado</option>
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
          <button class="button incident-action" type="submit" :disabled="saving">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ saving ? "Guardando..." : (editingIncident ? "Guardar incidencia" : "Crear incidencia") }}</span>
          </button>
        </div>
      </form>
    </div>
  </section>
</template>
