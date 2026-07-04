<script setup lang="ts">
type BankOption = {
  id?: string;
  name: string;
  code?: string | null;
  status?: string;
};

type ComunidadFelizRow = {
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

type ComunidadFelizResponse = {
  rows: ComunidadFelizRow[];
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
  ingresos_filename: string;
  ingresos_base64: string;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const banks = ref<BankOption[]>([]);
const selectedBankKey = ref("name:Banco de Chile");
const bankStatementFile = ref<File | null>(null);
const chargesFile = ref<File | null>(null);
const fileInputKey = ref(0);
const processing = ref(false);
const errorMessage = ref("");
const result = ref<ComunidadFelizResponse | null>(null);
const selectedUcoFilter = ref("");
const selectedStatusFilter = ref("");

const bankKey = (bank: BankOption) => bank.id || `name:${bank.name}`;
const selectedBank = computed(() => banks.value.find((bank) => bankKey(bank) === selectedBankKey.value) || null);
const canProcess = computed(() => Boolean(selectedBank.value && bankStatementFile.value && chargesFile.value && !processing.value));
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
const liveSummary = computed(() => {
  const rows = result.value?.rows || [];
  return {
    total: rows.length,
    matched: rows.filter((row) => row.uco).length,
    not_matched: rows.filter((row) => !row.uco).length,
    procesar_pago: rows.filter((row) => row.status === "Procesar Pago").length,
    analizar: rows.filter((row) => row.status === "Analizar").length,
    ya_procesado: rows.filter((row) => row.status === "Ya procesado").length,
  };
});

const loadBanks = async () => {
  try {
    const data = await request<{ items?: BankOption[] }>("/api/v1/banks/?page=1&page_size=100&order_by=name");
    const activeBanks = (data.items || []).filter((bank) => bank.name && (!bank.status || bank.status === "active"));
    banks.value = activeBanks.length ? activeBanks : [{ name: "Banco de Chile", code: "banco_chile" }];
  } catch {
    banks.value = [{ name: "Banco de Chile", code: "banco_chile" }];
  }

  const chile = banks.value.find((bank) => `${bank.name} ${bank.code || ""}`.toLowerCase().includes("chile"));
  selectedBankKey.value = bankKey(chile || banks.value[0]);
};

const setFile = (event: Event, target: "bank" | "charges") => {
  const file = (event.target as HTMLInputElement).files?.[0] || null;
  if (target === "bank") bankStatementFile.value = file;
  if (target === "charges") chargesFile.value = file;
  result.value = null;
  errorMessage.value = "";
};

const resetTool = () => {
  const chile = banks.value.find((bank) => `${bank.name} ${bank.code || ""}`.toLowerCase().includes("chile"));
  selectedBankKey.value = bankKey(chile || banks.value[0]);
  bankStatementFile.value = null;
  chargesFile.value = null;
  processing.value = false;
  errorMessage.value = "";
  result.value = null;
  selectedUcoFilter.value = "";
  selectedStatusFilter.value = "";
  fileInputKey.value += 1;
};

const processFiles = async () => {
  if (!canProcess.value || !selectedBank.value) return;

  const form = new FormData();
  form.append("bank_statement", bankStatementFile.value as File);
  form.append("charges_file", chargesFile.value as File);
  if (selectedBank.value.id) form.append("bank_id", selectedBank.value.id);
  form.append("bank_name", selectedBank.value.name);

  processing.value = true;
  errorMessage.value = "";
  result.value = null;
  selectedUcoFilter.value = "";
  selectedStatusFilter.value = "";

  try {
    result.value = await request<ComunidadFelizResponse>("/api/v1/comunidad-feliz/process", {
      method: "POST",
      body: form,
    });
  } catch (error) {
    errorMessage.value = parseError(error);
  } finally {
    processing.value = false;
  }
};

const toggleStatus = (row: ComunidadFelizRow) => {
  if (row.status === "Analizar") {
    row.status = "Procesar Pago";
  } else if (row.status === "Procesar Pago") {
    row.status = "Analizar";
  }
};

const downloadBase64 = (base64: string, filename: string) => {
  const binary = atob(base64);
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
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

const downloadMovements = () => {
  if (!result.value) return;
  downloadBase64(result.value.download_base64, result.value.download_filename);
};

const downloadIngresos = async () => {
  if (!result.value) return;
  try {
    const data = await request<{ ingresos_filename: string; ingresos_base64: string }>("/api/v1/comunidad-feliz/export-ingresos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows: result.value.rows }),
    });
    downloadBase64(data.ingresos_base64, data.ingresos_filename);
  } catch (error) {
    errorMessage.value = parseError(error);
  }
};

const parseError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo procesar Comunidad Feliz.";
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

onMounted(loadBanks);
</script>

<template>
  <section class="panel edifito-panel">
    <div class="edifito-header">
      <div>
        <p class="eyebrow">Herramientas</p>
        <h2>Comunidad Feliz</h2>
        <p class="placeholder-copy">Condominio activo: {{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="hero-actions">
        <button class="button ghost" type="button" @click="resetTool">
          <svg class="icon" aria-hidden="true"><use href="#icon-settings" /></svg>
          <span>Reset</span>
        </button>
        <button class="button orange" type="button" :disabled="!canProcess" @click="processFiles">
          <svg class="icon" aria-hidden="true"><use href="#icon-checks" /></svg>
          <span>{{ processing ? "Procesando" : "Procesar" }}</span>
        </button>
      </div>
    </div>

    <div :key="fileInputKey" class="comunidad-form">
      <label>
        Banco
        <select v-model="selectedBankKey">
          <option v-for="bank in banks" :key="bankKey(bank)" :value="bankKey(bank)">
            {{ bank.name }}
          </option>
        </select>
      </label>
      <label>
        Cartola Banco de Chile XLS/XLSX
        <input type="file" accept=".xls,.xlsx" @change="setFile($event, 'bank')" />
      </label>
      <label>
        Gasto Común Comunidad Feliz XLSX
        <input type="file" accept=".xlsx" @change="setFile($event, 'charges')" />
      </label>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div v-if="result" class="edifito-results">
      <div class="edifito-summary">
        <article><span>Total</span><strong>{{ liveSummary.total }}</strong></article>
        <article><span>Match</span><strong>{{ liveSummary.matched }}</strong></article>
        <article><span>Sin match</span><strong>{{ liveSummary.not_matched }}</strong></article>
        <article><span>Procesar</span><strong>{{ liveSummary.procesar_pago }}</strong></article>
        <article><span>Analizar</span><strong>{{ liveSummary.analizar }}</strong></article>
        <article><span>Ya procesado</span><strong>{{ liveSummary.ya_procesado }}</strong></article>
      </div>

      <div class="comunidad-toolbar">
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
        <button class="button ghost" type="button" @click="downloadMovements">
          <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
          <span>Descargar Excel</span>
        </button>
        <button class="button orange" type="button" @click="downloadIngresos">
          <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
          <span>Carga Automatica</span>
        </button>
      </div>

      <div class="edifito-table-wrap">
        <table class="edifito-table comunidad-table">
          <thead>
            <tr>
              <th class="bank-col">MONTO</th>
              <th class="bank-col">NOMBRE</th>
              <th class="bank-col">FECHA</th>
              <th class="bank-col">DOCUMENTO</th>
              <th class="bank-col">SUCURSAL</th>
              <th class="analysis-col">UCO</th>
              <th class="analysis-col">MATCH NOMBRE</th>
              <th class="analysis-col">COBRO</th>
              <th class="analysis-col">PAGO</th>
              <th class="analysis-col">ESTADO</th>
              <th class="analysis-col">ACCION</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in filteredRows" :key="`${row.nombre}-${row.fecha}-${index}`">
              <td>{{ row.monto }}</td>
              <td>{{ row.nombre }}</td>
              <td>{{ row.fecha }}</td>
              <td>{{ row.documento }}</td>
              <td>{{ row.sucursal }}</td>
              <td>{{ row.uco }}</td>
              <td>{{ row.match_nombre }}</td>
              <td>{{ row.cobro }}</td>
              <td>{{ row.pago }}</td>
              <td>{{ row.status }}</td>
              <td class="center-cell">
                <button class="icon-action-button" type="button" @click="toggleStatus(row)">
                  <svg class="status-action" :class="row.status ? row.status.toLowerCase().replaceAll(' ', '-') : 'not-match'" aria-hidden="true">
                    <use :href="`#icon-${actionIcon(row.status)}`" />
                  </svg>
                </button>
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
