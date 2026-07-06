<script setup lang="ts">
type PageMeta = {
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

type UnitRecord = {
  id: string;
  condominium_id: string;
  identifier: string;
  floor?: string | null;
  unit_type: string;
  external_code?: string | null;
  allocation_number?: number | null;
  allocation_identifier?: string | null;
  proration_total?: number | string | null;
  proration?: number | string | null;
  assignment_date?: string | null;
  metadata?: Record<string, unknown>;
};

type NeighborRecord = {
  id: string;
  user_id?: string | null;
  email?: string | null;
  full_name: string;
  phone?: string | null;
  unit_id: string;
  unit_identifier: string;
  relationship_type: string;
  document_type?: string | null;
  document_number?: string | null;
  address?: string | null;
  is_primary_contact: boolean;
  status: string;
  receives_notifications: boolean;
  start_date?: string | null;
  end_date?: string | null;
  metadata?: Record<string, unknown>;
};

type UnitForm = {
  id: string;
  identifier: string;
  floor: string;
  unit_type: string;
  external_code: string;
  allocation_number: string;
  allocation_identifier: string;
  proration_total: string;
  proration: string;
  assignment_date: string;
  metadata: string;
};

type NeighborForm = {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  unit_id: string;
  relationship_type: string;
  document_type: string;
  document_number: string;
  address: string;
  is_primary_contact: boolean;
  status: string;
  receives_notifications: boolean;
  start_date: string;
  end_date: string;
  metadata: string;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const activeTab = ref<"neighbors" | "units">("neighbors");
const units = ref<UnitRecord[]>([]);
const neighbors = ref<NeighborRecord[]>([]);
const unitsMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const neighborsMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const unitsSearch = ref("");
const neighborsSearch = ref("");
const loading = ref(false);
const errorMessage = ref("");
const formError = ref("");
const toastMessage = ref("");
const searchTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const mode = ref<"list" | "neighborForm" | "unitForm">("list");
const deleteCandidate = ref<{ type: "neighbor" | "unit"; id: string; label: string } | null>(null);

const unitForm = reactive<UnitForm>({
  id: "",
  identifier: "",
  floor: "",
  unit_type: "apartment",
  external_code: "",
  allocation_number: "",
  allocation_identifier: "",
  proration_total: "",
  proration: "",
  assignment_date: "",
  metadata: "{}",
});

const neighborForm = reactive<NeighborForm>({
  id: "",
  email: "",
  full_name: "",
  phone: "",
  unit_id: "",
  relationship_type: "residente",
  document_type: "rut",
  document_number: "",
  address: "",
  is_primary_contact: false,
  status: "active",
  receives_notifications: true,
  start_date: "",
  end_date: "",
  metadata: "{}",
});

const pageSizeOptions = [10, 25, 50];
const relationshipOptions = [
  ["copropietario", "Copropietario"],
  ["residente", "Residente"],
  ["arrendatario", "Arrendatario"],
  ["contacto", "Contacto"],
  ["otro", "Otro"],
];
const documentTypeOptions = [
  ["rut", "RUT"],
  ["dni", "DNI"],
  ["passport", "Pasaporte"],
  ["foreign_id", "Documento extranjero"],
  ["other", "Otro"],
];
const statusOptions = [
  ["active", "Activo"],
  ["inactive", "Inactivo"],
];
const unitTypeOptions = [
  ["apartment", "Departamento"],
  ["house", "Casa"],
  ["office", "Oficina"],
  ["parking", "Estacionamiento"],
  ["storage", "Bodega"],
  ["other", "Otro"],
];

const currentMeta = computed(() => activeTab.value === "neighbors" ? neighborsMeta : unitsMeta);
const pageLabel = computed(() => `Pagina ${currentMeta.value.page} de ${currentMeta.value.pages || 1}`);
const rangeLabel = computed(() => {
  const meta = currentMeta.value;
  if (!meta.total) return "Sin registros";
  const start = (meta.page - 1) * meta.page_size + 1;
  const end = Math.min(meta.total, meta.page * meta.page_size);
  return `${start}-${end} de ${meta.total}`;
});
const title = computed(() => {
  if (mode.value === "neighborForm") return neighborForm.id ? "Editar vecino" : "Nuevo vecino";
  if (mode.value === "unitForm") return unitForm.id ? "Editar unidad" : "Nueva unidad";
  return "Vecinos y unidades";
});

const statusLabel = (status: string | null | undefined) => {
  if (status === "active") return "Activo";
  if (status === "inactive") return "Inactivo";
  return status || "Sin estado";
};

const statusBadgeClass = (status: string | null | undefined) => {
  if (status === "active") return "is-active";
  if (status === "inactive") return "is-inactive";
  return "is-neutral";
};

const loadUnits = async () => {
  const params = new URLSearchParams({
    page: String(unitsMeta.page),
    page_size: String(unitsMeta.page_size),
  });
  if (unitsSearch.value.trim()) params.set("q", unitsSearch.value.trim());
  const data = await request<{ items?: UnitRecord[]; meta?: PageMeta }>(`/api/v1/units/?${params}`);
  units.value = data.items || [];
  Object.assign(unitsMeta, data.meta || { total: units.value.length, page: unitsMeta.page, page_size: unitsMeta.page_size, pages: 1 });
};

const loadNeighbors = async () => {
  const params = new URLSearchParams({
    page: String(neighborsMeta.page),
    page_size: String(neighborsMeta.page_size),
  });
  if (neighborsSearch.value.trim()) params.set("q", neighborsSearch.value.trim());
  const data = await request<{ items?: NeighborRecord[]; meta?: PageMeta }>(`/api/v1/portal/neighbors/?${params}`);
  neighbors.value = data.items || [];
  Object.assign(neighborsMeta, data.meta || { total: neighbors.value.length, page: neighborsMeta.page, page_size: neighborsMeta.page_size, pages: 1 });
};

const loadActiveTab = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    if (activeTab.value === "neighbors") {
      await Promise.all([loadNeighbors(), loadUnits()]);
    } else {
      await loadUnits();
    }
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const selectTab = async (tab: "neighbors" | "units") => {
  activeTab.value = tab;
  mode.value = "list";
  await loadActiveTab();
};

const goPage = async (page: number) => {
  const meta = currentMeta.value;
  meta.page = Math.min(Math.max(page, 1), meta.pages || 1);
  await loadActiveTab();
};

const changePageSize = async () => {
  currentMeta.value.page = 1;
  await loadActiveTab();
};

const scheduleSearch = () => {
  if (searchTimer.value) clearTimeout(searchTimer.value);
  searchTimer.value = setTimeout(async () => {
    currentMeta.value.page = 1;
    await loadActiveTab();
  }, 350);
};

const openCreateNeighbor = async () => {
  resetNeighborForm();
  await loadUnits();
  mode.value = "neighborForm";
};

const openEditNeighbor = async (neighbor: NeighborRecord) => {
  await loadUnits();
  neighborForm.id = neighbor.id;
  neighborForm.email = neighbor.email || "";
  neighborForm.full_name = neighbor.full_name;
  neighborForm.phone = neighbor.phone || "";
  neighborForm.unit_id = neighbor.unit_id;
  neighborForm.relationship_type = neighbor.relationship_type || "residente";
  neighborForm.document_type = neighbor.document_type || "rut";
  neighborForm.document_number = neighbor.document_number || "";
  neighborForm.address = neighbor.address || "";
  neighborForm.is_primary_contact = neighbor.is_primary_contact;
  neighborForm.status = neighbor.status || "active";
  neighborForm.receives_notifications = neighbor.receives_notifications;
  neighborForm.start_date = neighbor.start_date || "";
  neighborForm.end_date = neighbor.end_date || "";
  neighborForm.metadata = JSON.stringify(neighbor.metadata || {}, null, 2);
  formError.value = "";
  mode.value = "neighborForm";
};

const openCreateUnit = () => {
  resetUnitForm();
  mode.value = "unitForm";
};

const openEditUnit = (unit: UnitRecord) => {
  unitForm.id = unit.id;
  unitForm.identifier = unit.identifier || "";
  unitForm.floor = unit.floor || "";
  unitForm.unit_type = unit.unit_type || "apartment";
  unitForm.external_code = unit.external_code || "";
  unitForm.allocation_number = unit.allocation_number ? String(unit.allocation_number) : "";
  unitForm.allocation_identifier = unit.allocation_identifier || "";
  unitForm.proration_total = unit.proration_total != null ? String(unit.proration_total) : "";
  unitForm.proration = unit.proration != null ? String(unit.proration) : "";
  unitForm.assignment_date = unit.assignment_date || "";
  unitForm.metadata = JSON.stringify(unit.metadata || {}, null, 2);
  formError.value = "";
  mode.value = "unitForm";
};

const returnToList = async () => {
  mode.value = "list";
  resetNeighborForm();
  resetUnitForm();
  await loadActiveTab();
};

const saveNeighbor = async () => {
  formError.value = "";
  let parsedMetadata: Record<string, unknown>;
  try {
    parsedMetadata = neighborForm.metadata.trim() ? JSON.parse(neighborForm.metadata) : {};
  } catch {
    formError.value = "Metadata debe ser un JSON valido.";
    return;
  }

  const payload = {
    email: emptyToNull(neighborForm.email),
    full_name: neighborForm.full_name.trim(),
    phone: emptyToNull(neighborForm.phone),
    unit_id: emptyToNull(neighborForm.unit_id),
    relationship_type: neighborForm.relationship_type,
    document_type: emptyToNull(neighborForm.document_type),
    document_number: emptyToNull(neighborForm.document_number),
    address: emptyToNull(neighborForm.address),
    is_primary_contact: neighborForm.is_primary_contact,
    status: neighborForm.status,
    receives_notifications: neighborForm.receives_notifications,
    start_date: emptyToNull(neighborForm.start_date),
    end_date: emptyToNull(neighborForm.end_date),
    metadata: parsedMetadata,
  };
  if (!payload.full_name || !payload.unit_id) {
    formError.value = "Nombre y unidad son obligatorios.";
    return;
  }

  try {
    await request<NeighborRecord>(neighborForm.id ? `/api/v1/portal/neighbors/${neighborForm.id}` : "/api/v1/portal/neighbors/", {
      method: neighborForm.id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(neighborForm.id ? "Vecino actualizado correctamente." : "Vecino creado correctamente.");
    activeTab.value = "neighbors";
    await returnToList();
  } catch (error) {
    formError.value = readableError(error);
  }
};

const saveUnit = async () => {
  formError.value = "";
  if (!activeCondominium.value?.id) {
    formError.value = "Selecciona un condominio activo antes de guardar.";
    return;
  }

  let parsedMetadata: Record<string, unknown>;
  try {
    parsedMetadata = unitForm.metadata.trim() ? JSON.parse(unitForm.metadata) : {};
  } catch {
    formError.value = "Metadata debe ser un JSON valido.";
    return;
  }

  const payload = {
    condominium_id: activeCondominium.value.id,
    identifier: unitForm.identifier.trim(),
    floor: emptyToNull(unitForm.floor),
    unit_type: unitForm.unit_type,
    external_code: emptyToNull(unitForm.external_code),
    allocation_number: emptyToNumber(unitForm.allocation_number),
    allocation_identifier: emptyToNull(unitForm.allocation_identifier),
    proration_total: emptyToNumber(unitForm.proration_total),
    proration: emptyToNumber(unitForm.proration),
    assignment_date: emptyToNull(unitForm.assignment_date),
    metadata: parsedMetadata,
  };
  if (!payload.identifier) {
    formError.value = "La unidad es obligatoria.";
    return;
  }

  try {
    await request<UnitRecord>(unitForm.id ? `/api/v1/units/${unitForm.id}` : "/api/v1/units/", {
      method: unitForm.id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(unitForm.id ? "Unidad actualizada correctamente." : "Unidad creada correctamente.");
    activeTab.value = "units";
    await returnToList();
  } catch (error) {
    formError.value = readableError(error);
  }
};

const askDeleteNeighbor = (neighbor: NeighborRecord) => {
  deleteCandidate.value = { type: "neighbor", id: neighbor.id, label: neighbor.full_name };
};

const askDeleteUnit = (unit: UnitRecord) => {
  deleteCandidate.value = { type: "unit", id: unit.id, label: unit.identifier };
};

const cancelDelete = () => {
  deleteCandidate.value = null;
};

const confirmDelete = async () => {
  if (!deleteCandidate.value) return;
  try {
    if (deleteCandidate.value.type === "neighbor") {
      await request(`/api/v1/portal/neighbors/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Vecino eliminado correctamente.");
      activeTab.value = "neighbors";
    } else {
      await request(`/api/v1/units/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Unidad eliminada correctamente.");
      activeTab.value = "units";
    }
    deleteCandidate.value = null;
    await loadActiveTab();
  } catch (error) {
    errorMessage.value = readableError(error);
    deleteCandidate.value = null;
  }
};

const resetNeighborForm = () => {
  neighborForm.id = "";
  neighborForm.email = "";
  neighborForm.full_name = "";
  neighborForm.phone = "";
  neighborForm.unit_id = "";
  neighborForm.relationship_type = "residente";
  neighborForm.document_type = "rut";
  neighborForm.document_number = "";
  neighborForm.address = "";
  neighborForm.is_primary_contact = false;
  neighborForm.status = "active";
  neighborForm.receives_notifications = true;
  neighborForm.start_date = "";
  neighborForm.end_date = "";
  neighborForm.metadata = "{}";
  formError.value = "";
};

const resetUnitForm = () => {
  unitForm.id = "";
  unitForm.identifier = "";
  unitForm.floor = "";
  unitForm.unit_type = "apartment";
  unitForm.external_code = "";
  unitForm.allocation_number = "";
  unitForm.allocation_identifier = "";
  unitForm.proration_total = "";
  unitForm.proration = "";
  unitForm.assignment_date = "";
  unitForm.metadata = "{}";
  formError.value = "";
};

const showToast = (message: string) => {
  toastMessage.value = message;
  setTimeout(() => {
    if (toastMessage.value === message) toastMessage.value = "";
  }, 3000);
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

const emptyToNull = (value: string) => {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
};

const emptyToNumber = (value: string) => {
  const trimmed = value.trim().replace(",", ".");
  return trimmed ? Number(trimmed) : null;
};

const relationshipLabel = (value: string) => relationshipOptions.find(([key]) => key === value)?.[1] || value;
const unitTypeLabel = (value: string) => unitTypeOptions.find(([key]) => key === value)?.[1] || value;

onMounted(loadActiveTab);
</script>

<template>
  <section class="panel entity-panel">
    <div class="entity-header">
      <div>
        <p class="eyebrow">Vecinos y unidades</p>
        <h2>{{ title }}</h2>
        <p class="placeholder-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <button v-if="mode !== 'list'" class="button ghost" type="button" @click="returnToList">
        <svg class="icon" aria-hidden="true"><use href="#icon-arrow-left" /></svg>
        <span>Volver al listado</span>
      </button>
    </div>

    <div v-if="mode === 'list'" class="entity-list">
      <div class="entity-tabs" role="tablist" aria-label="Vecinos y unidades">
        <button class="button compact" :class="activeTab === 'neighbors' ? 'navy' : 'ghost'" type="button" @click="selectTab('neighbors')">Vecinos</button>
        <button class="button compact" :class="activeTab === 'units' ? 'navy' : 'ghost'" type="button" @click="selectTab('units')">Unidades</button>
      </div>

      <div class="entity-toolbar">
        <input
          v-if="activeTab === 'neighbors'"
          v-model="neighborsSearch"
          type="search"
          placeholder="Buscar vecino, email, documento o unidad"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <input
          v-else
          v-model="unitsSearch"
          type="search"
          placeholder="Buscar unidad"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <button v-if="activeTab === 'neighbors'" class="button orange" type="button" @click="openCreateNeighbor">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo vecino</span>
        </button>
        <button v-else class="button orange" type="button" @click="openCreateUnit">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nueva unidad</span>
        </button>
        <button class="button ghost" type="button" :disabled="loading" @click="loadActiveTab">
          <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
          <span>Actualizar</span>
        </button>
      </div>

      <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
      <p v-if="toastMessage" class="success-message">{{ toastMessage }}</p>

      <div class="edifito-table-wrap entity-table-wrap">
        <table v-if="activeTab === 'neighbors'" class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Relacion</th>
              <th>Unidad</th>
              <th>Documento</th>
              <th>Email</th>
              <th>Telefono</th>
              <th>Principal</th>
              <th>Notifica</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="neighbor in neighbors" :key="neighbor.id">
              <td><strong>{{ neighbor.full_name }}</strong></td>
              <td>{{ relationshipLabel(neighbor.relationship_type) }}</td>
              <td>{{ neighbor.unit_identifier }}</td>
              <td>{{ neighbor.document_number || "" }}</td>
              <td>{{ neighbor.email }}</td>
              <td>{{ neighbor.phone || "" }}</td>
              <td>
                <span class="boolean-chip" :class="neighbor.is_primary_contact ? 'is-on' : 'is-off'">
                  <svg class="icon" aria-hidden="true"><use href="#icon-shield" /></svg>
                  <span>{{ neighbor.is_primary_contact ? "Si" : "No" }}</span>
                </span>
              </td>
              <td>
                <span class="boolean-chip" :class="neighbor.receives_notifications ? 'is-on' : 'is-off'">
                  <svg class="icon" aria-hidden="true"><use href="#icon-message" /></svg>
                  <span>{{ neighbor.receives_notifications ? "Si" : "No" }}</span>
                </span>
              </td>
              <td>
                <span class="status-badge" :class="statusBadgeClass(neighbor.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(neighbor.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact navy" type="button" @click="openEditNeighbor(neighbor)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                  <span>Editar</span>
                </button>
                <button class="button compact danger" type="button" @click="askDeleteNeighbor(neighbor)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                  <span>Borrar</span>
                </button>
              </td>
            </tr>
            <tr v-if="!neighbors.length">
              <td class="empty-row" colspan="10">{{ loading ? "Cargando vecinos..." : "Sin vecinos para mostrar." }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else class="edifito-table entity-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Unidad</th>
              <th>Codigo</th>
              <th>Piso</th>
              <th>Tipo</th>
              <th>Prorrateo</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="unit in units" :key="unit.id">
              <td class="mono-cell">{{ unit.id }}</td>
              <td><strong>{{ unit.identifier }}</strong></td>
              <td>{{ unit.external_code || "" }}</td>
              <td>{{ unit.floor || "" }}</td>
              <td>{{ unitTypeLabel(unit.unit_type) }}</td>
              <td>{{ unit.proration_total ?? unit.proration ?? "" }}</td>
              <td class="actions-cell">
                <button class="button compact navy" type="button" @click="openEditUnit(unit)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                  <span>Editar</span>
                </button>
                <button class="button compact danger" type="button" @click="askDeleteUnit(unit)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                  <span>Borrar</span>
                </button>
              </td>
            </tr>
            <tr v-if="!units.length">
              <td class="empty-row" colspan="7">{{ loading ? "Cargando unidades..." : "Sin unidades para mostrar." }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="entity-pagination">
        <span>{{ rangeLabel }}</span>
        <div class="pagination-controls">
          <label>
            Filas
            <select v-model.number="currentMeta.page_size" @change="changePageSize">
              <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
            </select>
          </label>
          <button class="button ghost compact" type="button" :disabled="currentMeta.page <= 1" @click="goPage(1)">
            <svg class="icon" aria-hidden="true"><use href="#icon-chevrons-left" /></svg>
            <span>Primera</span>
          </button>
          <button class="button ghost compact" type="button" :disabled="currentMeta.page <= 1" @click="goPage(currentMeta.page - 1)">
            <svg class="icon" aria-hidden="true"><use href="#icon-chevron-left" /></svg>
            <span>Anterior</span>
          </button>
          <strong>{{ pageLabel }}</strong>
          <button class="button ghost compact" type="button" :disabled="currentMeta.page >= currentMeta.pages" @click="goPage(currentMeta.page + 1)">
            <span>Siguiente</span>
            <svg class="icon" aria-hidden="true"><use href="#icon-chevron-right" /></svg>
          </button>
          <button class="button ghost compact" type="button" :disabled="currentMeta.page >= currentMeta.pages" @click="goPage(currentMeta.pages)">
            <span>Ultima</span>
            <svg class="icon" aria-hidden="true"><use href="#icon-chevrons-right" /></svg>
          </button>
        </div>
      </div>
    </div>

    <form v-else-if="mode === 'neighborForm'" class="entity-form" @submit.prevent="saveNeighbor">
      <p v-if="neighborForm.id" class="record-id">ID: {{ neighborForm.id }}</p>
      <div class="entity-form-grid">
        <label>
          Nombre completo
          <input v-model="neighborForm.full_name" maxlength="150" required />
        </label>
        <label>
          Email
          <input v-model="neighborForm.email" type="email" maxlength="255" />
        </label>
        <label>
          Telefono
          <input v-model="neighborForm.phone" maxlength="40" />
        </label>
        <label>
          Unidad
          <select v-model="neighborForm.unit_id">
            <option value="">Sin unidad</option>
            <option v-for="unit in units" :key="unit.id" :value="unit.id">{{ unit.identifier }}</option>
          </select>
        </label>
        <label>
          Relacion con la unidad
          <select v-model="neighborForm.relationship_type">
            <option v-for="[value, label] in relationshipOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Tipo documento
          <select v-model="neighborForm.document_type">
            <option v-for="[value, label] in documentTypeOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Documento
          <input v-model="neighborForm.document_number" maxlength="40" />
        </label>
        <label class="span-all">
          Direccion
          <input v-model="neighborForm.address" maxlength="255" />
        </label>
        <label>
          Estado
          <select v-model="neighborForm.status">
            <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Inicio relacion
          <input v-model="neighborForm.start_date" type="date" />
        </label>
        <label>
          Fin relacion
          <input v-model="neighborForm.end_date" type="date" />
        </label>
        <label class="checkbox-field">
          <input v-model="neighborForm.is_primary_contact" type="checkbox" />
          Contacto principal
        </label>
        <label class="checkbox-field">
          <input v-model="neighborForm.receives_notifications" type="checkbox" />
          Recibe notificaciones
        </label>
        <label class="span-all">
          Metadata
          <textarea v-model="neighborForm.metadata" rows="4" placeholder="{}" />
        </label>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar vecino</span>
        </button>
      </div>
    </form>

    <form v-else class="entity-form" @submit.prevent="saveUnit">
      <p v-if="unitForm.id" class="record-id">ID: {{ unitForm.id }}</p>
      <div class="entity-form-grid">
        <label>
          Unidad
          <input v-model="unitForm.identifier" required />
        </label>
        <label>
          Piso
          <input v-model="unitForm.floor" maxlength="20" />
        </label>
        <label>
          Tipo
          <select v-model="unitForm.unit_type">
            <option v-for="[value, label] in unitTypeOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Codigo externo
          <input v-model="unitForm.external_code" />
        </label>
        <label>
          N asignacion
          <input v-model="unitForm.allocation_number" type="number" step="1" />
        </label>
        <label>
          Asignacion
          <textarea v-model="unitForm.allocation_identifier" rows="3" />
        </label>
        <label>
          % prorrateo total
          <input v-model="unitForm.proration_total" inputmode="decimal" />
        </label>
        <label>
          % prorrateo
          <input v-model="unitForm.proration" inputmode="decimal" />
        </label>
        <label>
          Fecha asignacion
          <input v-model="unitForm.assignment_date" type="date" />
        </label>
        <label class="span-all">
          Metadata
          <textarea v-model="unitForm.metadata" rows="5" placeholder="{}" />
        </label>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar unidad</span>
        </button>
      </div>
    </form>
  </section>

  <div v-if="deleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-title">
    <div class="confirm-modal">
      <p class="eyebrow">Confirmacion</p>
      <h2 id="delete-title">Borrar {{ deleteCandidate.type === "neighbor" ? "vecino" : "unidad" }}</h2>
      <p>Esta accion eliminara {{ deleteCandidate.label }} del condominio activo.</p>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="cancelDelete">Cancelar</button>
        <button class="button danger" type="button" @click="confirmDelete">Borrar</button>
      </div>
    </div>
  </div>
</template>
