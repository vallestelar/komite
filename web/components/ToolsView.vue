<script setup lang="ts">
const props = defineProps<{
  view: string;
}>();

const emit = defineEmits<{
  openView: [view: string];
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

type BulkPaymentMode = "both" | "process" | "analyze";

type EdifitoNeighborsImportResponse = {
  condominium_id: string;
  condominium_name: string;
  summary: {
    rows: number;
    units_created: number;
    units_updated: number;
    contacts_created: number;
    contacts_updated: number;
    contacts_skipped: number;
    users_created: number;
    users_updated: number;
    users_skipped: number;
  };
  items: Array<{
    unit: string;
    relationship_type: string;
    full_name: string;
    status: string;
  }>;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const tools = [
  {
    title: "Informe conciliación Edifito",
    icon: "table",
    targetView: "edifito",
    status: "Preparado",
    copy: "Cruzar cartolas Santander con asignaciones y cobros por UCO para preparar movimientos conciliables.",
  },
  {
    title: "Informe conciliación Comunidad Feliz",
    icon: "home",
    targetView: "comunidad-feliz",
    status: "Preparado",
    copy: "Cruzar cartolas Banco de Chile con boletas Comunidad Feliz y generar archivos de carga automatica.",
  },
  {
    title: "Procesar audio",
    icon: "mic",
    targetView: "audio",
    status: "Preparado",
    copy: "Transcribir audios de terreno y convertirlos en borradores de incidencia, tarea, informe o comunicado.",
  },
  {
    title: "Importar planillas",
    icon: "table",
    targetView: "spreadsheet-tools",
    status: "Preparado",
    copy: "Cargar planillas de novedades, unidades, mantenciones o pendientes para normalizarlas antes de trabajarlas.",
  },
  {
    title: "Resumen mensual",
    icon: "spark",
    targetView: "monthly-summary",
    status: "Preparado",
    copy: "Agrupar incidencias, tareas, mantenciones e inspecciones para preparar informes de gestion revisables.",
  },
];

const banks = ref<BankOption[]>([]);
const toolSearch = ref("");
const toolsPage = ref(1);
const toolsPageSize = 6;
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
const showBulkPaymentsModal = ref(false);
const bulkPaymentsTemplateFile = ref<File | null>(null);
const bulkPaymentsMode = ref<BulkPaymentMode>("both");
const bulkPaymentsError = ref("");
const bulkPaymentsNotice = ref("");
const bulkPaymentsGeneratedFiles = ref<string[]>([]);
const bulkPaymentsInputKey = ref(0);
const importCondominiumId = ref(activeCondominium.value?.id || "");
const importAssignmentsFile = ref<File | null>(null);
const importFileInputKey = ref(0);
const importProcessing = ref(false);
const importErrorMessage = ref("");
const importResult = ref<EdifitoNeighborsImportResponse | null>(null);
const importPreview = ref<EdifitoNeighborsImportResponse | null>(null);
const showImportConfirm = ref(false);

const selectedBank = computed(() => banks.value.find((bank) => bankKey(bank) === selectedBankKey.value) || null);
const canProcess = computed(() => Boolean(selectedBank.value && bankStatementFile.value && assignmentsFile.value && chargeDetailFile.value && !processing.value));
const isEdifito = computed(() => props.view === "edifito");
const isEdifitoImport = computed(() => props.view === "edifito-neighbors-import");
const isCatalog = computed(() => !isEdifito.value && !isEdifitoImport.value);
const canImportNeighbors = computed(() => Boolean(importCondominiumId.value && importAssignmentsFile.value && !importProcessing.value));
const importCondominiumOptions = computed(() => activeCondominium.value ? [activeCondominium.value] : []);
const filteredTools = computed(() => {
  const query = toolSearch.value.trim().toLowerCase();
  if (!query) return tools;

  return tools.filter((tool) => `${tool.title} ${tool.copy} ${tool.status}`.toLowerCase().includes(query));
});
const toolsPages = computed(() => Math.max(1, Math.ceil(filteredTools.value.length / toolsPageSize)));
const paginatedTools = computed(() => {
  const start = (toolsPage.value - 1) * toolsPageSize;
  return filteredTools.value.slice(start, start + toolsPageSize);
});
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

const goToolsPage = (page: number) => {
  toolsPage.value = Math.min(Math.max(page, 1), toolsPages.value);
};

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

const setImportAssignmentsFile = (event: Event) => {
  importAssignmentsFile.value = (event.target as HTMLInputElement).files?.[0] || null;
  importResult.value = null;
  importErrorMessage.value = "";
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
  showBulkPaymentsModal.value = false;
  bulkPaymentsTemplateFile.value = null;
  bulkPaymentsMode.value = "both";
  bulkPaymentsError.value = "";
  bulkPaymentsNotice.value = "";
  bulkPaymentsGeneratedFiles.value = [];
  bulkPaymentsInputKey.value += 1;
  fileInputKey.value += 1;
};

const resetImportNeighbors = () => {
  importCondominiumId.value = activeCondominium.value?.id || "";
  importAssignmentsFile.value = null;
  importProcessing.value = false;
  importErrorMessage.value = "";
  importResult.value = null;
  importPreview.value = null;
  showImportConfirm.value = false;
  importFileInputKey.value += 1;
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

const previewEdifitoNeighborsImport = async () => {
  if (!canImportNeighbors.value) return;

  const form = new FormData();
  form.append("condominium_id", importCondominiumId.value);
  form.append("assignments_file", importAssignmentsFile.value as File);

  importProcessing.value = true;
  importErrorMessage.value = "";
  importResult.value = null;
  importPreview.value = null;
  showImportConfirm.value = false;

  try {
    importPreview.value = await request<EdifitoNeighborsImportResponse>("/api/v1/edifito/import-neighbors/preview", {
      method: "POST",
      body: form,
    });
    showImportConfirm.value = true;
  } catch (error) {
    importErrorMessage.value = parseError(error);
  } finally {
    importProcessing.value = false;
  }
};

const importEdifitoNeighbors = async () => {
  if (!canImportNeighbors.value) return;

  const form = new FormData();
  form.append("condominium_id", importCondominiumId.value);
  form.append("assignments_file", importAssignmentsFile.value as File);

  importProcessing.value = true;
  importErrorMessage.value = "";
  importResult.value = null;

  try {
    importResult.value = await request<EdifitoNeighborsImportResponse>("/api/v1/edifito/import-neighbors", {
      method: "POST",
      body: form,
    });
    showImportConfirm.value = false;
    importPreview.value = null;
  } catch (error) {
    importErrorMessage.value = parseError(error);
  } finally {
    importProcessing.value = false;
  }
};

const cancelImportConfirmation = () => {
  showImportConfirm.value = false;
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
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
  downloadBlob(blob, result.value.download_filename);
};

const openBulkPaymentsModal = () => {
  bulkPaymentsTemplateFile.value = null;
  bulkPaymentsMode.value = "both";
  bulkPaymentsError.value = "";
  bulkPaymentsNotice.value = "";
  bulkPaymentsGeneratedFiles.value = [];
  bulkPaymentsInputKey.value += 1;
  showBulkPaymentsModal.value = true;
};

const closeBulkPaymentsModal = () => {
  showBulkPaymentsModal.value = false;
  bulkPaymentsNotice.value = "";
  bulkPaymentsGeneratedFiles.value = [];
};

const setBulkPaymentsTemplateFile = (event: Event) => {
  bulkPaymentsTemplateFile.value = (event.target as HTMLInputElement).files?.[0] || null;
  bulkPaymentsError.value = "";
  bulkPaymentsNotice.value = "";
  bulkPaymentsGeneratedFiles.value = [];
};

const readTextFile = (file: File) => new Promise<string>((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(String(reader.result || ""));
  reader.onerror = () => reject(new Error("No se pudo leer la plantilla CSV."));
  reader.readAsText(file, "utf-8");
});

const parseCsvLine = (line: string) => {
  const cells: string[] = [];
  let current = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === ";" && !quoted) {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }

  cells.push(current);
  return cells;
};

const stringifyCsvValue = (value: string) => {
  const text = value ?? "";
  if (!/[;"\r\n]/.test(text)) return text;
  return `"${text.replaceAll('"', '""')}"`;
};

const normalizeMatchValue = (value: string) => value
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-zA-Z0-9]/g, "")
  .toUpperCase();

const normalizePaymentDate = (value: string) => {
  const text = (value || "").trim();
  const match = text.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
  if (!match) return { display: text, transaction: text.replace(/\D/g, "") };

  const day = match[1].padStart(2, "0");
  const month = match[2].padStart(2, "0");
  const year = match[3];
  return {
    display: `${day}/${month}/${year}`,
    transaction: `${day}${month}${year}`,
  };
};

const allowedBulkStatuses = () => {
  if (bulkPaymentsMode.value === "process") return new Set(["Procesar Pago"]);
  if (bulkPaymentsMode.value === "analyze") return new Set(["Analizar"]);
  return new Set(["Procesar Pago", "Analizar"]);
};

const parseMoneyValue = (value: string) => {
  let clean = (value || "").replace(/[^\d,.-]/g, "").trim();
  if (!clean) return Number.NaN;

  if (clean.includes(",")) {
    clean = clean.replace(/\./g, "").replace(",", ".");
  } else if ((clean.match(/\./g) || []).length > 1 || /\.\d{3}$/.test(clean)) {
    clean = clean.replace(/\./g, "");
  }

  return Number(clean);
};

const isFullPaymentAmount = (paidValue: string, expectedValue: string) => {
  const paid = parseMoneyValue(paidValue);
  const expected = parseMoneyValue(expectedValue);
  return Number.isFinite(paid) && Number.isFinite(expected) && Math.abs(paid - expected) <= 0.5;
};

const bulkPaymentObservation = (row: EdifitoRow, paymentUcos: Set<string>) => {
  const status = (row.status || "").trim().toLowerCase();
  if (status !== "analizar") return "PAGO GG.CC";
  if (paymentUcos.has(normalizeMatchValue(row.uco))) {
    return "PAGO GG.CC";
  }
  if (isFullPaymentAmount(row.monto, row.cobro)) {
    return "PAGO GG.CC";
  }

  return "ABONO GG.CC";
};

const findBulkPaymentRows = (templateUnitName: string, candidatesByUco: Map<string, EdifitoRow[]>) => {
  const normalizedUnitName = normalizeMatchValue(templateUnitName);
  const matchingUco = [...candidatesByUco.keys()]
    .sort((first, second) => second.length - first.length)
    .find((uco) => normalizedUnitName.includes(uco));
  return matchingUco ? candidatesByUco.get(matchingUco) || [] : [];
};

const generateBulkPaymentsFile = async () => {
  if (!result.value || !bulkPaymentsTemplateFile.value) {
    bulkPaymentsError.value = "Selecciona la plantilla CSV de carga masiva.";
    return;
  }

  try {
    bulkPaymentsError.value = "";
    bulkPaymentsNotice.value = "";
    bulkPaymentsGeneratedFiles.value = [];

    const templateText = await readTextFile(bulkPaymentsTemplateFile.value);
    const lines = templateText.replace(/^\uFEFF/, "").split(/\r\n|\n|\r/).filter((line) => line.length);
    if (!lines.length) throw new Error("La plantilla CSV esta vacia.");

    const header = parseCsvLine(lines[0]);
    const headerMap = new Map(header.map((cell, index) => [normalizeMatchValue(cell), index]));
    const unitNameIndex = headerMap.get(normalizeMatchValue("nombre de unidad"));
    const paymentDateIndex = headerMap.get(normalizeMatchValue("fecha pago(dd-mm-yyyy o dd/mm/yyyy)"));
    const amountIndex = headerMap.get(normalizeMatchValue("monto"));
    const bankIndex = headerMap.get(normalizeMatchValue("banco"));
    const transactionIndex = headerMap.get(normalizeMatchValue("no. transaccion"));
    const notesIndex = headerMap.get(normalizeMatchValue("observaciones"));

    if (
      unitNameIndex === undefined
      || paymentDateIndex === undefined
      || amountIndex === undefined
      || transactionIndex === undefined
      || notesIndex === undefined
    ) {
      throw new Error("La plantilla no tiene las columnas esperadas de carga masiva.");
    }

    const statuses = allowedBulkStatuses();
    const candidates = result.value.rows.filter((row) => row.uco && statuses.has(row.status));
    const paymentUcos = new Set(
      result.value.rows
        .filter((row) => row.uco && (row.status || "").trim().toLowerCase() === "procesar pago")
        .map((row) => normalizeMatchValue(row.uco)),
    );
    if (!candidates.length) {
      throw new Error("No hay movimientos para generar la carga masiva con el alcance seleccionado.");
    }

    const candidatesByUco = new Map<string, EdifitoRow[]>();
    for (const candidate of candidates) {
      const key = normalizeMatchValue(candidate.uco);
      if (!key) continue;
      const rows = candidatesByUco.get(key) || [];
      rows.push(candidate);
      candidatesByUco.set(key, rows);
    }

    const maxFiles = Math.max(...[...candidatesByUco.values()].map((rows) => rows.length));
    const bodyLines = lines.slice(1);
    const generatedFiles: Array<{ filename: string; csv: string }> = [];
    const today = new Date();
    const suffix = `${String(today.getDate()).padStart(2, "0")}_${String(today.getMonth() + 1).padStart(2, "0")}_${today.getFullYear()}`;

    for (let fileIndex = 0; fileIndex < maxFiles; fileIndex += 1) {
      const outputRows = [header];
      let filledRows = 0;

      for (const line of bodyLines) {
        const templateRow = parseCsvLine(line).slice(0, header.length);
        while (templateRow.length < header.length) templateRow.push("");

        const paymentRows = findBulkPaymentRows(templateRow[unitNameIndex] || "", candidatesByUco);
        const paymentRow = paymentRows[fileIndex];
        if (paymentRow) {
          const date = normalizePaymentDate(paymentRow.fecha);
          templateRow[paymentDateIndex] = date.display;
          templateRow[amountIndex] = paymentRow.monto;
          if (bankIndex !== undefined) templateRow[bankIndex] = "";
          templateRow[transactionIndex] = date.transaction;
          templateRow[notesIndex] = bulkPaymentObservation(paymentRow, paymentUcos);
          filledRows += 1;
        }

        outputRows.push(templateRow);
      }

      if (filledRows > 0) {
        const csv = outputRows.map((row) => row.map(stringifyCsvValue).join(";")).join("\r\n");
        const fileNumber = maxFiles > 1 ? `_${String(fileIndex + 1).padStart(2, "0")}` : "";
        generatedFiles.push({
          filename: `pagos_masivos_edifito_${suffix}${fileNumber}.csv`,
          csv,
        });
      }
    }

    if (!generatedFiles.length) {
      throw new Error("No se encontro ningun match entre la plantilla CSV y los movimientos seleccionados.");
    }

    generatedFiles.forEach((file) => {
      const blob = new Blob([`\uFEFF${file.csv}`], { type: "text/csv;charset=utf-8" });
      downloadBlob(blob, file.filename);
    });

    if (generatedFiles.length > 1) {
      bulkPaymentsNotice.value = `Se han generado ${generatedFiles.length} ficheros de carga porque hay mas de un pago para una misma UCO.`;
    } else {
      bulkPaymentsNotice.value = "Se ha generado 1 fichero de carga masiva.";
    }

    bulkPaymentsGeneratedFiles.value = generatedFiles.map((file) => file.filename);
  } catch (error) {
    bulkPaymentsError.value = error instanceof Error ? error.message : "No se pudo generar el CSV de carga masiva.";
  }
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

const tableStatusLabel = (status: string | null | undefined) => {
  if (status === "active") return "Activo";
  if (status === "inactive") return "Inactivo";
  if (status === "created") return "Creado";
  if (status === "updated") return "Actualizado";
  if (status === "skipped") return "Omitido";
  return status || "Sin estado";
};

const tableStatusBadgeClass = (status: string | null | undefined) => {
  if (status === "active" || status === "created" || status === "updated") return "is-active";
  if (status === "inactive") return "is-inactive";
  return "is-neutral";
};

watch(isEdifito, (active) => {
  if (active && !banks.value.length) loadBanks();
}, { immediate: true });

watch(isEdifitoImport, (active) => {
  if (active && !importCondominiumId.value) resetImportNeighbors();
}, { immediate: true });

watch(activeCondominium, (condominium) => {
  importCondominiumId.value = condominium?.id || "";
});

watch(toolSearch, () => {
  toolsPage.value = 1;
});

watch(toolsPages, (pages) => {
  if (toolsPage.value > pages) toolsPage.value = pages;
});
</script>

<template>
  <section v-if="isCatalog" class="panel placeholder-panel">
    <p class="eyebrow">Herramientas</p>
    <h2>Centro de apoyo para la administradora</h2>
    <p class="placeholder-copy">
      Funciones pensadas para reducir trabajo repetitivo del equipo del cliente: procesar informacion, ordenar evidencias y preparar borradores antes de publicar o enviar.
    </p>

    <div class="tools-catalog-toolbar">
      <label class="tools-search">
        Buscar herramienta
        <input v-model="toolSearch" type="search" placeholder="Buscar por nombre o funcion" />
      </label>
      <span class="tools-count">{{ filteredTools.length }} herramientas</span>
    </div>

    <div v-if="paginatedTools.length" class="tool-grid">
      <button v-for="tool in paginatedTools" :key="tool.title" class="tool-card tool-card-link" type="button" @click="emit('openView', tool.targetView)">
        <span class="tool-icon">
          <svg class="icon" aria-hidden="true"><use :href="`#icon-${tool.icon}`" /></svg>
        </span>
        <div>
          <h3>{{ tool.title }}</h3>
          <p class="card-copy">{{ tool.copy }}</p>
        </div>
        <span class="tool-card-footer">
          <span class="status-pill">{{ tool.status }}</span>
          <span class="tool-link-label">
            <span>Abrir</span>
            <svg class="icon" aria-hidden="true"><use href="#icon-chevron-down" /></svg>
          </span>
        </span>
      </button>
    </div>
    <p v-else class="tools-empty">No hay herramientas que coincidan con la busqueda.</p>

    <div v-if="filteredTools.length" class="tools-pagination">
      <button class="button ghost icon-only" type="button" title="Pagina anterior" :disabled="toolsPage === 1" @click="goToolsPage(toolsPage - 1)">
        <svg class="icon prev-icon" aria-hidden="true"><use href="#icon-chevron-down" /></svg>
      </button>
      <span class="tools-page-label">Pagina {{ toolsPage }} de {{ toolsPages }}</span>
      <button class="button ghost icon-only" type="button" title="Pagina siguiente" :disabled="toolsPage === toolsPages" @click="goToolsPage(toolsPage + 1)">
        <svg class="icon next-icon" aria-hidden="true"><use href="#icon-chevron-down" /></svg>
      </button>
    </div>
  </section>

  <section v-else-if="isEdifito" class="panel edifito-panel">
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
        Cartola banco Santander PDF
        <input type="file" accept=".pdf" @change="setFile($event, 'bank')" />
      </label>
      <label>
        Informe asignaciones Edifito XLSX
        <input type="file" accept=".xlsx" @change="setFile($event, 'assignments')" />
      </label>
      <label>
        Informe en detalle cobros y pagos por UCO XLSX
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
          <span>Descargar Analisis</span>
        </button>
        <button class="button ghost" type="button" @click="openBulkPaymentsModal">
          <svg class="icon" aria-hidden="true"><use href="#icon-table" /></svg>
          <span>Descargar ficheros para carga masiva</span>
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

    <div v-if="showBulkPaymentsModal" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="bulk-payments-title">
      <div class="confirm-modal import-confirm-modal bulk-payments-modal">
        <p class="eyebrow">Carga masiva</p>
        <h3 id="bulk-payments-title">Descargar ficheros para carga masiva</h3>
        <p class="placeholder-copy">
          Sube la plantilla CSV del condominio. El sistema completara las unidades encontradas en la conciliacion segun el alcance seleccionado.
        </p>

        <div :key="bulkPaymentsInputKey" class="bulk-payments-form">
          <label>
            Plantilla CSV de carga masiva
            <input type="file" accept=".csv,text/csv" @change="setBulkPaymentsTemplateFile" />
          </label>
          <label>
            Movimientos a incluir
            <select v-model="bulkPaymentsMode">
              <option value="both">Procesar Pago y Analizar</option>
              <option value="process">Solo Procesar Pago</option>
              <option value="analyze">Solo Analizar</option>
            </select>
          </label>
        </div>

        <p v-if="bulkPaymentsError" class="form-error result-message">{{ bulkPaymentsError }}</p>

        <div v-if="bulkPaymentsNotice" class="bulk-payments-notice">
          <div>
            <strong>{{ bulkPaymentsNotice }}</strong>
            <p>Archivos descargados:</p>
          </div>
          <ul>
            <li v-for="filename in bulkPaymentsGeneratedFiles" :key="filename">{{ filename }}</li>
          </ul>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" @click="closeBulkPaymentsModal">
            {{ bulkPaymentsNotice ? "Cerrar" : "Cancelar" }}
          </button>
          <button class="button orange" type="button" @click="generateBulkPaymentsFile">
            <svg class="icon" aria-hidden="true"><use href="#icon-table" /></svg>
            <span>Generar CSV</span>
          </button>
        </div>
      </div>
    </div>
  </section>

  <section v-else class="panel edifito-panel">
    <div class="edifito-header">
      <div>
        <p class="eyebrow">Herramientas</p>
        <h2>Carga vecinos Edifito</h2>
        <p class="placeholder-copy">Importa unidades, copropietarios y residentes desde el informe de asignaciones.</p>
      </div>
      <div class="hero-actions">
        <button class="button ghost" type="button" @click="resetImportNeighbors">
          <svg class="icon" aria-hidden="true"><use href="#icon-settings" /></svg>
          <span>Reset</span>
        </button>
        <button class="button orange" type="button" :disabled="!canImportNeighbors" @click="previewEdifitoNeighborsImport">
          <svg class="icon" aria-hidden="true"><use href="#icon-checks" /></svg>
          <span>{{ importProcessing ? "Analizando" : "Revisar carga" }}</span>
        </button>
      </div>
    </div>

    <div :key="importFileInputKey" class="edifito-form">
      <label>
        Comunidad
        <select v-model="importCondominiumId" disabled>
          <option v-if="!activeCondominium" value="">Selecciona comunidad arriba</option>
          <option v-for="condominium in importCondominiumOptions" :key="condominium.id" :value="condominium.id">
            {{ condominium.name }}
          </option>
        </select>
      </label>
      <label>
        Informe asignaciones Edifito XLSX
        <input type="file" accept=".xlsx" @change="setImportAssignmentsFile" />
      </label>
    </div>

    <p v-if="importErrorMessage" class="form-error result-message">{{ importErrorMessage }}</p>

    <div v-if="importResult" class="edifito-results">
      <div class="edifito-summary">
        <article><span>Filas</span><strong>{{ importResult.summary.rows }}</strong></article>
        <article><span>Unidades nuevas</span><strong>{{ importResult.summary.units_created }}</strong></article>
        <article><span>Unidades actualizadas</span><strong>{{ importResult.summary.units_updated }}</strong></article>
        <article><span>Contactos nuevos</span><strong>{{ importResult.summary.contacts_created }}</strong></article>
        <article><span>Contactos actualizados</span><strong>{{ importResult.summary.contacts_updated }}</strong></article>
        <article><span>Usuarios nuevos</span><strong>{{ importResult.summary.users_created }}</strong></article>
        <article><span>Usuarios actualizados</span><strong>{{ importResult.summary.users_updated }}</strong></article>
        <article><span>Omitidos</span><strong>{{ importResult.summary.contacts_skipped }}</strong></article>
      </div>

      <p class="success-message">Carga aplicada en {{ importResult.condominium_name }}.</p>

      <div class="edifito-table-wrap">
        <table class="edifito-table">
          <thead>
            <tr>
              <th>Unidad</th>
              <th>Relación</th>
              <th>Nombre</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in importResult.items" :key="`${item.unit}-${item.relationship_type}-${item.full_name}-${index}`">
              <td>{{ item.unit }}</td>
              <td>{{ item.relationship_type }}</td>
              <td>{{ item.full_name }}</td>
              <td>
                <span class="status-badge" :class="tableStatusBadgeClass(item.status)">
                  <span aria-hidden="true"></span>
                  {{ tableStatusLabel(item.status) }}
                </span>
              </td>
            </tr>
            <tr v-if="!importResult.items.length">
              <td class="empty-row" colspan="4">No hay detalle para mostrar.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showImportConfirm && importPreview" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="import-preview-title">
      <div class="confirm-modal import-confirm-modal">
        <p class="eyebrow">Confirmar carga</p>
        <h3 id="import-preview-title">Carga vecinos Edifito</h3>
        <p class="placeholder-copy">
          Se va a aplicar el informe en {{ importPreview.condominium_name }}. Revisa el resumen antes de continuar.
        </p>

        <div class="edifito-summary import-preview-summary">
          <article><span>Filas</span><strong>{{ importPreview.summary.rows }}</strong></article>
          <article><span>Unidades nuevas</span><strong>{{ importPreview.summary.units_created }}</strong></article>
          <article><span>Unidades actualizadas</span><strong>{{ importPreview.summary.units_updated }}</strong></article>
          <article><span>Contactos nuevos</span><strong>{{ importPreview.summary.contacts_created }}</strong></article>
          <article><span>Contactos actualizados</span><strong>{{ importPreview.summary.contacts_updated }}</strong></article>
          <article><span>Usuarios nuevos</span><strong>{{ importPreview.summary.users_created }}</strong></article>
          <article><span>Usuarios actualizados</span><strong>{{ importPreview.summary.users_updated }}</strong></article>
          <article><span>Omitidos</span><strong>{{ importPreview.summary.contacts_skipped + importPreview.summary.users_skipped }}</strong></article>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="importProcessing" @click="cancelImportConfirmation">
            Cancelar
          </button>
          <button class="button orange" type="button" :disabled="importProcessing" @click="importEdifitoNeighbors">
            <svg class="icon" aria-hidden="true"><use href="#icon-checks" /></svg>
            <span>{{ importProcessing ? "Procesando" : "Aceptar y cargar" }}</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
