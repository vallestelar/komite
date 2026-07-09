<script setup lang="ts">
type InspectionChecklistItem = {
  id: string;
  label: string;
  status: string;
  observations?: string | null;
  requires_action: boolean;
};

type InspectionExecution = {
  id: string;
  result: string;
  comments?: string | null;
  requires_follow_up: boolean;
  executed_at?: string | null;
  checklist: InspectionChecklistItem[];
};

type InspectionItem = {
  id: string;
  title: string;
  description?: string | null;
  planned_date: string;
  planned_start_time?: string | null;
  assigned_user_name?: string | null;
  assigned_profile?: string | null;
  priority: string;
  status: string;
  event_type?: string | null;
  source_type?: string | null;
  section_name?: string | null;
  asset_name?: string | null;
  template_name?: string | null;
  execution?: InspectionExecution | null;
};

type InspectionResponse = {
  items: InspectionItem[];
  summary: {
    total: number;
    pending: number;
    in_progress: number;
    overdue: number;
    completed: number;
    requires_action: number;
  };
};

const { request } = useApi();
const { activeCondominium, token } = useAuth();

const inspections = ref<InspectionItem[]>([]);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(String(new Date().getMonth() + 1));
const selectedStatus = ref("");
const search = ref("");
const activeInspection = ref<InspectionItem | null>(null);
const summary = reactive({
  total: 0,
  pending: 0,
  in_progress: 0,
  overdue: 0,
  completed: 0,
  requires_action: 0,
});
const executionForm = reactive({
  result: "in_progress",
  comments: "",
  requires_follow_up: false,
  close_event: false,
  checklist: [] as InspectionChecklistItem[],
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

const resultOptions = [
  ["in_progress", "En curso"],
  ["conforme", "Conforme"],
  ["observed", "Con observaciones"],
  ["requires_action", "Requiere acción"],
  ["not_executed", "No ejecutada"],
] as const;

const checklistStatusOptions = [
  ["pending", "Pendiente"],
  ["ok", "Conforme"],
  ["observed", "Observado"],
  ["requires_action", "Requiere acción"],
] as const;

const yearOptions = computed(() => {
  const current = new Date().getFullYear();
  return [current - 1, current, current + 1, current + 2];
});

const visibleInspections = computed(() => {
  const query = normalize(search.value);
  if (!query) return inspections.value;
  return inspections.value.filter((inspection) => normalize([
    inspection.title,
    inspection.description || "",
    inspection.section_name || "",
    inspection.asset_name || "",
    inspection.assigned_user_name || "",
    inspection.template_name || "",
  ].join(" ")).includes(query));
});

const loadInspections = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.set("year", String(selectedYear.value));
    if (selectedMonth.value) params.set("month", selectedMonth.value);
    if (selectedStatus.value) params.set("status", selectedStatus.value);
    const data = await request<InspectionResponse>(`/api/v1/portal/inspections/?${params}`);
    inspections.value = data.items || [];
    Object.assign(summary, data.summary);
  } catch (error) {
    inspections.value = [];
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const openExecution = async (inspection: InspectionItem) => {
  errorMessage.value = "";
  try {
    const detail = await request<InspectionItem>(`/api/v1/portal/inspections/${inspection.id}`);
    activeInspection.value = detail;
    executionForm.result = detail.execution?.result || (detail.status === "completed" ? "conforme" : "in_progress");
    executionForm.comments = detail.execution?.comments || "";
    executionForm.requires_follow_up = Boolean(detail.execution?.requires_follow_up);
    executionForm.close_event = detail.status === "completed";
    executionForm.checklist = (detail.execution?.checklist?.length ? detail.execution.checklist : [{
      id: "main",
      label: detail.title,
      status: "pending",
      observations: "",
      requires_action: false,
    }]).map((item) => ({ ...item }));
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const closeExecution = () => {
  if (saving.value) return;
  activeInspection.value = null;
};

const saveExecution = async () => {
  if (!activeInspection.value) return;
  saving.value = true;
  errorMessage.value = "";
  try {
    const updated = await request<InspectionItem>(`/api/v1/portal/inspections/${activeInspection.value.id}/execution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        result: executionForm.result,
        comments: executionForm.comments.trim() || null,
        requires_follow_up: executionForm.requires_follow_up,
        close_event: executionForm.close_event,
        checklist: executionForm.checklist.map((item) => ({
          id: item.id,
          label: item.label,
          status: item.status,
          observations: item.observations?.trim() || null,
          requires_action: item.requires_action,
        })),
      }),
    });
    inspections.value = inspections.value.map((item) => item.id === updated.id ? updated : item);
    activeInspection.value = null;
    await loadInspections();
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    saving.value = false;
  }
};

const addChecklistItem = () => {
  executionForm.checklist.push({
    id: `manual-${Date.now()}`,
    label: "",
    status: "pending",
    observations: "",
    requires_action: false,
  });
};

const removeChecklistItem = (index: number) => {
  executionForm.checklist.splice(index, 1);
};

const formatDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(year, month - 1, day));
};

const formatDateDayMonth = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short" }).format(new Date(year, month - 1, day));
};

const formatDateYear = (value: string) => {
  const [year] = value.split("-");
  return year;
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudieron cargar las inspecciones.";
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

const resultLabel = (result: string | null | undefined) => {
  if (result === "conforme") return "Conforme";
  if (result === "observed") return "Con observaciones";
  if (result === "requires_action") return "Requiere acción";
  if (result === "not_executed") return "No ejecutada";
  if (result === "in_progress") return "En curso";
  if (result === "pending") return "Pendiente";
  return result || "Sin ejecución";
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

watch([selectedYear, selectedMonth, selectedStatus], loadInspections);
watch([() => activeCondominium.value?.id, token], loadInspections);
onMounted(loadInspections);
</script>

<template>
  <section class="content-grid">
    <div class="dashboard-hero">
      <div>
        <p class="eyebrow">Inspecciones</p>
        <h2>Control operativo de inspecciones</h2>
        <p>{{ activeCondominium?.name || "Sin condominio" }}</p>
      </div>
      <div class="hero-metrics compact">
        <article>
          <span>Total</span>
          <strong>{{ summary.total }}</strong>
        </article>
        <article>
          <span>Pendientes</span>
          <strong>{{ summary.pending }}</strong>
        </article>
        <article class="danger-card">
          <span>Vencidas</span>
          <strong>{{ summary.overdue }}</strong>
        </article>
        <article>
          <span>Requieren acción</span>
          <strong>{{ summary.requires_action }}</strong>
        </article>
      </div>
    </div>

    <div class="table-card">
      <div class="operational-toolbar">
        <label>
          Año
          <select v-model="selectedYear">
            <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
          </select>
        </label>
        <label>
          Mes
          <select v-model="selectedMonth">
            <option v-for="[value, label] in monthOptions" :key="value" :value="String(value)">{{ label }}</option>
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
          <input v-model="search" type="search" placeholder="Buscar inspección, zona o responsable" />
        </label>
        <button class="button ghost" type="button" :disabled="loading" @click="loadInspections">
          <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
          <span>Actualizar</span>
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div class="table-card inspections-table-card">
      <table class="data-table inspections-table">
        <colgroup>
          <col class="inspection-col-date" />
          <col class="inspection-col-main" />
          <col class="inspection-col-zone" />
          <col class="inspection-col-person" />
          <col class="inspection-col-priority" />
          <col class="inspection-col-status" />
          <col class="inspection-col-result" />
          <col class="inspection-col-actions" />
        </colgroup>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Inspección</th>
            <th>Zona</th>
            <th>Responsable</th>
            <th>Prioridad</th>
            <th>Estado</th>
            <th>Resultado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inspection in visibleInspections" :key="inspection.id">
            <td>
              <span class="inspection-date">
                <strong>{{ formatDateDayMonth(inspection.planned_date) }}</strong>
                <small>{{ formatDateYear(inspection.planned_date) }}</small>
              </span>
            </td>
            <td class="inspection-main-cell">
              <span class="inspection-title">{{ inspection.title }}</span>
              <span class="inspection-subtitle">{{ inspection.template_name || inspection.description || "Sin plantilla" }}</span>
            </td>
            <td><span class="inspection-muted-cell">{{ inspection.asset_name || inspection.section_name || "Sin zona" }}</span></td>
            <td><span class="inspection-person-cell">{{ inspection.assigned_user_name || "Sin persona asignada" }}</span></td>
            <td><span class="priority-pill" :class="priorityClass(inspection.priority)">{{ priorityLabel(inspection.priority) }}</span></td>
            <td>
              <span class="status-badge" :class="statusBadgeClass(inspection.status)">
                <span aria-hidden="true"></span>
                {{ statusLabel(inspection.status) }}
              </span>
            </td>
            <td><span class="inspection-muted-cell">{{ resultLabel(inspection.execution?.result) }}</span></td>
            <td class="inspection-actions">
              <button class="button navy icon-only" type="button" title="Ejecutar inspección" @click="openExecution(inspection)">
                <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
              </button>
            </td>
          </tr>
          <tr v-if="!visibleInspections.length">
            <td colspan="8" class="empty-cell">{{ loading ? "Cargando inspecciones..." : "No hay inspecciones para mostrar." }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="activeInspection" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="inspection-execution-title">
      <form class="confirm-modal inspection-execution-modal" @submit.prevent="saveExecution">
        <div class="inspection-modal-header">
          <div>
            <p class="eyebrow">Inspección</p>
            <h2 id="inspection-execution-title">{{ activeInspection.title }}</h2>
            <p class="placeholder-copy">
              {{ formatDate(activeInspection.planned_date) }} · {{ activeInspection.asset_name || activeInspection.section_name || "Sin zona" }}
            </p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="saving" title="Cerrar" @click="closeExecution">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label>
            Resultado
            <select v-model="executionForm.result">
              <option v-for="[value, label] in resultOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label class="switch-field inspection-switch">
            <input v-model="executionForm.requires_follow_up" type="checkbox" />
            <span>Requiere seguimiento</span>
          </label>
          <label class="switch-field inspection-switch">
            <input v-model="executionForm.close_event" type="checkbox" />
            <span>Cerrar inspección</span>
          </label>
          <label class="wide-field">
            Observaciones generales
            <textarea v-model="executionForm.comments" rows="3" placeholder="Resumen de lo revisado, hallazgos o próximos pasos."></textarea>
          </label>
        </div>

        <section class="inspection-checklist">
          <div class="inspection-checklist-header">
            <h3>Checklist</h3>
            <button class="button ghost" type="button" @click="addChecklistItem">
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Agregar ítem</span>
            </button>
          </div>
          <article v-for="(item, index) in executionForm.checklist" :key="item.id" class="inspection-checklist-item">
            <label>
              Ítem
              <input v-model="item.label" type="text" placeholder="Describe el punto revisado" required />
            </label>
            <label>
              Estado
              <select v-model="item.status">
                <option v-for="[value, label] in checklistStatusOptions" :key="value" :value="value">{{ label }}</option>
              </select>
            </label>
            <label class="switch-field inspection-switch">
              <input v-model="item.requires_action" type="checkbox" />
              <span>Acción requerida</span>
            </label>
            <label class="wide-field">
              Observaciones
              <textarea v-model="item.observations" rows="2" placeholder="Detalle del hallazgo, si aplica."></textarea>
            </label>
            <button class="button danger icon-only" type="button" title="Quitar ítem" @click="removeChecklistItem(index)">
              <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
            </button>
          </article>
        </section>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="saving" @click="closeExecution">Cancelar</button>
          <button class="button navy" type="submit" :disabled="saving">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ saving ? "Guardando..." : "Guardar inspección" }}</span>
          </button>
        </div>
      </form>
    </div>
  </section>
</template>
