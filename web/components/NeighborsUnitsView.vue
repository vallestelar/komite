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

type CommonAreaRecord = {
  id: string;
  condominium_id: string;
  name: string;
  area_type: string;
  location?: string | null;
  capacity?: number | null;
  requires_reservation: boolean;
  status: string;
  notes?: string | null;
  metadata?: Record<string, unknown>;
};

type AssetRecord = {
  id: string;
  condominium_id: string;
  name: string;
  asset_type: string;
  location?: string | null;
  brand?: string | null;
  model?: string | null;
  serial_number?: string | null;
  provider?: string | null;
  installation_date?: string | null;
  requires_maintenance: boolean;
  maintenance_frequency?: string | null;
  status: string;
  notes?: string | null;
  metadata?: Record<string, unknown>;
};

type UnitAnnexRecord = {
  id: string;
  condominium_id: string;
  unit_id: string;
  annex_type: string;
  identifier: string;
  description?: string | null;
  status: string;
  metadata?: Record<string, unknown>;
};

type UnitPetRecord = {
  id: string;
  condominium_id: string;
  unit_id: string;
  name: string;
  species: string;
  breed?: string | null;
  color?: string | null;
  chip_number?: string | null;
  status: string;
  notes?: string | null;
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

type CommonAreaForm = {
  id: string;
  name: string;
  area_type: string;
  location: string;
  capacity: string;
  requires_reservation: boolean;
  status: string;
  notes: string;
  metadata: string;
};

type AssetForm = {
  id: string;
  name: string;
  asset_type: string;
  location: string;
  brand: string;
  model: string;
  serial_number: string;
  provider: string;
  installation_date: string;
  requires_maintenance: boolean;
  maintenance_frequency: string;
  status: string;
  notes: string;
  metadata: string;
};

type UnitAnnexForm = {
  id: string;
  unit_id: string;
  annex_type: string;
  identifier: string;
  description: string;
  status: string;
};

type UnitPetForm = {
  id: string;
  unit_id: string;
  name: string;
  species: string;
  breed: string;
  color: string;
  chip_number: string;
  status: string;
  notes: string;
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

const props = defineProps<{
  focusNeighborId?: string;
}>();

const { request } = useApi();
const { activeCondominium } = useAuth();

type EntityTab = "neighbors" | "common" | "assets" | "units" | "annexes" | "pets";

const activeTab = ref<EntityTab>("neighbors");
const commonAreas = ref<CommonAreaRecord[]>([]);
const assets = ref<AssetRecord[]>([]);
const units = ref<UnitRecord[]>([]);
const unitLookup = ref<UnitRecord[]>([]);
const unitAnnexes = ref<UnitAnnexRecord[]>([]);
const unitPets = ref<UnitPetRecord[]>([]);
const neighbors = ref<NeighborRecord[]>([]);
const unitsMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const neighborsMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const commonAreasMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const assetsMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const annexesMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const petsMeta = reactive<PageMeta>({ total: 0, page: 1, page_size: 10, pages: 1 });
const unitsSearch = ref("");
const neighborsSearch = ref("");
const commonAreasSearch = ref("");
const assetsSearch = ref("");
const annexesSearch = ref("");
const petsSearch = ref("");
const loading = ref(false);
const errorMessage = ref("");
const formError = ref("");
const toastMessage = ref("");
const searchTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const mode = ref<"list" | "neighborForm" | "commonAreaForm" | "assetForm" | "unitForm" | "annexForm" | "petForm">("list");
const deleteCandidate = ref<{ type: "neighbor" | "commonArea" | "asset" | "unit" | "annex" | "pet"; id: string; label: string } | null>(null);

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

const commonAreaForm = reactive<CommonAreaForm>({
  id: "",
  name: "",
  area_type: "pool",
  location: "",
  capacity: "",
  requires_reservation: false,
  status: "active",
  notes: "",
  metadata: "{}",
});

const assetForm = reactive<AssetForm>({
  id: "",
  name: "",
  asset_type: "pump",
  location: "",
  brand: "",
  model: "",
  serial_number: "",
  provider: "",
  installation_date: "",
  requires_maintenance: true,
  maintenance_frequency: "",
  status: "active",
  notes: "",
  metadata: "{}",
});

const unitAnnexForm = reactive<UnitAnnexForm>({
  id: "",
  unit_id: "",
  annex_type: "parking",
  identifier: "",
  description: "",
  status: "active",
});

const unitPetForm = reactive<UnitPetForm>({
  id: "",
  unit_id: "",
  name: "",
  species: "dog",
  breed: "",
  color: "",
  chip_number: "",
  status: "active",
  notes: "",
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
const commonAreaTypeOptions = [
  ["pool", "Piscina"],
  ["barbecue", "Quincho"],
  ["garden", "Jardin"],
  ["multipurpose_room", "Sala multiuso"],
  ["gym", "Gimnasio"],
  ["playground", "Juegos infantiles"],
  ["laundry", "Lavanderia"],
  ["parking_common", "Estacionamiento comun"],
  ["other", "Otro"],
];
const assetTypeOptions = [
  ["pump", "Bomba"],
  ["elevator", "Ascensor"],
  ["gate", "Porton"],
  ["boiler", "Caldera"],
  ["electrical_panel", "Tablero electrico"],
  ["camera", "Camara"],
  ["pool_equipment", "Equipo piscina"],
  ["generator", "Generador"],
  ["sensor", "Sensor"],
  ["other", "Otro"],
];
const annexTypeOptions = [
  ["parking", "Estacionamiento"],
  ["storage", "Bodega"],
  ["locker", "Locker"],
  ["bike_storage", "Bicicletero"],
  ["other", "Otro"],
];
const petSpeciesOptions = [
  ["dog", "Perro"],
  ["cat", "Gato"],
  ["bird", "Ave"],
  ["other", "Otro"],
];

const currentMeta = computed(() => {
  if (activeTab.value === "neighbors") return neighborsMeta;
  if (activeTab.value === "common") return commonAreasMeta;
  if (activeTab.value === "assets") return assetsMeta;
  if (activeTab.value === "units") return unitsMeta;
  if (activeTab.value === "annexes") return annexesMeta;
  return petsMeta;
});
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
  if (mode.value === "commonAreaForm") return commonAreaForm.id ? "Editar espacio" : "Nuevo espacio";
  if (mode.value === "assetForm") return assetForm.id ? "Editar activo" : "Nuevo activo";
  if (mode.value === "unitForm") return unitForm.id ? "Editar unidad" : "Nueva unidad";
  if (mode.value === "annexForm") return unitAnnexForm.id ? "Editar anexo" : "Nuevo anexo";
  if (mode.value === "petForm") return unitPetForm.id ? "Editar mascota" : "Nueva mascota";
  return "Condominio";
});

const deleteTypeLabel = computed(() => {
  if (deleteCandidate.value?.type === "neighbor") return "vecino";
  if (deleteCandidate.value?.type === "commonArea") return "espacio";
  if (deleteCandidate.value?.type === "asset") return "activo";
  if (deleteCandidate.value?.type === "unit") return "unidad";
  if (deleteCandidate.value?.type === "annex") return "anexo";
  if (deleteCandidate.value?.type === "pet") return "mascota";
  return "registro";
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

const formatDate = (value: string | null | undefined) => {
  if (!value) return "";
  const [datePart] = value.split("T");
  const parts = datePart.split("-");
  if (parts.length !== 3) return value;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
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

const loadUnitLookup = async () => {
  const data = await request<{ items?: UnitRecord[] }>("/api/v1/units/?page=1&page_size=200");
  unitLookup.value = data.items || [];
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

const loadCommonAreas = async () => {
  const params = new URLSearchParams({
    page: String(commonAreasMeta.page),
    page_size: String(commonAreasMeta.page_size),
  });
  if (commonAreasSearch.value.trim()) params.set("q", commonAreasSearch.value.trim());
  const data = await request<{ items?: CommonAreaRecord[]; meta?: PageMeta }>(`/api/v1/common-areas/?${params}`);
  commonAreas.value = data.items || [];
  Object.assign(commonAreasMeta, data.meta || { total: commonAreas.value.length, page: commonAreasMeta.page, page_size: commonAreasMeta.page_size, pages: 1 });
};

const loadAssets = async () => {
  const params = new URLSearchParams({
    page: String(assetsMeta.page),
    page_size: String(assetsMeta.page_size),
  });
  if (assetsSearch.value.trim()) params.set("q", assetsSearch.value.trim());
  const data = await request<{ items?: AssetRecord[]; meta?: PageMeta }>(`/api/v1/condominium-assets/?${params}`);
  assets.value = data.items || [];
  Object.assign(assetsMeta, data.meta || { total: assets.value.length, page: assetsMeta.page, page_size: assetsMeta.page_size, pages: 1 });
};

const loadAnnexes = async () => {
  const params = new URLSearchParams({
    page: String(annexesMeta.page),
    page_size: String(annexesMeta.page_size),
  });
  if (annexesSearch.value.trim()) params.set("q", annexesSearch.value.trim());
  const data = await request<{ items?: UnitAnnexRecord[]; meta?: PageMeta }>(`/api/v1/unit-annexes/?${params}`);
  unitAnnexes.value = data.items || [];
  Object.assign(annexesMeta, data.meta || { total: unitAnnexes.value.length, page: annexesMeta.page, page_size: annexesMeta.page_size, pages: 1 });
};

const loadPets = async () => {
  const params = new URLSearchParams({
    page: String(petsMeta.page),
    page_size: String(petsMeta.page_size),
  });
  if (petsSearch.value.trim()) params.set("q", petsSearch.value.trim());
  const data = await request<{ items?: UnitPetRecord[]; meta?: PageMeta }>(`/api/v1/unit-pets/?${params}`);
  unitPets.value = data.items || [];
  Object.assign(petsMeta, data.meta || { total: unitPets.value.length, page: petsMeta.page, page_size: petsMeta.page_size, pages: 1 });
};

const loadUnitRelated = async (unitId: string) => {
  if (!unitId) {
    unitAnnexes.value = [];
    unitPets.value = [];
    return;
  }

  const params = new URLSearchParams({
    page: "1",
    page_size: "200",
    filter_unit_id: unitId,
  });
  const [annexData, petData] = await Promise.all([
    request<{ items?: UnitAnnexRecord[] }>(`/api/v1/unit-annexes/?${params}`),
    request<{ items?: UnitPetRecord[] }>(`/api/v1/unit-pets/?${params}`),
  ]);
  unitAnnexes.value = annexData.items || [];
  unitPets.value = petData.items || [];
};

const loadActiveTab = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    if (activeTab.value === "neighbors") {
      await Promise.all([loadNeighbors(), loadUnits()]);
    } else if (activeTab.value === "common") {
      await loadCommonAreas();
    } else if (activeTab.value === "assets") {
      await loadAssets();
    } else if (activeTab.value === "units") {
      await loadUnits();
    } else if (activeTab.value === "annexes") {
      await Promise.all([loadAnnexes(), loadUnitLookup()]);
    } else {
      await Promise.all([loadPets(), loadUnitLookup()]);
    }
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const selectTab = async (tab: EntityTab) => {
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

const openNeighborById = async (neighborId: string) => {
  if (!neighborId) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const neighbor = await request<NeighborRecord>(`/api/v1/portal/neighbors/${neighborId}`);
    activeTab.value = "neighbors";
    await openEditNeighbor(neighbor);
  } catch (error) {
    errorMessage.value = readableError(error);
    mode.value = "list";
  } finally {
    loading.value = false;
  }
};

const openCreateUnit = () => {
  resetUnitForm();
  mode.value = "unitForm";
};

const openCreateCommonArea = () => {
  resetCommonAreaForm();
  mode.value = "commonAreaForm";
};

const openCreateAsset = () => {
  resetAssetForm();
  mode.value = "assetForm";
};

const openCreateAnnex = async () => {
  resetUnitAnnexForm();
  await loadUnitLookup();
  mode.value = "annexForm";
};

const openCreatePet = async () => {
  resetUnitPetForm();
  await loadUnitLookup();
  mode.value = "petForm";
};

const openEditUnit = async (unit: UnitRecord) => {
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
  resetUnitAnnexForm();
  resetUnitPetForm();
  await loadUnitRelated(unit.id);
  formError.value = "";
  mode.value = "unitForm";
};

const openEditCommonArea = (area: CommonAreaRecord) => {
  commonAreaForm.id = area.id;
  commonAreaForm.name = area.name || "";
  commonAreaForm.area_type = area.area_type || "other";
  commonAreaForm.location = area.location || "";
  commonAreaForm.capacity = area.capacity != null ? String(area.capacity) : "";
  commonAreaForm.requires_reservation = Boolean(area.requires_reservation);
  commonAreaForm.status = area.status || "active";
  commonAreaForm.notes = area.notes || "";
  commonAreaForm.metadata = JSON.stringify(area.metadata || {}, null, 2);
  formError.value = "";
  mode.value = "commonAreaForm";
};

const openEditAsset = (asset: AssetRecord) => {
  assetForm.id = asset.id;
  assetForm.name = asset.name || "";
  assetForm.asset_type = asset.asset_type || "other";
  assetForm.location = asset.location || "";
  assetForm.brand = asset.brand || "";
  assetForm.model = asset.model || "";
  assetForm.serial_number = asset.serial_number || "";
  assetForm.provider = asset.provider || "";
  assetForm.installation_date = asset.installation_date || "";
  assetForm.requires_maintenance = Boolean(asset.requires_maintenance);
  assetForm.maintenance_frequency = asset.maintenance_frequency || "";
  assetForm.status = asset.status || "active";
  assetForm.notes = asset.notes || "";
  assetForm.metadata = JSON.stringify(asset.metadata || {}, null, 2);
  formError.value = "";
  mode.value = "assetForm";
};

const openEditAnnex = async (annex: UnitAnnexRecord) => {
  await loadUnitLookup();
  unitAnnexForm.id = annex.id;
  unitAnnexForm.unit_id = annex.unit_id;
  unitAnnexForm.annex_type = annex.annex_type || "parking";
  unitAnnexForm.identifier = annex.identifier || "";
  unitAnnexForm.description = annex.description || "";
  unitAnnexForm.status = annex.status || "active";
  formError.value = "";
  mode.value = "annexForm";
};

const openEditPet = async (pet: UnitPetRecord) => {
  await loadUnitLookup();
  unitPetForm.id = pet.id;
  unitPetForm.unit_id = pet.unit_id;
  unitPetForm.name = pet.name || "";
  unitPetForm.species = pet.species || "dog";
  unitPetForm.breed = pet.breed || "";
  unitPetForm.color = pet.color || "";
  unitPetForm.chip_number = pet.chip_number || "";
  unitPetForm.status = pet.status || "active";
  unitPetForm.notes = pet.notes || "";
  formError.value = "";
  mode.value = "petForm";
};

const returnToList = async () => {
  mode.value = "list";
  resetNeighborForm();
  resetCommonAreaForm();
  resetAssetForm();
  resetUnitForm();
  resetUnitAnnexForm();
  resetUnitPetForm();
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

const saveCommonArea = async () => {
  formError.value = "";
  if (!activeCondominium.value?.id) {
    formError.value = "Selecciona un condominio activo antes de guardar.";
    return;
  }

  let parsedMetadata: Record<string, unknown>;
  try {
    parsedMetadata = commonAreaForm.metadata.trim() ? JSON.parse(commonAreaForm.metadata) : {};
  } catch {
    formError.value = "Metadata debe ser un JSON valido.";
    return;
  }

  const payload = {
    condominium_id: activeCondominium.value.id,
    name: commonAreaForm.name.trim(),
    area_type: commonAreaForm.area_type,
    location: emptyToNull(commonAreaForm.location),
    capacity: emptyToNumber(commonAreaForm.capacity),
    requires_reservation: commonAreaForm.requires_reservation,
    status: commonAreaForm.status,
    notes: emptyToNull(commonAreaForm.notes),
    metadata: parsedMetadata,
  };
  if (!payload.name) {
    formError.value = "El nombre es obligatorio.";
    return;
  }

  try {
    await request<CommonAreaRecord>(commonAreaForm.id ? `/api/v1/common-areas/${commonAreaForm.id}` : "/api/v1/common-areas/", {
      method: commonAreaForm.id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(commonAreaForm.id ? "Espacio actualizado correctamente." : "Espacio creado correctamente.");
    activeTab.value = "common";
    await returnToList();
  } catch (error) {
    formError.value = readableError(error);
  }
};

const saveAsset = async () => {
  formError.value = "";
  if (!activeCondominium.value?.id) {
    formError.value = "Selecciona un condominio activo antes de guardar.";
    return;
  }

  let parsedMetadata: Record<string, unknown>;
  try {
    parsedMetadata = assetForm.metadata.trim() ? JSON.parse(assetForm.metadata) : {};
  } catch {
    formError.value = "Metadata debe ser un JSON valido.";
    return;
  }

  const payload = {
    condominium_id: activeCondominium.value.id,
    name: assetForm.name.trim(),
    asset_type: assetForm.asset_type,
    location: emptyToNull(assetForm.location),
    brand: emptyToNull(assetForm.brand),
    model: emptyToNull(assetForm.model),
    serial_number: emptyToNull(assetForm.serial_number),
    provider: emptyToNull(assetForm.provider),
    installation_date: emptyToNull(assetForm.installation_date),
    requires_maintenance: assetForm.requires_maintenance,
    maintenance_frequency: emptyToNull(assetForm.maintenance_frequency),
    status: assetForm.status,
    notes: emptyToNull(assetForm.notes),
    metadata: parsedMetadata,
  };
  if (!payload.name) {
    formError.value = "El nombre es obligatorio.";
    return;
  }

  try {
    await request<AssetRecord>(assetForm.id ? `/api/v1/condominium-assets/${assetForm.id}` : "/api/v1/condominium-assets/", {
      method: assetForm.id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast(assetForm.id ? "Activo actualizado correctamente." : "Activo creado correctamente.");
    activeTab.value = "assets";
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
    if (unitForm.id) await loadUnitRelated(unitForm.id);
    await returnToList();
  } catch (error) {
    formError.value = readableError(error);
  }
};

const saveUnitAnnex = async () => {
  formError.value = "";
  if (!activeCondominium.value?.id) return;
  const targetUnitId = unitAnnexForm.unit_id || unitForm.id;
  const payload = {
    condominium_id: activeCondominium.value.id,
    unit_id: targetUnitId,
    annex_type: unitAnnexForm.annex_type,
    identifier: unitAnnexForm.identifier.trim(),
    description: emptyToNull(unitAnnexForm.description),
    status: unitAnnexForm.status,
    metadata: {},
  };
  if (!payload.identifier) {
    formError.value = "Indica un identificador para el anexo.";
    return;
  }
  if (!payload.unit_id) {
    formError.value = "Selecciona la unidad vinculada al anexo.";
    return;
  }

  try {
    const wasEditing = Boolean(unitAnnexForm.id);
    await request<UnitAnnexRecord>(unitAnnexForm.id ? `/api/v1/unit-annexes/${unitAnnexForm.id}` : "/api/v1/unit-annexes/", {
      method: unitAnnexForm.id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    resetUnitAnnexForm();
    if (mode.value === "unitForm" && unitForm.id) await loadUnitRelated(unitForm.id);
    if (mode.value === "annexForm") {
      activeTab.value = "annexes";
      await returnToList();
    }
    showToast(wasEditing ? "Anexo actualizado correctamente." : "Anexo añadido correctamente.");
  } catch (error) {
    formError.value = readableError(error);
  }
};

const saveUnitPet = async () => {
  formError.value = "";
  if (!activeCondominium.value?.id) return;
  const targetUnitId = unitPetForm.unit_id || unitForm.id;
  const payload = {
    condominium_id: activeCondominium.value.id,
    unit_id: targetUnitId,
    name: unitPetForm.name.trim(),
    species: unitPetForm.species,
    breed: emptyToNull(unitPetForm.breed),
    color: emptyToNull(unitPetForm.color),
    chip_number: emptyToNull(unitPetForm.chip_number),
    status: unitPetForm.status,
    notes: emptyToNull(unitPetForm.notes),
    metadata: {},
  };
  if (!payload.name) {
    formError.value = "Indica el nombre de la mascota.";
    return;
  }
  if (!payload.unit_id) {
    formError.value = "Selecciona la unidad vinculada a la mascota.";
    return;
  }

  try {
    const wasEditing = Boolean(unitPetForm.id);
    await request<UnitPetRecord>(unitPetForm.id ? `/api/v1/unit-pets/${unitPetForm.id}` : "/api/v1/unit-pets/", {
      method: unitPetForm.id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    resetUnitPetForm();
    if (mode.value === "unitForm" && unitForm.id) await loadUnitRelated(unitForm.id);
    if (mode.value === "petForm") {
      activeTab.value = "pets";
      await returnToList();
    }
    showToast(wasEditing ? "Mascota actualizada correctamente." : "Mascota añadida correctamente.");
  } catch (error) {
    formError.value = readableError(error);
  }
};

const askDeleteNeighbor = (neighbor: NeighborRecord) => {
  deleteCandidate.value = { type: "neighbor", id: neighbor.id, label: neighbor.full_name };
};

const askDeleteCommonArea = (area: CommonAreaRecord) => {
  deleteCandidate.value = { type: "commonArea", id: area.id, label: area.name };
};

const askDeleteAsset = (asset: AssetRecord) => {
  deleteCandidate.value = { type: "asset", id: asset.id, label: asset.name };
};

const askDeleteUnit = (unit: UnitRecord) => {
  deleteCandidate.value = { type: "unit", id: unit.id, label: unit.identifier };
};

const askDeleteAnnex = (annex: UnitAnnexRecord) => {
  deleteCandidate.value = { type: "annex", id: annex.id, label: annex.identifier };
};

const askDeletePet = (pet: UnitPetRecord) => {
  deleteCandidate.value = { type: "pet", id: pet.id, label: pet.name };
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
    } else if (deleteCandidate.value.type === "commonArea") {
      await request(`/api/v1/common-areas/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Espacio eliminado correctamente.");
      activeTab.value = "common";
    } else if (deleteCandidate.value.type === "asset") {
      await request(`/api/v1/condominium-assets/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Activo eliminado correctamente.");
      activeTab.value = "assets";
    } else if (deleteCandidate.value.type === "unit") {
      await request(`/api/v1/units/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Unidad eliminada correctamente.");
      activeTab.value = "units";
    } else if (deleteCandidate.value.type === "annex") {
      await request(`/api/v1/unit-annexes/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Anexo eliminado correctamente.");
      if (unitForm.id) await loadUnitRelated(unitForm.id);
    } else {
      await request(`/api/v1/unit-pets/${deleteCandidate.value.id}`, { method: "DELETE" });
      showToast("Mascota eliminada correctamente.");
      if (unitForm.id) await loadUnitRelated(unitForm.id);
    }
    deleteCandidate.value = null;
    if (mode.value === "list") await loadActiveTab();
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
  unitAnnexes.value = [];
  unitPets.value = [];
  resetUnitAnnexForm();
  resetUnitPetForm();
  formError.value = "";
};

const resetCommonAreaForm = () => {
  commonAreaForm.id = "";
  commonAreaForm.name = "";
  commonAreaForm.area_type = "pool";
  commonAreaForm.location = "";
  commonAreaForm.capacity = "";
  commonAreaForm.requires_reservation = false;
  commonAreaForm.status = "active";
  commonAreaForm.notes = "";
  commonAreaForm.metadata = "{}";
  formError.value = "";
};

const resetAssetForm = () => {
  assetForm.id = "";
  assetForm.name = "";
  assetForm.asset_type = "pump";
  assetForm.location = "";
  assetForm.brand = "";
  assetForm.model = "";
  assetForm.serial_number = "";
  assetForm.provider = "";
  assetForm.installation_date = "";
  assetForm.requires_maintenance = true;
  assetForm.maintenance_frequency = "";
  assetForm.status = "active";
  assetForm.notes = "";
  assetForm.metadata = "{}";
  formError.value = "";
};

const resetUnitAnnexForm = () => {
  unitAnnexForm.id = "";
  unitAnnexForm.unit_id = "";
  unitAnnexForm.annex_type = "parking";
  unitAnnexForm.identifier = "";
  unitAnnexForm.description = "";
  unitAnnexForm.status = "active";
};

const resetUnitPetForm = () => {
  unitPetForm.id = "";
  unitPetForm.unit_id = "";
  unitPetForm.name = "";
  unitPetForm.species = "dog";
  unitPetForm.breed = "";
  unitPetForm.color = "";
  unitPetForm.chip_number = "";
  unitPetForm.status = "active";
  unitPetForm.notes = "";
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
const commonAreaTypeLabel = (value: string) => commonAreaTypeOptions.find(([key]) => key === value)?.[1] || value;
const assetTypeLabel = (value: string) => assetTypeOptions.find(([key]) => key === value)?.[1] || value;
const annexTypeLabel = (value: string) => annexTypeOptions.find(([key]) => key === value)?.[1] || value;
const petSpeciesLabel = (value: string) => petSpeciesOptions.find(([key]) => key === value)?.[1] || value;
const unitIdentifier = (unitId: string) => unitLookup.value.find((unit) => unit.id === unitId)?.identifier || "Sin unidad";

onMounted(async () => {
  if (props.focusNeighborId) {
    await openNeighborById(props.focusNeighborId);
    return;
  }
  await loadActiveTab();
});

watch(() => props.focusNeighborId, async (neighborId) => {
  if (neighborId) await openNeighborById(neighborId);
});
</script>

<template>
  <section class="panel entity-panel">
    <div class="entity-header">
      <div>
        <p class="eyebrow">Condominio</p>
        <h2>{{ title }}</h2>
        <p class="placeholder-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <button v-if="mode !== 'list'" class="button ghost" type="button" @click="returnToList">
        <svg class="icon" aria-hidden="true"><use href="#icon-arrow-left" /></svg>
        <span>Volver al listado</span>
      </button>
    </div>

    <div v-if="mode === 'list'" class="entity-list">
      <div class="entity-tabs" role="tablist" aria-label="Condominio">
        <button class="button compact" :class="activeTab === 'neighbors' ? 'navy' : 'ghost'" type="button" @click="selectTab('neighbors')">
          <svg class="icon" aria-hidden="true"><use href="#icon-users" /></svg>
          <span>Vecinos</span>
        </button>
        <button class="button compact" :class="activeTab === 'units' ? 'navy' : 'ghost'" type="button" @click="selectTab('units')">
          <svg class="icon" aria-hidden="true"><use href="#icon-home" /></svg>
          <span>Unidades</span>
        </button>
        <button class="button compact" :class="activeTab === 'annexes' ? 'navy' : 'ghost'" type="button" @click="selectTab('annexes')">
          <svg class="icon" aria-hidden="true"><use href="#icon-link" /></svg>
          <span>Anexos</span>
        </button>
        <button class="button compact" :class="activeTab === 'pets' ? 'navy' : 'ghost'" type="button" @click="selectTab('pets')">
          <svg class="icon" aria-hidden="true"><use href="#icon-paw" /></svg>
          <span>Mascotas</span>
        </button>
        <button class="button compact" :class="activeTab === 'common' ? 'navy' : 'ghost'" type="button" @click="selectTab('common')">
          <svg class="icon" aria-hidden="true"><use href="#icon-plant" /></svg>
          <span>Espacios</span>
        </button>
        <button class="button compact" :class="activeTab === 'assets' ? 'navy' : 'ghost'" type="button" @click="selectTab('assets')">
          <svg class="icon" aria-hidden="true"><use href="#icon-tool" /></svg>
          <span>Activos</span>
        </button>
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
          v-else-if="activeTab === 'common'"
          v-model="commonAreasSearch"
          type="search"
          placeholder="Buscar piscina, quincho, jardin o sala"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <input
          v-else-if="activeTab === 'assets'"
          v-model="assetsSearch"
          type="search"
          placeholder="Buscar activo, tipo, marca, serie o proveedor"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <input
          v-else-if="activeTab === 'units'"
          v-model="unitsSearch"
          type="search"
          placeholder="Buscar unidad"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <input
          v-else-if="activeTab === 'annexes'"
          v-model="annexesSearch"
          type="search"
          placeholder="Buscar anexo, tipo o unidad"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <input
          v-else
          v-model="petsSearch"
          type="search"
          placeholder="Buscar mascota, especie o chip"
          @input="scheduleSearch"
          @keydown.enter.prevent="loadActiveTab"
        />
        <button v-if="activeTab === 'neighbors'" class="button orange" type="button" @click="openCreateNeighbor">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo vecino</span>
        </button>
        <button v-else-if="activeTab === 'common'" class="button orange" type="button" @click="openCreateCommonArea">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo espacio</span>
        </button>
        <button v-else-if="activeTab === 'assets'" class="button orange" type="button" @click="openCreateAsset">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo activo</span>
        </button>
        <button v-else-if="activeTab === 'units'" class="button orange" type="button" @click="openCreateUnit">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nueva unidad</span>
        </button>
        <button v-else-if="activeTab === 'annexes'" class="button orange" type="button" @click="openCreateAnnex">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo anexo</span>
        </button>
        <button v-else class="button orange" type="button" @click="openCreatePet">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nueva mascota</span>
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
              <th>Relación</th>
              <th>Unidad</th>
              <th>Documento</th>
              <th>Email</th>
              <th>Teléfono</th>
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
                <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditNeighbor(neighbor)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar" title="Borrar" @click="askDeleteNeighbor(neighbor)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!neighbors.length">
              <td class="empty-row" colspan="10">{{ loading ? "Cargando vecinos..." : "Sin vecinos para mostrar." }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="activeTab === 'common'" class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Ubicación</th>
              <th>Capacidad</th>
              <th>Reserva</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="area in commonAreas" :key="area.id">
              <td><strong>{{ area.name }}</strong></td>
              <td>{{ commonAreaTypeLabel(area.area_type) }}</td>
              <td>{{ area.location || "" }}</td>
              <td>{{ area.capacity ?? "" }}</td>
              <td>
                <span class="boolean-chip" :class="area.requires_reservation ? 'is-on' : 'is-off'">
                  <svg class="icon" aria-hidden="true"><use href="#icon-calendar" /></svg>
                  <span>{{ area.requires_reservation ? "Si" : "No" }}</span>
                </span>
              </td>
              <td>
                <span class="status-badge" :class="statusBadgeClass(area.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(area.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditCommonArea(area)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar" title="Borrar" @click="askDeleteCommonArea(area)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!commonAreas.length">
              <td class="empty-row" colspan="7">{{ loading ? "Cargando espacios..." : "Sin espacios para mostrar." }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="activeTab === 'assets'" class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Ubicacion</th>
              <th>Marca / modelo</th>
              <th>Serie</th>
              <th>Mantenimiento</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="asset in assets" :key="asset.id">
              <td><strong>{{ asset.name }}</strong></td>
              <td>{{ assetTypeLabel(asset.asset_type) }}</td>
              <td>{{ asset.location || "" }}</td>
              <td>{{ [asset.brand, asset.model].filter(Boolean).join(" / ") }}</td>
              <td>{{ asset.serial_number || "" }}</td>
              <td>
                <span class="boolean-chip" :class="asset.requires_maintenance ? 'is-on' : 'is-off'">
                  <svg class="icon" aria-hidden="true"><use href="#icon-tool" /></svg>
                  <span>{{ asset.requires_maintenance ? (asset.maintenance_frequency || "Si") : "No" }}</span>
                </span>
              </td>
              <td>
                <span class="status-badge" :class="statusBadgeClass(asset.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(asset.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditAsset(asset)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar" title="Borrar" @click="askDeleteAsset(asset)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!assets.length">
              <td class="empty-row" colspan="8">{{ loading ? "Cargando activos..." : "Sin activos para mostrar." }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="activeTab === 'units'" class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Unidad</th>
              <th>Código</th>
              <th>Piso</th>
              <th>Tipo</th>
              <th>Prorrateo</th>
              <th>Fecha asignación</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="unit in units" :key="unit.id">
              <td><strong>{{ unit.identifier }}</strong></td>
              <td>{{ unit.external_code || "" }}</td>
              <td>{{ unit.floor || "" }}</td>
              <td>{{ unitTypeLabel(unit.unit_type) }}</td>
              <td>{{ unit.proration_total ?? unit.proration ?? "" }}</td>
              <td>{{ formatDate(unit.assignment_date) || "Sin fecha" }}</td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditUnit(unit)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar" title="Borrar" @click="askDeleteUnit(unit)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!units.length">
              <td class="empty-row" colspan="7">{{ loading ? "Cargando unidades..." : "Sin unidades para mostrar." }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="activeTab === 'annexes'" class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Unidad</th>
              <th>Tipo</th>
              <th>Identificador</th>
              <th>Descripcion</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="annex in unitAnnexes" :key="annex.id">
              <td><strong>{{ unitIdentifier(annex.unit_id) }}</strong></td>
              <td>{{ annexTypeLabel(annex.annex_type) }}</td>
              <td>{{ annex.identifier }}</td>
              <td>{{ annex.description || "" }}</td>
              <td>
                <span class="status-badge" :class="statusBadgeClass(annex.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(annex.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditAnnex(annex)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar" title="Borrar" @click="askDeleteAnnex(annex)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!unitAnnexes.length">
              <td class="empty-row" colspan="6">{{ loading ? "Cargando anexos..." : "Sin anexos para mostrar." }}</td>
            </tr>
          </tbody>
        </table>

        <table v-else class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Unidad</th>
              <th>Nombre</th>
              <th>Especie</th>
              <th>Raza</th>
              <th>Color</th>
              <th>Chip</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pet in unitPets" :key="pet.id">
              <td><strong>{{ unitIdentifier(pet.unit_id) }}</strong></td>
              <td>{{ pet.name }}</td>
              <td>{{ petSpeciesLabel(pet.species) }}</td>
              <td>{{ pet.breed || "" }}</td>
              <td>{{ pet.color || "" }}</td>
              <td>{{ pet.chip_number || "" }}</td>
              <td>
                <span class="status-badge" :class="statusBadgeClass(pet.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(pet.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar" title="Editar" @click="openEditPet(pet)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar" title="Borrar" @click="askDeletePet(pet)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!unitPets.length">
              <td class="empty-row" colspan="8">{{ loading ? "Cargando mascotas..." : "Sin mascotas para mostrar." }}</td>
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
          Teléfono
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
          Relación con la unidad
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
          Dirección
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
        <label class="switch-field">
          <input v-model="neighborForm.is_primary_contact" type="checkbox" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Contacto principal</span>
        </label>
        <label class="switch-field">
          <input v-model="neighborForm.receives_notifications" type="checkbox" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Recibe notificaciones</span>
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

    <form v-else-if="mode === 'commonAreaForm'" class="entity-form" @submit.prevent="saveCommonArea">
      <p v-if="commonAreaForm.id" class="record-id">ID: {{ commonAreaForm.id }}</p>
      <div class="entity-form-grid">
        <label>
          Nombre
          <input v-model="commonAreaForm.name" placeholder="Ej. Piscina principal" maxlength="120" required />
        </label>
        <label>
          Tipo
          <select v-model="commonAreaForm.area_type">
            <option v-for="[value, label] in commonAreaTypeOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Ubicación
          <input v-model="commonAreaForm.location" placeholder="Ej. Patio central" maxlength="160" />
        </label>
        <label>
          Capacidad
          <input v-model="commonAreaForm.capacity" type="number" min="0" step="1" />
        </label>
        <label>
          Estado
          <select v-model="commonAreaForm.status">
            <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label class="switch-field">
          <input v-model="commonAreaForm.requires_reservation" type="checkbox" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Requiere reserva</span>
        </label>
        <label class="span-all">
          Notas
          <textarea v-model="commonAreaForm.notes" rows="3" placeholder="Condiciones de uso, horarios o detalles operativos." />
        </label>
        <label class="span-all">
          Metadata
          <textarea v-model="commonAreaForm.metadata" rows="4" placeholder="{}" />
        </label>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar espacio</span>
        </button>
      </div>
    </form>

    <form v-else-if="mode === 'assetForm'" class="entity-form" @submit.prevent="saveAsset">
      <p v-if="assetForm.id" class="record-id">ID: {{ assetForm.id }}</p>
      <div class="entity-form-grid">
        <label>
          Nombre
          <input v-model="assetForm.name" placeholder="Ej. Bomba principal sala norte" maxlength="140" required />
        </label>
        <label>
          Tipo
          <select v-model="assetForm.asset_type">
            <option v-for="[value, label] in assetTypeOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Ubicacion
          <input v-model="assetForm.location" placeholder="Ej. Sala de bombas" maxlength="160" />
        </label>
        <label>
          Estado
          <select v-model="assetForm.status">
            <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Marca
          <input v-model="assetForm.brand" maxlength="100" />
        </label>
        <label>
          Modelo
          <input v-model="assetForm.model" maxlength="100" />
        </label>
        <label>
          Numero de serie
          <input v-model="assetForm.serial_number" maxlength="100" />
        </label>
        <label>
          Proveedor / mantenedor
          <input v-model="assetForm.provider" maxlength="160" />
        </label>
        <label>
          Fecha instalacion
          <input v-model="assetForm.installation_date" type="date" />
        </label>
        <label>
          Frecuencia mantenimiento
          <input v-model="assetForm.maintenance_frequency" placeholder="Ej. Mensual, trimestral, anual" maxlength="80" />
        </label>
        <label class="switch-field">
          <input v-model="assetForm.requires_maintenance" type="checkbox" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Requiere mantenimiento</span>
        </label>
        <label class="span-all">
          Notas
          <textarea v-model="assetForm.notes" rows="3" placeholder="Datos utiles para inspecciones, mantenciones o incidencias." />
        </label>
        <label class="span-all">
          Metadata
          <textarea v-model="assetForm.metadata" rows="4" placeholder="{}" />
        </label>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar activo</span>
        </button>
      </div>
    </form>

    <form v-else-if="mode === 'unitForm'" class="entity-form" @submit.prevent="saveUnit">
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
          Código externo
          <input v-model="unitForm.external_code" />
        </label>
        <label>
          N asignación
          <input v-model="unitForm.allocation_number" type="number" step="1" />
        </label>
        <label>
          Asignación
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
          Fecha asignación
          <input v-model="unitForm.assignment_date" type="date" />
        </label>
        <label class="span-all">
          Metadata
          <textarea v-model="unitForm.metadata" rows="5" placeholder="{}" />
        </label>
      </div>
      <section v-if="unitForm.id" class="unit-related-panel">
        <header>
          <div>
            <p class="eyebrow">Anexos y mascotas</p>
            <h3>Información vinculada a la unidad</h3>
          </div>
        </header>

        <div class="unit-related-grid">
          <article class="unit-related-card">
            <div class="unit-related-card-title">
              <h4>Anexos</h4>
              <span>{{ unitAnnexes.length }}</span>
            </div>
            <div v-if="unitAnnexes.length" class="unit-related-list">
              <div v-for="annex in unitAnnexes" :key="annex.id" class="unit-related-item">
                <div>
                  <strong>{{ annex.identifier }}</strong>
                  <span>{{ annexTypeLabel(annex.annex_type) }}</span>
                  <small v-if="annex.description">{{ annex.description }}</small>
                </div>
                <span class="status-badge" :class="statusBadgeClass(annex.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(annex.status) }}
                </span>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar anexo" title="Borrar anexo" @click="askDeleteAnnex(annex)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </div>
            </div>
            <p v-else class="placeholder-copy">Sin anexos registrados.</p>

            <div class="unit-related-form">
              <label>
                Tipo
                <select v-model="unitAnnexForm.annex_type">
                  <option v-for="[value, label] in annexTypeOptions" :key="value" :value="value">{{ label }}</option>
                </select>
              </label>
              <label>
                Identificador
                <input v-model="unitAnnexForm.identifier" placeholder="Ej. EST-101" />
              </label>
              <label>
                Estado
                <select v-model="unitAnnexForm.status">
                  <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
                </select>
              </label>
              <label class="span-all">
                Descripción
                <input v-model="unitAnnexForm.description" placeholder="Detalle opcional" />
              </label>
              <button class="button ghost" type="button" @click="saveUnitAnnex">
                <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
                <span>Añadir anexo</span>
              </button>
            </div>
          </article>

          <article class="unit-related-card">
            <div class="unit-related-card-title">
              <h4>Mascotas</h4>
              <span>{{ unitPets.length }}</span>
            </div>
            <div v-if="unitPets.length" class="unit-related-list">
              <div v-for="pet in unitPets" :key="pet.id" class="unit-related-item">
                <div>
                  <strong>{{ pet.name }}</strong>
                  <span>{{ petSpeciesLabel(pet.species) }}</span>
                  <small>{{ [pet.breed, pet.color, pet.chip_number ? `Chip ${pet.chip_number}` : ""].filter(Boolean).join(" · ") }}</small>
                </div>
                <span class="status-badge" :class="statusBadgeClass(pet.status)">
                  <span aria-hidden="true"></span>
                  {{ statusLabel(pet.status) }}
                </span>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar mascota" title="Borrar mascota" @click="askDeletePet(pet)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </div>
            </div>
            <p v-else class="placeholder-copy">Sin mascotas registradas.</p>

            <div class="unit-related-form">
              <label>
                Nombre
                <input v-model="unitPetForm.name" placeholder="Ej. Luna" />
              </label>
              <label>
                Especie
                <select v-model="unitPetForm.species">
                  <option v-for="[value, label] in petSpeciesOptions" :key="value" :value="value">{{ label }}</option>
                </select>
              </label>
              <label>
                Estado
                <select v-model="unitPetForm.status">
                  <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
                </select>
              </label>
              <label>
                Raza
                <input v-model="unitPetForm.breed" />
              </label>
              <label>
                Color
                <input v-model="unitPetForm.color" />
              </label>
              <label>
                Chip
                <input v-model="unitPetForm.chip_number" />
              </label>
              <label class="span-all">
                Notas
                <input v-model="unitPetForm.notes" placeholder="Detalle opcional" />
              </label>
              <button class="button ghost" type="button" @click="saveUnitPet">
                <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
                <span>Añadir mascota</span>
              </button>
            </div>
          </article>
        </div>
      </section>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar unidad</span>
        </button>
      </div>
    </form>

    <form v-else-if="mode === 'annexForm'" class="entity-form" @submit.prevent="saveUnitAnnex">
      <p v-if="unitAnnexForm.id" class="record-id">ID: {{ unitAnnexForm.id }}</p>
      <div class="entity-form-grid">
        <label>
          Unidad
          <select v-model="unitAnnexForm.unit_id" required>
            <option value="">Selecciona unidad</option>
            <option v-for="unit in unitLookup" :key="unit.id" :value="unit.id">{{ unit.identifier }}</option>
          </select>
        </label>
        <label>
          Tipo
          <select v-model="unitAnnexForm.annex_type">
            <option v-for="[value, label] in annexTypeOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Identificador
          <input v-model="unitAnnexForm.identifier" placeholder="Ej. EST-101" required />
        </label>
        <label>
          Estado
          <select v-model="unitAnnexForm.status">
            <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label class="span-all">
          Descripcion
          <input v-model="unitAnnexForm.description" placeholder="Detalle opcional" />
        </label>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar anexo</span>
        </button>
      </div>
    </form>

    <form v-else-if="mode === 'petForm'" class="entity-form" @submit.prevent="saveUnitPet">
      <p v-if="unitPetForm.id" class="record-id">ID: {{ unitPetForm.id }}</p>
      <div class="entity-form-grid">
        <label>
          Unidad
          <select v-model="unitPetForm.unit_id" required>
            <option value="">Selecciona unidad</option>
            <option v-for="unit in unitLookup" :key="unit.id" :value="unit.id">{{ unit.identifier }}</option>
          </select>
        </label>
        <label>
          Nombre
          <input v-model="unitPetForm.name" placeholder="Ej. Luna" required />
        </label>
        <label>
          Especie
          <select v-model="unitPetForm.species">
            <option v-for="[value, label] in petSpeciesOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Estado
          <select v-model="unitPetForm.status">
            <option v-for="[value, label] in statusOptions" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>
          Raza
          <input v-model="unitPetForm.breed" />
        </label>
        <label>
          Color
          <input v-model="unitPetForm.color" />
        </label>
        <label>
          Chip
          <input v-model="unitPetForm.chip_number" />
        </label>
        <label class="span-all">
          Notas
          <input v-model="unitPetForm.notes" placeholder="Detalle opcional" />
        </label>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
      <div class="form-actions">
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>Guardar mascota</span>
        </button>
      </div>
    </form>
  </section>

  <div v-if="deleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-title">
    <div class="confirm-modal">
      <p class="eyebrow">Confirmacion</p>
      <h2 id="delete-title">Borrar {{ deleteTypeLabel }}</h2>
      <p>Esta acción eliminará {{ deleteCandidate.label }} del condominio activo.</p>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="cancelDelete">Cancelar</button>
        <button class="button danger" type="button" @click="confirmDelete">Borrar</button>
      </div>
    </div>
  </div>
</template>
