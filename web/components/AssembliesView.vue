<script setup lang="ts">
type AssemblyAttendee = {
  name: string;
  email?: string | null;
  role?: string | null;
  attendance_status: string;
  notes?: string | null;
};

type AssemblyAgendaItem = {
  id?: string | null;
  title: string;
  description?: string | null;
  owner?: string | null;
  conclusion?: string | null;
  status: string;
};

type Assembly = {
  id: string;
  title: string;
  description?: string | null;
  assembly_type: string;
  status: string;
  scheduled_date: string;
  scheduled_start_time?: string | null;
  estimated_duration_hours?: number | null;
  location?: string | null;
  modality: string;
  quorum_required?: number | null;
  attendees: AssemblyAttendee[];
  agenda_items: AssemblyAgendaItem[];
  conclusions?: string | null;
};

type AssembliesResponse = {
  items: Assembly[];
  summary: Record<string, number>;
};

const { request } = useApi();
const { activeCondominium, token } = useAuth();
const config = useRuntimeConfig();

const assemblies = ref<Assembly[]>([]);
const summary = ref<Record<string, number>>({});
const loading = ref(false);
const saving = ref(false);
const downloadingId = ref("");
const errorMessage = ref("");
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(String(new Date().getMonth() + 1));
const selectedStatus = ref("");
const search = ref("");
const editingAssembly = ref<Assembly | null>(null);
const showForm = ref(false);

const form = reactive({
  title: "",
  description: "",
  assembly_type: "ordinary",
  status: "scheduled",
  scheduled_date: new Date().toISOString().slice(0, 10),
  scheduled_start_time: "",
  estimated_duration_hours: "",
  location: "",
  modality: "presential",
  quorum_required: "",
  conclusions: "",
  attendees: [] as AssemblyAttendee[],
  agenda_items: [] as AssemblyAgendaItem[],
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
  ["scheduled", "Programada"],
  ["in_progress", "En curso"],
  ["closed", "Cerrada"],
  ["cancelled", "Cancelada"],
] as const;

const yearOptions = computed(() => {
  const current = new Date().getFullYear();
  return [current - 1, current, current + 1, current + 2];
});

const visibleAssemblies = computed(() => {
  const query = normalize(search.value);
  if (!query) return assemblies.value;
  return assemblies.value.filter((assembly) => normalize([
    assembly.title,
    assembly.description || "",
    assembly.location || "",
    assembly.conclusions || "",
    ...(assembly.agenda_items || []).map((item) => `${item.title} ${item.owner || ""}`),
    ...(assembly.attendees || []).map((item) => `${item.name} ${item.email || ""} ${item.role || ""}`),
  ].join(" ")).includes(query));
});

const apiBase = computed(() => {
  if (import.meta.client) return localStorage.getItem("komite_api_base") || config.public.apiBase;
  return config.public.apiBase;
});

const loadAssemblies = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.set("year", String(selectedYear.value));
    if (selectedMonth.value) params.set("month", selectedMonth.value);
    if (selectedStatus.value) params.set("status", selectedStatus.value);
    const data = await request<AssembliesResponse>(`/api/v1/portal/assemblies/?${params}`);
    assemblies.value = data.items || [];
    summary.value = data.summary || {};
  } catch (error) {
    assemblies.value = [];
    summary.value = {};
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.title = "";
  form.description = "";
  form.assembly_type = "ordinary";
  form.status = "scheduled";
  form.scheduled_date = new Date().toISOString().slice(0, 10);
  form.scheduled_start_time = "";
  form.estimated_duration_hours = "";
  form.location = "";
  form.modality = "presential";
  form.quorum_required = "";
  form.conclusions = "";
  form.attendees = [emptyAttendee()];
  form.agenda_items = [emptyAgendaItem()];
};

const emptyAttendee = (): AssemblyAttendee => ({
  name: "",
  email: "",
  role: "",
  attendance_status: "expected",
  notes: "",
});

const emptyAgendaItem = (): AssemblyAgendaItem => ({
  id: crypto.randomUUID?.() || `point-${Date.now()}`,
  title: "",
  description: "",
  owner: "",
  conclusion: "",
  status: "pending",
});

const openCreate = () => {
  editingAssembly.value = null;
  resetForm();
  showForm.value = true;
};

const openEdit = (assembly: Assembly) => {
  editingAssembly.value = assembly;
  form.title = assembly.title;
  form.description = assembly.description || "";
  form.assembly_type = assembly.assembly_type || "ordinary";
  form.status = assembly.status || "scheduled";
  form.scheduled_date = assembly.scheduled_date;
  form.scheduled_start_time = assembly.scheduled_start_time || "";
  form.estimated_duration_hours = assembly.estimated_duration_hours ? String(assembly.estimated_duration_hours) : "";
  form.location = assembly.location || "";
  form.modality = assembly.modality || "presential";
  form.quorum_required = assembly.quorum_required ? String(assembly.quorum_required) : "";
  form.conclusions = assembly.conclusions || "";
  form.attendees = assembly.attendees?.length ? assembly.attendees.map((item) => ({ ...item })) : [emptyAttendee()];
  form.agenda_items = assembly.agenda_items?.length ? assembly.agenda_items.map((item) => ({ ...item })) : [emptyAgendaItem()];
  showForm.value = true;
};

const closeForm = () => {
  if (saving.value) return;
  showForm.value = false;
  editingAssembly.value = null;
};

const saveAssembly = async () => {
  if (!form.title.trim()) {
    errorMessage.value = "Indica el nombre de la asamblea.";
    return;
  }
  saving.value = true;
  errorMessage.value = "";
  try {
    const endpoint = editingAssembly.value
      ? `/api/v1/portal/assemblies/${editingAssembly.value.id}`
      : "/api/v1/portal/assemblies/";
    const saved = await request<Assembly>(endpoint, {
      method: editingAssembly.value ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    assemblies.value = editingAssembly.value
      ? assemblies.value.map((assembly) => assembly.id === saved.id ? saved : assembly)
      : [...assemblies.value, saved];
    assemblies.value = [...assemblies.value].sort((left, right) => {
      const dateCompare = left.scheduled_date.localeCompare(right.scheduled_date);
      return dateCompare || (left.scheduled_start_time || "").localeCompare(right.scheduled_start_time || "");
    });
    selectedYear.value = Number(saved.scheduled_date.slice(0, 4));
    selectedMonth.value = String(Number(saved.scheduled_date.slice(5, 7)));
    recomputeSummary();
    showForm.value = false;
    editingAssembly.value = null;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    saving.value = false;
  }
};

const buildPayload = () => ({
  title: form.title.trim(),
  description: form.description.trim() || null,
  assembly_type: form.assembly_type,
  status: form.status,
  scheduled_date: form.scheduled_date,
  scheduled_start_time: form.scheduled_start_time || null,
  estimated_duration_hours: optionalNumber(form.estimated_duration_hours),
  location: form.location.trim() || null,
  modality: form.modality,
  quorum_required: optionalNumber(form.quorum_required),
  attendees: form.attendees.filter((item) => item.name.trim()).map((item) => ({
    ...item,
    name: item.name.trim(),
    email: item.email?.trim() || null,
    role: item.role?.trim() || null,
    notes: item.notes?.trim() || null,
  })),
  agenda_items: form.agenda_items.filter((item) => item.title.trim()).map((item) => ({
    ...item,
    title: item.title.trim(),
    description: item.description?.trim() || null,
    owner: item.owner?.trim() || null,
    conclusion: item.conclusion?.trim() || null,
  })),
  conclusions: form.conclusions.trim() || null,
});

const recomputeSummary = () => {
  summary.value = {
    total: assemblies.value.length,
    scheduled: assemblies.value.filter((item) => item.status === "scheduled").length,
    in_progress: assemblies.value.filter((item) => item.status === "in_progress").length,
    closed: assemblies.value.filter((item) => item.status === "closed").length,
    cancelled: assemblies.value.filter((item) => item.status === "cancelled").length,
  };
};

const addAttendee = () => {
  form.attendees.push(emptyAttendee());
};

const removeAttendee = (index: number) => {
  form.attendees.splice(index, 1);
  if (!form.attendees.length) form.attendees.push(emptyAttendee());
};

const addAgendaItem = () => {
  form.agenda_items.push(emptyAgendaItem());
};

const removeAgendaItem = (index: number) => {
  form.agenda_items.splice(index, 1);
  if (!form.agenda_items.length) form.agenda_items.push(emptyAgendaItem());
};

const downloadPdf = async (assembly: Assembly) => {
  if (!token.value || !activeCondominium.value?.id) return;
  downloadingId.value = assembly.id;
  errorMessage.value = "";
  try {
    const response = await fetch(`${apiBase.value}/api/v1/portal/assemblies/${assembly.id}/summary.pdf`, {
      headers: {
        Authorization: `Bearer ${token.value}`,
        "X-Condominium": activeCondominium.value.id,
      },
    });
    if (!response.ok) throw new Error(await response.text());
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `asamblea-${assembly.scheduled_date}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    downloadingId.value = "";
  }
};

const optionalNumber = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const formatDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(year, month - 1, day));
};

const statusLabel = (status: string | null | undefined) => {
  if (status === "scheduled") return "Programada";
  if (status === "in_progress") return "En curso";
  if (status === "closed") return "Cerrada";
  if (status === "cancelled") return "Cancelada";
  return status || "Sin estado";
};

const statusBadgeClass = (status: string | null | undefined) => {
  if (status === "closed") return "is-active";
  if (status === "cancelled") return "is-inactive";
  if (status === "in_progress") return "is-progress";
  if (status === "scheduled") return "is-pending";
  return "is-neutral";
};

const assemblyTypeLabel = (value: string) => {
  if (value === "extraordinary") return "Extraordinaria";
  if (value === "committee") return "Comité";
  if (value === "informative") return "Informativa";
  return "Ordinaria";
};

const modalityLabel = (value: string) => {
  if (value === "online") return "Online";
  if (value === "hybrid") return "Híbrida";
  return "Presencial";
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudieron cargar las asambleas.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

const normalize = (value: string) => value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();

watch([selectedYear, selectedMonth, selectedStatus], loadAssemblies);
watch([() => activeCondominium.value?.id, token], loadAssemblies);
onMounted(loadAssemblies);
</script>

<template>
  <section class="panel assemblies-panel">
    <div class="dashboard-hero assemblies-hero">
      <div>
        <p class="eyebrow">Asambleas</p>
        <h2>Gobierno y acuerdos del condominio</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary operational-summary">
        <article>
          <span>Total</span>
          <strong>{{ summary.total || 0 }}</strong>
        </article>
        <article>
          <span>Programadas</span>
          <strong>{{ summary.scheduled || 0 }}</strong>
        </article>
        <article>
          <span>Cerradas</span>
          <strong>{{ summary.closed || 0 }}</strong>
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
        <input v-model="search" type="search" placeholder="Buscar asamblea, punto o asistente" />
      </label>
      <button class="button ghost" type="button" :disabled="loading" @click="loadAssemblies">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <div class="operational-view-row">
      <p class="placeholder-copy">Registra convocatorias, asistentes, puntos tratados y conclusiones para generar actas rápidas.</p>
      <button class="button assembly-action" type="button" @click="openCreate">
        <svg class="icon" aria-hidden="true"><use href="#icon-users" /></svg>
        <span>Nueva asamblea</span>
      </button>
    </div>

    <div v-if="visibleAssemblies.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Asamblea</th>
            <th>Tipo</th>
            <th>Modalidad</th>
            <th>Asistentes</th>
            <th>Puntos</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="assembly in visibleAssemblies" :key="assembly.id">
            <td>
              <strong>{{ formatDate(assembly.scheduled_date) }}</strong>
              <small v-if="assembly.scheduled_start_time">{{ assembly.scheduled_start_time }}</small>
            </td>
            <td>
              <strong>{{ assembly.title }}</strong>
              <small>{{ assembly.location || "Sin lugar definido" }}</small>
            </td>
            <td>{{ assemblyTypeLabel(assembly.assembly_type) }}</td>
            <td>{{ modalityLabel(assembly.modality) }}</td>
            <td>{{ assembly.attendees?.length || 0 }}</td>
            <td>{{ assembly.agenda_items?.length || 0 }}</td>
            <td>
              <span class="status-badge" :class="statusBadgeClass(assembly.status)">
                <span aria-hidden="true"></span>
                {{ statusLabel(assembly.status) }}
              </span>
            </td>
            <td class="actions-cell">
              <button class="button compact icon-action navy" type="button" title="Editar asamblea" @click="openEdit(assembly)">
                <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
              </button>
              <button class="button compact icon-action ghost" type="button" title="Descargar resumen PDF" :disabled="downloadingId === assembly.id" @click="downloadPdf(assembly)">
                <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-users" /></svg>
      </span>
      <h2>Sin asambleas registradas</h2>
      <p class="placeholder-copy">Crea una asamblea para incorporarla a la agenda operativa del condominio.</p>
    </div>

    <div v-if="showForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="assembly-form-title">
      <form class="confirm-modal assembly-modal" @submit.prevent="saveAssembly">
        <div>
          <p class="eyebrow">Asambleas</p>
          <h2 id="assembly-form-title">{{ editingAssembly ? "Editar asamblea" : "Nueva asamblea" }}</h2>
          <p class="placeholder-copy">Define convocatoria, asistentes, puntos a tratar y conclusiones. La fecha quedará visible en la agenda operativa.</p>
        </div>

        <div class="entity-form-grid">
          <label class="span-two">
            Nombre
            <input v-model="form.title" type="text" maxlength="180" placeholder="Ej. Asamblea ordinaria de copropietarios" required />
          </label>
          <label>
            Fecha
            <input v-model="form.scheduled_date" type="date" required />
          </label>
          <label>
            Hora
            <input v-model="form.scheduled_start_time" type="time" />
          </label>
          <label>
            Tipo
            <select v-model="form.assembly_type">
              <option value="ordinary">Ordinaria</option>
              <option value="extraordinary">Extraordinaria</option>
              <option value="committee">Comité</option>
              <option value="informative">Informativa</option>
            </select>
          </label>
          <label>
            Modalidad
            <select v-model="form.modality">
              <option value="presential">Presencial</option>
              <option value="online">Online</option>
              <option value="hybrid">Híbrida</option>
            </select>
          </label>
          <label>
            Estado
            <select v-model="form.status">
              <option value="scheduled">Programada</option>
              <option value="in_progress">En curso</option>
              <option value="closed">Cerrada</option>
              <option value="cancelled">Cancelada</option>
            </select>
          </label>
          <label>
            Duración estimada (horas)
            <input v-model="form.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 1.5" />
          </label>
          <label>
            Lugar
            <input v-model="form.location" type="text" maxlength="180" placeholder="Ej. Salón multiuso" />
          </label>
          <label>
            Quórum requerido
            <input v-model="form.quorum_required" type="number" min="0" step="1" placeholder="Ej. 20" />
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="form.description" rows="3"></textarea>
          </label>
        </div>

        <section class="assembly-editor-block">
          <div class="section-heading-row">
            <div>
              <h3>Asistentes</h3>
              <p class="placeholder-copy">Puedes registrar convocados, asistentes reales o ausentes.</p>
            </div>
            <button class="button ghost compact" type="button" @click="addAttendee">
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Agregar</span>
            </button>
          </div>
          <div class="assembly-list-editor">
            <div v-for="(attendee, index) in form.attendees" :key="index" class="assembly-inline-row">
              <input v-model="attendee.name" type="text" placeholder="Nombre" />
              <input v-model="attendee.email" type="email" placeholder="Email" />
              <input v-model="attendee.role" type="text" placeholder="Rol / unidad" />
              <select v-model="attendee.attendance_status">
                <option value="expected">Convocado</option>
                <option value="present">Presente</option>
                <option value="absent">Ausente</option>
                <option value="represented">Representado</option>
              </select>
              <button class="button danger compact icon-action" type="button" title="Quitar asistente" @click="removeAttendee(index)">
                <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
              </button>
            </div>
          </div>
        </section>

        <section class="assembly-editor-block">
          <div class="section-heading-row">
            <div>
              <h3>Puntos a tratar</h3>
              <p class="placeholder-copy">Funciona como una pauta: punto, responsable y conclusión final.</p>
            </div>
            <button class="button ghost compact" type="button" @click="addAgendaItem">
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Agregar</span>
            </button>
          </div>
          <div class="assembly-list-editor">
            <div v-for="(point, index) in form.agenda_items" :key="point.id || index" class="assembly-point-row">
              <input v-model="point.title" type="text" placeholder="Punto a tratar" />
              <input v-model="point.owner" type="text" placeholder="Responsable" />
              <select v-model="point.status">
                <option value="pending">Pendiente</option>
                <option value="discussed">Tratado</option>
                <option value="approved">Aprobado</option>
                <option value="rejected">Rechazado</option>
              </select>
              <textarea v-model="point.description" rows="2" placeholder="Detalle del punto"></textarea>
              <textarea v-model="point.conclusion" rows="2" placeholder="Conclusión o acuerdo"></textarea>
              <button class="button danger compact icon-action" type="button" title="Quitar punto" @click="removeAgendaItem(index)">
                <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
              </button>
            </div>
          </div>
        </section>

        <label>
          Conclusiones generales
          <textarea v-model="form.conclusions" rows="4" placeholder="Acuerdos generales, próximos pasos o decisiones relevantes."></textarea>
        </label>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="saving" @click="closeForm">Cancelar</button>
          <button class="button navy" type="submit" :disabled="saving">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ saving ? "Guardando..." : editingAssembly ? "Guardar cambios" : "Crear asamblea" }}</span>
          </button>
        </div>
      </form>
    </div>
  </section>
</template>
