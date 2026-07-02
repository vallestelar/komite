<script setup lang="ts">
const props = defineProps<{
  view: string;
}>();

type BankOption = {
  id?: string;
  name: string;
  code?: string | null;
  status?: string;
};

type EdifitoRow = {
  monto: string;
  rut: string;
  nombre: string;
  fecha: string;
  documento: string;
  sucursal: string;
  uco: string;
  match_rut: string;
  match_nombre: string;
  mes: string;
  cobro: string;
  pago: string;
  fecha_pago: string;
  status: string;
};

type EdifitoResponse = {
  rows: EdifitoRow[];
  summary: {
    total: number;
    matched: number;
    not_matched: number;
    procesar_pago: number;
    analizar: number;
    ya_procesado: number;
  };
  download_filename: string;
  download_base64: string;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const tools = [
  {
    title: "Edifito",
    icon: "table",
    status: "Preparado",
    copy: "Cruzar cartolas Santander con asignaciones y cobros por UCO para preparar movimientos conciliables.",
  },
  {
    title: "Procesar audio",
    icon: "mic",
    status: "Preparado",
    copy: "Transcribir audios de terreno y convertirlos en borradores de incidencia, tarea, informe o comunicado.",
  },
  {
    title: "Importar planillas",
    icon: "table",
    status: "Preparado",
    copy: "Cargar planillas de novedades, unidades, mantenciones o pendientes para normalizarlas antes de trabajarlas.",
  },
  {
    title: "Resumen mensual",
    icon: "spark",
    status: "Preparado",
    copy: "Agrupar incidencias, tareas, mantenciones e inspecciones para preparar informes de gestion revisables.",
  },
];

const banks = ref<BankOption[]>([]);
const selectedBankKey = ref("name:Santander");
const bankStatementFile = ref<File | null>(null);
const assignmentsFile = ref<File | null>(null);
const chargeDetailFile = ref<File | null>(null);
const fileInputKey = ref(0);
const processing = ref(false);
const errorMessage = ref("");
const result = ref<EdifitoResponse | null>(null);
const selectedUcoFilter = ref("");
const selectedStatusFilter = ref("");

const selectedBank = computed(() => banks.value.find((bank) => bankKey(bank) === selectedBankKey.value) || null);
const canProcess = computed(() => Boolean(selectedBank.value && bankStatementFile.value && assignmentsFile.value && chargeDetailFile.value && !processing.value));
const isEdifito = computed(() => props.view === "edifito");
const ucoOptions = computed(() => {
  const values = new Set((result.value?.rows || []).map((row) => row.uco).filter(Boolean));
  return [...values].sort((a, b) => a.localeCompare(b));
});
const statusOptions = computed(() => {
  const values = new Set((result.value?.rows || []).map((row) => row.status || "Sin match"));
  return [...values].sort((a, b) => a.localeCompare(b));
});
const filteredRows = computed(() => {
  return (result.value?.rows || []).filter((row) => {
    const status = row.status || "Sin match";
    const matchesUco = !selectedUcoFilter.value || row.uco === selectedUcoFilter.value;
    const matchesStatus = !selectedStatusFilter.value || status === selectedStatusFilter.value;
    return matchesUco && matchesStatus;
  });
});

const bankKey = (bank: BankOption) => bank.id || `name:${bank.name}`;

const loadBanks = async () => {
  try {
    const data = await request<{ items?: BankOption[] }>("/api/v1/banks/?page=1&page_size=100&order_by=name");
    const activeBanks = (data.items || []).filter((bank) => bank.name && (!bank.status || bank.status === "active"));
    banks.value = activeBanks.length ? activeBanks : [{ name: "Santander", code: "santander" }];
  } catch {
    banks.value = [{ name: "Santander", code: "santander" }];
  }

  const santander = banks.value.find((bank) => `${bank.name} ${bank.code || ""}`.toLowerCase().includes("santander"));
  selectedBankKey.value = bankKey(santander || banks.value[0]);
};

const setFile = (event: Event, target: "bank" | "assignments" | "detail") => {
  const file = (event.target as HTMLInputElement).files?.[0] || null;
  if (target === "bank") bankStatementFile.value = file;
  if (target === "assignments") assignmentsFile.value = file;
  if (target === "detail") chargeDetailFile.value = file;
  result.value = null;
  errorMessage.value = "";
};

const resetEdifito = () => {
  const santander = banks.value.find((bank) => `${bank.name} ${bank.code || ""}`.toLowerCase().includes("santander"));
  selectedBankKey.value = bankKey(santander || banks.value[0]);
  bankStatementFile.value = null;
  assignmentsFile.value = null;
  chargeDetailFile.value = null;
  selectedUcoFilter.value = "";
  selectedStatusFilter.value = "";
  processing.value = false;
  errorMessage.value = "";
  result.value = null;
  fileInputKey.value += 1;
};

const processEdifito = async () => {
  if (!canProcess.value || !selectedBank.value) return;

  const form = new FormData();
  form.append("bank_statement", bankStatementFile.value as File);
  form.append("assignments_file", assignmentsFile.value as File);
  form.append("charge_detail_file", chargeDetailFile.value as File);
  if (selectedBank.value.id) form.append("bank_id", selectedBank.value.id);
  form.append("bank_name", selectedBank.value.name);

  processing.value = true;
  errorMessage.value = "";
  result.value = null;

  try {
    result.value = await request<EdifitoResponse>("/api/v1/edifito/process", {
      method: "POST",
      body: form,
    });
    selectedUcoFilter.value = "";
    selectedStatusFilter.value = "";
  } catch (error) {
    errorMessage.value = parseError(error);
  } finally {
    processing.value = false;
  }
};

const downloadResult = () => {
  if (!result.value) return;

  const binary = atob(result.value.download_base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  const blob = new Blob([bytes], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = result.value.download_filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

const parseError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo procesar Edifito.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

const actionIcon = (status: string) => {
  if (status === "Procesar Pago") return "play-circle";
  if (status === "Ya procesado") return "stop-circle";
  if (status === "Analizar") return "alert-circle";
  return "help-circle";
};

watch(isEdifito, (active) => {
  if (active && !banks.value.length) loadBanks();
}, { immediate: true });
</script>

<template>
  <section v-if="view !== 'edifito'" class="panel placeholder-panel">
    <p class="eyebrow">Herramientas</p>
    <h2>Centro de apoyo para la administradora</h2>
    <p class="placeholder-copy">
      Funciones pensadas para reducir trabajo repetitivo del equipo del cliente: procesar informacion, ordenar evidencias y preparar borradores antes de publicar o enviar.
    </p>

    <div class="tool-grid" style="margin-top: 18px">
      <article v-for="tool in tools" :key="tool.title" class="tool-card">
        <span class="tool-icon">
          <svg class="icon" aria-hidden="true"><use :href="`#icon-${tool.icon}`" /></svg>
        </span>
        <div>
          <h3>{{ tool.title }}</h3>
          <p class="card-copy">{{ tool.copy }}</p>
        </div>
        <span class="status-pill">{{ tool.status }}</span>
      </article>
    </div>
  </section>

  <section v-else class="panel edifito-panel">
    <div class="edifito-header">
      <div>
        <p class="eyebrow">Herramientas</p>
        <h2>Edifito</h2>
        <p class="placeholder-copy">Condominio activo: {{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="hero-actions">
        <button class="button ghost" type="button" @click="resetEdifito">
          <svg class="icon" aria-hidden="true"><use href="#icon-settings" /></svg>
          <span>Reset</span>
        </button>
        <button class="button orange" type="button" :disabled="!canProcess" @click="processEdifito">
          <svg class="icon" aria-hidden="true"><use href="#icon-checks" /></svg>
          <span>{{ processing ? "Procesando" : "Procesar" }}</span>
        </button>
      </div>
    </div>

    <div :key="fileInputKey" class="edifito-form">
      <label>
        Banco
        <select v-model="selectedBankKey">
          <option v-for="bank in banks" :key="bankKey(bank)" :value="bankKey(bank)">
            {{ bank.name }}
          </option>
        </select>
      </label>
      <label>
        Cartola banco
        <input type="file" accept=".pdf" @change="setFile($event, 'bank')" />
      </label>
      <label>
        Informe asignaciones
        <input type="file" accept=".xlsx" @change="setFile($event, 'assignments')" />
      </label>
      <label>
        Detalle cobros y pagos por UCO
        <input type="file" accept=".xlsx" @change="setFile($event, 'detail')" />
      </label>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div v-if="result" class="edifito-results">
      <div class="edifito-summary">
        <article><span>Total</span><strong>{{ result.summary.total }}</strong></article>
        <article><span>Match</span><strong>{{ result.summary.matched }}</strong></article>
        <article><span>Sin match</span><strong>{{ result.summary.not_matched }}</strong></article>
        <article><span>Procesar</span><strong>{{ result.summary.procesar_pago }}</strong></article>
        <article><span>Analizar</span><strong>{{ result.summary.analizar }}</strong></article>
        <article><span>Ya procesado</span><strong>{{ result.summary.ya_procesado }}</strong></article>
      </div>

      <div class="edifito-toolbar">
        <label>
          Filtrar por UCO
          <select v-model="selectedUcoFilter">
            <option value="">Todos</option>
            <option v-for="uco in ucoOptions" :key="uco" :value="uco">{{ uco }}</option>
          </select>
        </label>
        <label>
          Filtrar por Estado
          <select v-model="selectedStatusFilter">
            <option value="">Todos</option>
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
        </label>
        <button class="button ghost" type="button" @click="downloadResult">
          <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
          <span>Descargar Excel</span>
        </button>
      </div>

      <div class="edifito-table-wrap">
        <table class="edifito-table">
          <thead>
            <tr>
              <th class="bank-col">MONTO</th>
              <th class="bank-col">RUT</th>
              <th class="bank-col">NOMBRE</th>
              <th class="bank-col">FECHA</th>
              <th class="bank-col">DOCUMENTO</th>
              <th class="bank-col">SUCURSAL</th>
              <th class="analysis-col">UCO</th>
              <th class="analysis-col">MATCH RUT</th>
              <th class="analysis-col">MATCH NOMBRE</th>
              <th class="analysis-col">ESTADO</th>
              <th class="analysis-col">ACCION</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in filteredRows" :key="`${row.rut}-${row.fecha}-${index}`">
              <td>{{ row.monto }}</td>
              <td>{{ row.rut }}</td>
              <td>{{ row.nombre }}</td>
              <td>{{ row.fecha }}</td>
              <td>{{ row.documento }}</td>
              <td>{{ row.sucursal }}</td>
              <td>{{ row.uco }}</td>
              <td>{{ row.match_rut }}</td>
              <td>{{ row.match_nombre }}</td>
              <td>{{ row.status }}</td>
              <td class="center-cell">
                <svg class="status-action" :class="row.status ? row.status.toLowerCase().replaceAll(' ', '-') : 'not-match'" aria-hidden="true">
                  <use :href="`#icon-${actionIcon(row.status)}`" />
                </svg>
              </td>
            </tr>
            <tr v-if="!filteredRows.length">
              <td class="empty-row" colspan="11">Sin movimientos para los filtros seleccionados.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
