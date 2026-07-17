<script setup lang="ts">
type PageMeta = {
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

type PeriodRecord = {
  id: string;
  condominium_id: string;
  name: string;
  description?: string | null;
  start_date: string;
  end_date: string;
  status: string;
  is_active: boolean;
  reserve_fund_rate: number | string;
};

type MovementRecord = {
  id: string;
  period_id: string;
};

type RunRecord = {
  id: string;
  period_id: string;
};

type PeriodForm = {
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  status: string;
  reserve_fund_rate: string;
  is_active: boolean;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const periods = ref<PeriodRecord[]>([]);
const incomes = ref<MovementRecord[]>([]);
const expenses = ref<MovementRecord[]>([]);
const runs = ref<RunRecord[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const periodFormError = ref("");
const toastMessage = ref("");
const editingPeriodId = ref("");
const isPeriodModalOpen = ref(false);
const deleteCandidate = ref<PeriodRecord | null>(null);

const form = reactive<PeriodForm>({
  name: "",
  description: "",
  start_date: "",
  end_date: "",
  status: "draft",
  reserve_fund_rate: "0.05",
  is_active: false,
});

const statusOptions = [
  ["draft", "Borrador"],
  ["upcoming", "Próximo"],
  ["open", "Abierto"],
  ["closed", "Cerrado"],
  ["blocked", "Bloqueado"],
  ["cancelled", "Anulado"],
];

const sortedPeriods = computed(() => [...periods.value].sort((left, right) => {
  const byStart = left.start_date.localeCompare(right.start_date);
  if (byStart !== 0) return byStart;
  return left.end_date.localeCompare(right.end_date);
}));

const activeCount = computed(() => periods.value.filter((period) => period.is_active).length);
const closedCount = computed(() => periods.value.filter((period) => period.status === "closed").length);
const currentPeriod = computed(() => periods.value.find((period) => period.is_active) || null);

const usageByPeriod = computed(() => {
  const usage: Record<string, { incomes: number; expenses: number; runs: number }> = {};
  for (const period of periods.value) usage[period.id] = { incomes: 0, expenses: 0, runs: 0 };
  for (const income of incomes.value) if (usage[income.period_id]) usage[income.period_id].incomes += 1;
  for (const expense of expenses.value) if (usage[expense.period_id]) usage[expense.period_id].expenses += 1;
  for (const run of runs.value) if (usage[run.period_id]) usage[run.period_id].runs += 1;
  return usage;
});

const formatDate = (value: string | null | undefined) => {
  if (!value) return "";
  const [datePart] = value.split("T");
  const parts = datePart.split("-");
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : value;
};

const reservePercent = (value: number | string | null | undefined) => `${(Number(value || 0) * 100).toLocaleString("es-CL", { maximumFractionDigits: 2 })}%`;

const statusLabel = (status: string | null | undefined) => statusOptions.find(([value]) => value === status)?.[1] || "Sin estado";

const statusBadgeClass = (period: PeriodRecord) => {
  if (period.is_active) return "is-active";
  if (period.status === "closed") return "is-closed";
  if (period.status === "blocked") return "is-blocked";
  if (period.status === "cancelled") return "is-cancelled";
  if (period.status === "open") return "is-open";
  if (period.status === "upcoming") return "is-upcoming";
  return "is-draft";
};

const numericValue = (value: string) => Number(value.replace(",", ".") || 0);

const findOverlappingPeriod = () => {
  if (!form.start_date || !form.end_date) return null;
  return periods.value.find((period) => {
    if (period.id === editingPeriodId.value) return false;
    return period.start_date <= form.end_date && period.end_date >= form.start_date;
  }) || null;
};

const readableError = (error: unknown) => {
  const raw = String((error as { message?: string })?.message || error || "Error inesperado");
  try {
    const parsed = JSON.parse(raw);
    return parsed.detail || raw;
  } catch {
    return raw;
  }
};

const showToast = (message: string) => {
  toastMessage.value = message;
  setTimeout(() => {
    if (toastMessage.value === message) toastMessage.value = "";
  }, 3000);
};

const resetForm = () => {
  editingPeriodId.value = "";
  periodFormError.value = "";
  Object.assign(form, {
    name: "",
    description: "",
    start_date: "",
    end_date: "",
    status: "draft",
    reserve_fund_rate: "0.05",
    is_active: false,
  });
};

const openCreatePeriod = () => {
  resetForm();
  errorMessage.value = "";
  isPeriodModalOpen.value = true;
};

const closePeriodModal = () => {
  isPeriodModalOpen.value = false;
  resetForm();
};

const loadPeriods = async () => {
  if (!activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const [periodPage, incomePage, expensePage, runPage] = await Promise.all([
      request<{ items?: PeriodRecord[]; meta?: PageMeta }>("/api/v1/accounting-periods/?page_size=100&order_by=-start_date"),
      request<{ items?: MovementRecord[]; meta?: PageMeta }>("/api/v1/accounting-incomes/?page_size=200"),
      request<{ items?: MovementRecord[]; meta?: PageMeta }>("/api/v1/accounting-expenses/?page_size=200"),
      request<{ items?: RunRecord[]; meta?: PageMeta }>("/api/v1/common-expense-runs/?page_size=200"),
    ]);
    periods.value = periodPage.items || [];
    incomes.value = incomePage.items || [];
    expenses.value = expensePage.items || [];
    runs.value = runPage.items || [];
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const editPeriod = (period: PeriodRecord) => {
  errorMessage.value = "";
  periodFormError.value = "";
  editingPeriodId.value = period.id;
  Object.assign(form, {
    name: period.name,
    description: period.description || "",
    start_date: period.start_date,
    end_date: period.end_date,
    status: period.status || "draft",
    reserve_fund_rate: String(period.reserve_fund_rate ?? "0"),
    is_active: period.is_active,
  });
  isPeriodModalOpen.value = true;
};

const savePeriod = async () => {
  if (!activeCondominium.value?.id) return;
  periodFormError.value = "";
  if (form.start_date && form.end_date && form.end_date < form.start_date) {
    periodFormError.value = "La fecha de fin no puede ser anterior a la fecha de inicio.";
    return;
  }
  const overlappingPeriod = findOverlappingPeriod();
  if (overlappingPeriod) {
    periodFormError.value = `El periodo pisa fechas de ${overlappingPeriod.name} (${formatDate(overlappingPeriod.start_date)} - ${formatDate(overlappingPeriod.end_date)}). Ajusta el intervalo para que no comparta ni un dia.`;
    return;
  }
  try {
    const wasEditing = Boolean(editingPeriodId.value);
    const isTerminal = ["closed", "blocked", "cancelled"].includes(form.status);
    const path = editingPeriodId.value ? `/api/v1/accounting-periods/${editingPeriodId.value}` : "/api/v1/accounting-periods/";
    await request<PeriodRecord>(path, {
      method: editingPeriodId.value ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        condominium_id: activeCondominium.value.id,
        name: form.name.trim(),
        description: form.description.trim() || null,
        start_date: form.start_date,
        end_date: form.end_date,
        status: form.is_active ? "open" : form.status,
        is_active: isTerminal ? false : form.is_active,
        reserve_fund_rate: numericValue(form.reserve_fund_rate),
        metadata: {},
      }),
    });
    closePeriodModal();
    showToast(wasEditing ? "Periodo actualizado correctamente." : "Periodo creado correctamente.");
    await loadPeriods();
  } catch (error) {
    periodFormError.value = readableError(error);
  }
};

const askDelete = (period: PeriodRecord) => {
  deleteCandidate.value = period;
};

const cancelDelete = () => {
  deleteCandidate.value = null;
};

const confirmDelete = async () => {
  if (!deleteCandidate.value) return;
  errorMessage.value = "";
  try {
    await request(`/api/v1/accounting-periods/${deleteCandidate.value.id}`, { method: "DELETE" });
    deleteCandidate.value = null;
    resetForm();
    showToast("Periodo eliminado correctamente.");
    await loadPeriods();
  } catch (error) {
    errorMessage.value = readableError(error);
    deleteCandidate.value = null;
  }
};

watch(() => activeCondominium.value?.id, loadPeriods, { immediate: true });
</script>

<template>
  <section class="panel periods-panel">
    <div class="dashboard-hero periods-hero">
      <div>
        <p class="eyebrow">Contabilidad</p>
        <h2>Periodos contables</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Condominio activo" }}</p>
      </div>
      <div class="committee-summary">
        <article>
          <span>Activo</span>
          <strong>{{ currentPeriod?.name || "Sin periodo" }}</strong>
        </article>
        <article>
          <span>Total</span>
          <strong>{{ periods.length }}</strong>
        </article>
        <article>
          <span>Cerrados</span>
          <strong>{{ closedCount }}</strong>
        </article>
      </div>
      <button class="button orange" type="button" @click="openCreatePeriod">
        <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
        <span>Nuevo periodo</span>
      </button>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
    <p v-if="toastMessage" class="success-message">{{ toastMessage }}</p>
    <p v-if="activeCount > 1" class="periods-warning">Hay más de un periodo activo. Al guardar uno como activo, el sistema normalizará el resto.</p>

    <div class="periods-layout">
      <form v-if="false" class="entity-form period-form" @submit.prevent="savePeriod">
        <div class="period-form-grid">
          <label class="span-all">
            Descripción
            <textarea v-model="form.description" rows="3" />
          </label>
        </div>
        <div class="form-actions">
          <button v-if="editingPeriodId" class="button ghost" type="button" @click="resetForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
            <span>Cancelar</span>
          </button>
          <button class="button navy" type="submit">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ editingPeriodId ? "Actualizar periodo" : "Guardar periodo" }}</span>
          </button>
        </div>
      </form>

      <div v-if="sortedPeriods.length" class="periods-grid">
        <article v-for="period in sortedPeriods" :key="period.id" class="period-card" :class="{ 'is-active-period': period.is_active }">
          <div class="period-card-header">
            <span class="committee-avatar" aria-hidden="true">
              <svg class="icon"><use href="#icon-calendar" /></svg>
            </span>
            <div>
              <p class="committee-position">{{ formatDate(period.start_date) }} - {{ formatDate(period.end_date) }}</p>
              <h3>{{ period.name }}</h3>
            </div>
            <span class="status-badge" :class="statusBadgeClass(period)">
              <span aria-hidden="true"></span>
              {{ period.is_active ? "Activo" : statusLabel(period.status) }}
            </span>
          </div>

          <div class="period-facts">
            <p>
              <svg class="icon" aria-hidden="true"><use href="#icon-percent" /></svg>
              <span>Fondo de reserva</span>
              <strong>{{ reservePercent(period.reserve_fund_rate) }}</strong>
            </p>
            <p>
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Ingresos</span>
              <strong>{{ usageByPeriod[period.id]?.incomes || 0 }}</strong>
            </p>
            <p>
              <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
              <span>Egresos</span>
              <strong>{{ usageByPeriod[period.id]?.expenses || 0 }}</strong>
            </p>
            <p>
              <svg class="icon" aria-hidden="true"><use href="#icon-calculator" /></svg>
              <span>Cálculos</span>
              <strong>{{ usageByPeriod[period.id]?.runs || 0 }}</strong>
            </p>
          </div>

          <p v-if="period.description" class="committee-notes">{{ period.description }}</p>

          <div class="committee-card-actions period-actions">
            <button class="button compact ghost" type="button" @click="editPeriod(period)">
              <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
              <span>Editar</span>
            </button>
            <button class="button compact danger" type="button" @click="askDelete(period)">
              <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
              <span>Borrar</span>
            </button>
          </div>
        </article>
      </div>

      <div v-else-if="!loading" class="committee-empty periods-empty">
        <span class="committee-avatar large" aria-hidden="true">
          <svg class="icon"><use href="#icon-calendar" /></svg>
        </span>
        <h2>Sin periodos registrados</h2>
        <p class="placeholder-copy">Crea el primer periodo contable para empezar a registrar ingresos, egresos y gastos comunes.</p>
      </div>
    </div>
  </section>

  <div v-if="isPeriodModalOpen" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="period-modal-title">
    <form class="confirm-modal period-modal" @submit.prevent="savePeriod">
      <div class="period-modal-header">
        <div>
          <p class="eyebrow">Periodo contable</p>
          <h2 id="period-modal-title">{{ editingPeriodId ? "Editar periodo" : "Nuevo periodo" }}</h2>
        </div>
        <button class="button ghost icon-only" type="button" aria-label="Cerrar" title="Cerrar" @click="closePeriodModal">
          <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
        </button>
      </div>
      <p v-if="periodFormError" class="form-error result-message period-modal-error">{{ periodFormError }}</p>
      <div class="period-form-grid">
        <label>
          Nombre
          <input v-model="form.name" required maxlength="120" placeholder="Agosto 2026" />
        </label>
        <label>
          Estado
          <select v-model="form.status">
            <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Inicio
          <input v-model="form.start_date" required type="date" />
        </label>
        <label>
          Fin
          <input v-model="form.end_date" required type="date" />
        </label>
        <label>
          Fondo reserva
          <input v-model="form.reserve_fund_rate" required inputmode="decimal" placeholder="0.05" />
        </label>
        <label class="switch-field period-active-field">
          <input v-model="form.is_active" type="checkbox" :disabled="['closed', 'blocked', 'cancelled'].includes(form.status)" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Periodo activo</span>
        </label>
        <label class="span-all">
          Descripción
          <textarea v-model="form.description" rows="3" />
        </label>
      </div>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="closePeriodModal">Cancelar</button>
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>{{ editingPeriodId ? "Actualizar periodo" : "Guardar periodo" }}</span>
        </button>
      </div>
    </form>
  </div>

  <div v-if="deleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-period-title">
    <div class="confirm-modal">
      <p class="eyebrow">Eliminar periodo</p>
      <h2 id="delete-period-title">{{ deleteCandidate.name }}</h2>
      <p>Solo se eliminará si no tiene ingresos, egresos ni cálculos de gasto común asociados.</p>
      <p v-if="deleteCandidate.is_active" class="periods-warning">Este periodo está activo. Si se elimina, el condominio quedará sin periodo activo.</p>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="cancelDelete">Cancelar</button>
        <button class="button danger" type="button" @click="confirmDelete">
          <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
          <span>Eliminar periodo</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.periods-panel {
  display: grid;
  gap: 18px;
}

.periods-hero {
  align-items: stretch;
}

.periods-hero .committee-summary {
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  margin-left: auto;
}

.periods-layout {
  min-width: 0;
}

.period-modal {
  display: grid;
  gap: 16px;
  width: min(720px, 100%);
}

.period-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.period-modal select,
.period-modal textarea {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 9px 11px;
  color: var(--text);
  background: var(--white);
  font: inherit;
}

.period-modal textarea {
  resize: vertical;
}

.period-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.period-form-grid .span-all {
  grid-column: 1 / -1;
}

.periods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}

.period-card {
  display: grid;
  gap: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
  background: #fbfcfe;
}

.period-card.is-active-period {
  border-color: rgba(6, 118, 71, 0.3);
  box-shadow: inset 0 0 0 1px rgba(6, 118, 71, 0.08);
}

.period-card-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: flex-start;
  gap: 12px;
}

.period-card h3 {
  margin: 0;
  color: var(--navy);
  font-size: 17px;
  line-height: 1.25;
}

.period-facts {
  display: grid;
  gap: 8px;
}

.period-facts p {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.period-facts strong {
  color: var(--navy);
}

.period-actions {
  gap: 8px;
}

.period-active-field {
  align-self: end;
  min-height: 42px;
}

.periods-warning {
  margin: 0;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  padding: 10px 12px;
  color: #9a3412;
  background: #fff7ed;
  font-weight: 700;
}

.status-badge.is-open,
.status-badge.is-upcoming {
  color: #175cd3;
  background: #eff8ff;
}

.status-badge.is-draft {
  color: #475467;
  background: #f2f4f7;
}

.status-badge.is-closed {
  color: #5925dc;
  background: #f4f3ff;
}

.status-badge.is-blocked,
.status-badge.is-cancelled {
  color: #b42318;
  background: #fef3f2;
}

.success-message {
  margin: 0;
  color: #067647;
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .periods-grid {
    grid-template-columns: 1fr;
  }

  .periods-hero .committee-summary {
    margin-left: 0;
  }

  .period-card-header {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .period-card-header .status-badge {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
