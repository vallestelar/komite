<script setup lang="ts">
type MaintenanceTemplate = {
  id: string;
  name: string;
  template_type?: string;
  version: number;
  status: string;
  effective_from?: string | null;
  effective_to?: string | null;
};

type MaintenanceItem = {
  id: string;
  condominium_template_id: string;
  section_name?: string | null;
  asset_name?: string | null;
  task_name: string;
  instructions?: string | null;
  periodicity?: string | null;
  planned_months: Array<number | string>;
  responsible_user_id?: string | null;
  responsible_profile?: string | null;
  estimated_duration_minutes?: number | null;
  priority: string;
  status: string;
};

type MaintenanceResponse = {
  templates: MaintenanceTemplate[];
  selected_template?: MaintenanceTemplate | null;
  items: MaintenanceItem[];
};

type ItemForm = {
  id: string;
  section_name: string;
  asset_name: string;
  task_name: string;
  instructions: string;
  periodicity: string;
  planned_months: number[];
  responsible_profile: string;
  estimated_duration_minutes: string;
  priority: string;
  status: string;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const templates = ref<MaintenanceTemplate[]>([]);
const selectedTemplateId = ref("");
const selectedTemplate = ref<MaintenanceTemplate | null>(null);
const items = ref<MaintenanceItem[]>([]);
const search = ref("");
const statusFilter = ref("");
const errorMessage = ref("");
const toastMessage = ref("");
const loading = ref(false);
const editMode = ref(false);
const formMode = ref<"create" | "edit">("edit");

const itemForm = reactive<ItemForm>({
  id: "",
  section_name: "",
  asset_name: "",
  task_name: "",
  instructions: "",
  periodicity: "monthly",
  planned_months: [],
  responsible_profile: "supervisor",
  estimated_duration_minutes: "",
  priority: "medium",
  status: "active",
});

const monthOptions = [
  [1, "Ene"],
  [2, "Feb"],
  [3, "Mar"],
  [4, "Abr"],
  [5, "May"],
  [6, "Jun"],
  [7, "Jul"],
  [8, "Ago"],
  [9, "Sep"],
  [10, "Oct"],
  [11, "Nov"],
  [12, "Dic"],
] as const;

const periodicityOptions = [
  ["daily", "Diaria"],
  ["weekly", "Semanal"],
  ["biweekly", "Quincenal"],
  ["monthly", "Mensual"],
  ["bimonthly", "Cada 2 meses"],
  ["quarterly", "Trimestral"],
  ["four_monthly", "Cada 4 meses"],
  ["semiannual", "Semestral"],
  ["annual", "Anual"],
  ["biennial", "Cada 2 años"],
  ["permanent", "Permanente"],
  ["on_demand", "Según necesidad"],
];

const profileOptions = [
  ["", "Sin responsable sugerido"],
  ["project_manager", "Project manager"],
  ["supervisor", "Supervisor"],
  ["ejecutivo", "Ejecutivo/a"],
  ["conserje", "Conserje"],
];

const priorityOptions = [
  ["low", "Baja"],
  ["medium", "Media"],
  ["high", "Alta"],
  ["urgent", "Urgente"],
];

const statusOptions = [
  ["active", "Activo"],
  ["inactive", "Inactivo"],
  ["draft", "Borrador"],
  ["paused", "Pausado"],
];

const activeItems = computed(() => items.value.filter((item) => item.status === "active"));
const inactiveItems = computed(() => items.value.filter((item) => item.status !== "active"));
const sectionCount = computed(() => new Set(items.value.map((item) => item.section_name || "Sin sección")).size);
const formTitle = computed(() => formMode.value === "create" ? "Nueva tarea" : "Editar tarea");

const filteredItems = computed(() => {
  const normalizedSearch = normalize(search.value);
  return items.value.filter((item) => {
    const matchesStatus = !statusFilter.value || item.status === statusFilter.value;
    const text = normalize(`${item.section_name || ""} ${item.asset_name || ""} ${item.task_name} ${item.instructions || ""}`);
    return matchesStatus && (!normalizedSearch || text.includes(normalizedSearch));
  });
});

const groupedItems = computed(() => {
  const groups = new Map<string, MaintenanceItem[]>();
  for (const item of filteredItems.value) {
    const section = item.section_name || "Sin sección";
    groups.set(section, [...(groups.get(section) || []), item]);
  }
  return Array.from(groups.entries()).map(([section, sectionItems]) => ({ section, items: sectionItems }));
});

const title = computed(() => selectedTemplate.value?.name || "Plan de mantenciones");

const loadPlan = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    if (selectedTemplateId.value) params.set("template_id", selectedTemplateId.value);
    const data = await request<MaintenanceResponse>(`/api/v1/portal/maintenance/?${params}`);
    templates.value = data.templates || [];
    selectedTemplate.value = data.selected_template || null;
    selectedTemplateId.value = data.selected_template?.id || templates.value[0]?.id || "";
    items.value = data.items || [];
    editMode.value = false;
  } catch (error) {
    items.value = [];
    templates.value = [];
    selectedTemplate.value = null;
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const resetItemForm = () => {
  itemForm.id = "";
  itemForm.section_name = "";
  itemForm.asset_name = "";
  itemForm.task_name = "";
  itemForm.instructions = "";
  itemForm.periodicity = "monthly";
  itemForm.planned_months = [];
  itemForm.responsible_profile = "supervisor";
  itemForm.estimated_duration_minutes = "";
  itemForm.priority = "medium";
  itemForm.status = "active";
};

const openNewItem = () => {
  if (!selectedTemplateId.value) return;
  resetItemForm();
  formMode.value = "create";
  editMode.value = true;
};

const openEditItem = (item: MaintenanceItem) => {
  itemForm.id = item.id;
  itemForm.section_name = item.section_name || "";
  itemForm.asset_name = item.asset_name || "";
  itemForm.task_name = item.task_name || "";
  itemForm.instructions = item.instructions || "";
  itemForm.periodicity = item.periodicity || "monthly";
  itemForm.planned_months = (item.planned_months || []).map((month) => Number(month)).filter((month) => Number.isFinite(month));
  itemForm.responsible_profile = item.responsible_profile || "";
  itemForm.estimated_duration_minutes = item.estimated_duration_minutes ? String(item.estimated_duration_minutes) : "";
  itemForm.priority = item.priority || "medium";
  itemForm.status = item.status || "active";
  formMode.value = "edit";
  editMode.value = true;
};

const closeEdit = () => {
  editMode.value = false;
  resetItemForm();
};

const toggleMonth = (month: number) => {
  itemForm.planned_months = itemForm.planned_months.includes(month)
    ? itemForm.planned_months.filter((item) => item !== month)
    : [...itemForm.planned_months, month].sort((left, right) => left - right);
};

const saveItem = async () => {
  if (!selectedTemplateId.value || !itemForm.task_name.trim()) {
    errorMessage.value = "Indica al menos el nombre de la tarea.";
    return;
  }
  try {
    const payload = {
      condominium_template_id: selectedTemplateId.value,
      section_name: itemForm.section_name || null,
      asset_name: itemForm.asset_name || null,
      task_name: itemForm.task_name.trim(),
      instructions: itemForm.instructions || null,
      periodicity: itemForm.periodicity || null,
      planned_months: itemForm.planned_months,
      responsible_profile: itemForm.responsible_profile || null,
      estimated_duration_minutes: itemForm.estimated_duration_minutes ? Number(itemForm.estimated_duration_minutes) : null,
      priority: itemForm.priority,
      status: itemForm.status,
    };
    const endpoint = formMode.value === "create"
      ? "/api/v1/portal/maintenance/items"
      : `/api/v1/portal/maintenance/items/${itemForm.id}`;
    const updated = await request<MaintenanceItem>(endpoint, {
      method: formMode.value === "create" ? "POST" : "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    items.value = formMode.value === "create"
      ? [...items.value, updated]
      : items.value.map((item) => item.id === updated.id ? updated : item);
    toastMessage.value = formMode.value === "create" ? "Tarea creada correctamente." : "Mantención actualizada correctamente.";
    closeEdit();
    window.setTimeout(() => {
      toastMessage.value = "";
    }, 2800);
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const periodicityLabel = (value: string | null | undefined) => periodicityOptions.find(([key]) => key === value)?.[1] || value || "";
const profileLabel = (value: string | null | undefined) => profileOptions.find(([key]) => key === value)?.[1] || value || "Sin responsable";
const priorityLabel = (value: string | null | undefined) => priorityOptions.find(([key]) => key === value)?.[1] || value || "";
const statusLabel = (value: string | null | undefined) => statusOptions.find(([key]) => key === value)?.[1] || value || "Sin estado";

const statusBadgeClass = (status: string | null | undefined) => {
  if (status === "active") return "is-active";
  if (status === "inactive") return "is-inactive";
  return "is-neutral";
};

const monthLabel = (value: number | string) => monthOptions.find(([month]) => month === Number(value))?.[1] || String(value);

const normalize = (value: string) => value
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g, "")
  .toLowerCase()
  .trim();

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo cargar el plan de mantenciones.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

watch(activeCondominium, () => {
  selectedTemplateId.value = "";
  loadPlan();
});

watch(selectedTemplateId, (next, previous) => {
  if (next && previous && next !== previous) loadPlan();
});

onMounted(loadPlan);
</script>

<template>
  <section class="panel maintenance-panel">
    <div class="dashboard-hero maintenance-hero">
      <div>
        <p class="eyebrow">Mantenciones</p>
        <h2>{{ title }}</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary">
        <article>
          <span>Items activos</span>
          <strong>{{ activeItems.length }}</strong>
        </article>
        <article>
          <span>Secciones</span>
          <strong>{{ sectionCount }}</strong>
        </article>
        <article>
          <span>No activos</span>
          <strong>{{ inactiveItems.length }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
    <p v-if="toastMessage" class="success-message">{{ toastMessage }}</p>

    <div v-if="templates.length" class="maintenance-toolbar">
      <label>
        Plantilla del condominio
        <select v-model="selectedTemplateId">
          <option v-for="template in templates" :key="template.id" :value="template.id">
            {{ template.name }} · v{{ template.version }}
          </option>
        </select>
      </label>
      <label>
        Estado
        <select v-model="statusFilter">
          <option value="">Todos los estados</option>
          <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
        </select>
      </label>
      <label>
        Buscar
        <input v-model="search" type="search" placeholder="Buscar sección, activo o tarea" />
      </label>
      <button class="button ghost" type="button" :disabled="loading" @click="loadPlan">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
      <button class="button orange" type="button" :disabled="loading || !selectedTemplateId" @click="openNewItem">
        <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
        <span>Nueva tarea</span>
      </button>
    </div>

    <div v-if="!templates.length && !errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-clipboard" /></svg>
      </span>
      <h2>Sin plantilla de mantenciones</h2>
      <p class="placeholder-copy">Duplica una plantilla desde el backoffice para este condominio.</p>
    </div>

    <div v-else class="maintenance-layout" :class="{ 'is-editing': editMode }">
      <div class="maintenance-list">
        <section v-for="group in groupedItems" :key="group.section" class="maintenance-section">
          <header>
            <h3>{{ group.section }}</h3>
            <span>{{ group.items.length }} tareas</span>
          </header>
          <div class="edifito-table-wrap entity-table-wrap">
            <table class="edifito-table entity-table maintenance-table">
              <thead>
                <tr>
                  <th>Activo / zona</th>
                  <th>Tarea</th>
                  <th>Periodicidad</th>
                  <th>Meses</th>
                  <th>Responsable</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in group.items" :key="item.id">
                  <td>{{ item.asset_name || "" }}</td>
                  <td>
                    <strong>{{ item.task_name }}</strong>
                    <small v-if="item.instructions">{{ item.instructions }}</small>
                  </td>
                  <td>{{ periodicityLabel(item.periodicity) }}</td>
                  <td>
                    <span v-if="item.planned_months?.length" class="month-list">
                      <span v-for="month in item.planned_months" :key="month">{{ monthLabel(month) }}</span>
                    </span>
                    <span v-else>Sin meses</span>
                  </td>
                  <td>{{ profileLabel(item.responsible_profile) }}</td>
                  <td>
                    <span class="status-badge" :class="statusBadgeClass(item.status)">
                      <span aria-hidden="true"></span>
                      {{ statusLabel(item.status) }}
                    </span>
                  </td>
                  <td class="actions-cell">
                    <div class="actions-inline">
                      <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditItem(item)">
                        <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <aside v-if="editMode" class="maintenance-editor">
        <div class="entity-header compact-header">
          <div>
            <p class="eyebrow">{{ formMode === "create" ? "Nueva mantención" : "Editar item" }}</p>
            <h2>{{ formTitle }}</h2>
          </div>
          <button class="button ghost icon-only" type="button" title="Cerrar" @click="closeEdit">
            <svg class="icon" aria-hidden="true"><use href="#icon-chevron-right" /></svg>
          </button>
        </div>
        <form class="entity-form" @submit.prevent="saveItem">
          <label>
            Sección
            <input v-model="itemForm.section_name" type="text" placeholder="Ej. Agua potable y alcantarillado" maxlength="150" />
          </label>
          <label>
            Activo / zona
            <input v-model="itemForm.asset_name" type="text" placeholder="Ej. Sala de bombas" maxlength="180" />
          </label>
          <label>
            Tarea
            <input v-model="itemForm.task_name" type="text" required placeholder="Nombre de la tarea" maxlength="255" />
          </label>
          <label>
            Instrucciones
            <textarea v-model="itemForm.instructions" rows="4" />
          </label>
          <label>
            Periodicidad
            <select v-model="itemForm.periodicity">
              <option v-for="[value, label] in periodicityOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label>
            Responsable sugerido
            <select v-model="itemForm.responsible_profile">
              <option v-for="[value, label] in profileOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label>
            Duración estimada min.
            <input v-model="itemForm.estimated_duration_minutes" type="number" min="0" step="1" />
          </label>
          <label>
            Prioridad
            <select v-model="itemForm.priority">
              <option v-for="[value, label] in priorityOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label>
            Estado
            <select v-model="itemForm.status">
              <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <div>
            <span class="field-label">Meses planificados</span>
            <div class="month-picker">
              <button
                v-for="[month, label] in monthOptions"
                :key="month"
                class="month-chip"
                :class="{ selected: itemForm.planned_months.includes(month) }"
                type="button"
                @click="toggleMonth(month)"
              >
                {{ label }}
              </button>
            </div>
          </div>
          <div class="form-actions">
            <button class="button navy" type="submit">
              <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
              <span>Guardar</span>
            </button>
          </div>
        </form>
      </aside>
    </div>
  </section>
</template>
