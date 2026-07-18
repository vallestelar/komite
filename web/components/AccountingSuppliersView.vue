<script setup lang="ts">
type PageMeta = {
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

type SupplierRecord = {
  id: string;
  company_id?: string | null;
  supplier_category_id?: string | null;
  name: string;
  rut?: string | null;
  email?: string | null;
  phone?: string | null;
  category?: string | null;
  status: string;
  notes?: string | null;
};

type SupplierCategory = {
  id: string;
  name: string;
  code?: string | null;
  status: string;
  display_order: number;
};

type SupplierCondominiumLink = {
  id: string;
  supplier_id: string;
  condominium_id: string;
  status: string;
  notes?: string | null;
};

const { request } = useApi();
const { activeCondominium, company, condominiums } = useAuth();

const suppliers = ref<SupplierRecord[]>([]);
const supplierLinks = ref<SupplierCondominiumLink[]>([]);
const categories = ref<SupplierCategory[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const formError = ref("");
const toastMessage = ref("");
const search = ref("");
const editingSupplierId = ref("");
const deleteCandidate = ref<SupplierRecord | null>(null);

const form = reactive({
  name: "",
  rut: "",
  email: "",
  phone: "",
  supplier_category_id: "",
  status: "active",
  notes: "",
  condominium_ids: [] as string[],
});

const selectedSupplier = computed(() => suppliers.value.find((supplier) => supplier.id === editingSupplierId.value) || null);

const defaultSupplierCategories = [
  { name: "Mantención", code: "maintenance", display_order: 10 },
  { name: "Servicios básicos", code: "utilities", display_order: 20 },
  { name: "Aseo y limpieza", code: "cleaning", display_order: 30 },
  { name: "Seguridad", code: "security", display_order: 40 },
  { name: "Jardinería", code: "gardening", display_order: 50 },
  { name: "Piscina y espacios comunes", code: "common_areas", display_order: 60 },
  { name: "Ascensores", code: "elevators", display_order: 70 },
  { name: "Control de plagas", code: "pest_control", display_order: 80 },
  { name: "Administración", code: "administration", display_order: 90 },
  { name: "Reparaciones y obras", code: "repairs", display_order: 100 },
  { name: "Suministros", code: "supplies", display_order: 110 },
  { name: "Tecnología", code: "technology", display_order: 120 },
  { name: "Seguros", code: "insurance", display_order: 130 },
  { name: "Honorarios profesionales", code: "professional_fees", display_order: 140 },
  { name: "Otros", code: "other", display_order: 999 },
] as const;

const activeCategories = computed(() => [...categories.value]
  .filter((category) => category.status !== "inactive")
  .sort((left, right) => (left.display_order - right.display_order) || left.name.localeCompare(right.name)));

const filteredSuppliers = computed(() => {
  const query = search.value.trim().toLowerCase();
  const linkedIds = new Set(supplierLinks.value.map((link) => link.supplier_id));
  return suppliers.value
    .filter((supplier) => linkedIds.has(supplier.id))
    .filter((supplier) => {
      if (!query) return true;
      return [
        supplier.name,
        supplier.rut,
        supplier.email,
        supplier.phone,
        supplierCategoryLabel(supplier),
        linkedCondominiumNames(supplier.id),
      ].some((value) => String(value || "").toLowerCase().includes(query));
    });
});

const activeLinkedCount = computed(() => supplierLinks.value.filter((link) => link.status !== "inactive").length);

const emptyToNull = (value: string) => {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
};

const normalizedSupplierKey = (value: string | null | undefined) => String(value || "")
  .trim()
  .toLowerCase()
  .replace(/[.\-\s]/g, "");

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

const supplierStatusLabel = (status: string | null | undefined) => {
  if (status === "active") return "Activo";
  if (status === "inactive") return "Inactivo";
  return "Borrador";
};

const supplierStatusClass = (status: string | null | undefined) => {
  if (status === "active") return "active";
  if (status === "inactive") return "blocked";
  return "draft";
};

const supplierCategoryLabel = (supplier: SupplierRecord) => {
  if (supplier.supplier_category_id) {
    return categories.value.find((category) => category.id === supplier.supplier_category_id)?.name || supplier.category || "Sin categoría";
  }
  return supplier.category || "Sin categoría";
};

const supplierLinksFor = (supplierId: string) => supplierLinks.value.filter((link) => link.supplier_id === supplierId);

const linkedCondominiumNames = (supplierId: string) => {
  const ids = new Set(supplierLinksFor(supplierId)
    .filter((link) => link.status !== "inactive")
    .map((link) => link.condominium_id));
  const names = condominiums.value
    .filter((condominium) => ids.has(condominium.id))
    .map((condominium) => condominium.name);
  return names.length ? names.join(", ") : "Sin condominios";
};

const linkedCondominiumSummary = (supplierId: string) => {
  const ids = new Set(supplierLinksFor(supplierId)
    .filter((link) => link.status !== "inactive")
    .map((link) => link.condominium_id));
  if (ids.size === condominiums.value.length && condominiums.value.length > 1) return "Todos los condominios";
  if (ids.size === 1) {
    const id = Array.from(ids)[0];
    return condominiums.value.find((condominium) => condominium.id === id)?.name || "1 condominio";
  }
  return `${ids.size} condominios`;
};

const resetForm = () => {
  editingSupplierId.value = "";
  formError.value = "";
  Object.assign(form, {
    name: "",
    rut: "",
    email: "",
    phone: "",
    supplier_category_id: "",
    status: "active",
    notes: "",
    condominium_ids: activeCondominium.value?.id ? [activeCondominium.value.id] : [],
  });
};

const selectAllCondominiums = () => {
  form.condominium_ids = condominiums.value.map((condominium) => condominium.id);
};

const clearCondominiums = () => {
  form.condominium_ids = [];
};

const ensureDefaultSupplierCategories = async () => {
  if (categories.value.length || !company.value?.id) return;

  await Promise.all(defaultSupplierCategories.map((category) => request<SupplierCategory>("/api/v1/accounting-supplier-categories/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      company_id: company.value?.id || null,
      name: category.name,
      code: category.code,
      status: "active",
      display_order: category.display_order,
      metadata: { default_category: true },
    }),
  }).catch((error) => {
    const message = readableError(error).toLowerCase();
    if (!message.includes("conflicto") && !message.includes("unique") && !message.includes("duplicate")) {
      throw error;
    }
    return null;
  })));

  const categoryPage = await request<{ items?: SupplierCategory[]; meta?: PageMeta }>("/api/v1/accounting-supplier-categories/?page_size=200&order_by=display_order&order_by=name");
  categories.value = categoryPage.items || [];
};

const findExistingSupplier = () => {
  const rutKey = normalizedSupplierKey(form.rut);
  if (rutKey) {
    const byRut = suppliers.value.find((supplier) => normalizedSupplierKey(supplier.rut) === rutKey);
    if (byRut) return byRut;
  }
  const nameKey = normalizedSupplierKey(form.name);
  return suppliers.value.find((supplier) => normalizedSupplierKey(supplier.name) === nameKey) || null;
};

const createOrReactivateLink = async (supplierId: string, condominiumId: string) => {
  const existing = supplierLinks.value.find((link) => link.supplier_id === supplierId && link.condominium_id === condominiumId);
  if (existing) {
    if (existing.status === "inactive") {
      await request<SupplierCondominiumLink>(`/api/v1/accounting-supplier-condominiums/${existing.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "active" }),
      });
    }
    return;
  }

  try {
    await request<SupplierCondominiumLink>("/api/v1/accounting-supplier-condominiums/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_id: company.value?.id || null,
        supplier_id: supplierId,
        condominium_id: condominiumId,
        status: "active",
        notes: null,
        metadata: {},
      }),
    });
  } catch (error) {
    const message = readableError(error).toLowerCase();
    if (!message.includes("conflicto") && !message.includes("unique") && !message.includes("duplicate")) {
      throw error;
    }
  }
};

const reconcileSupplierLinks = async (supplierId: string) => {
  const selectedIds = new Set(form.condominium_ids);
  const currentLinks = supplierLinksFor(supplierId);
  const linksToRemove = currentLinks.filter((link) => !selectedIds.has(link.condominium_id));

  await Promise.all([
    ...form.condominium_ids.map((condominiumId) => createOrReactivateLink(supplierId, condominiumId)),
    ...linksToRemove.map((link) => request(`/api/v1/accounting-supplier-condominiums/${link.id}`, { method: "DELETE" })),
  ]);
};

const loadSuppliers = async () => {
  if (!activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const [supplierPage, supplierLinkPage, categoryPage] = await Promise.all([
      request<{ items?: SupplierRecord[]; meta?: PageMeta }>("/api/v1/accounting-suppliers/?page_size=200&order_by=name"),
      request<{ items?: SupplierCondominiumLink[]; meta?: PageMeta }>("/api/v1/accounting-supplier-condominiums/?page_size=200"),
      request<{ items?: SupplierCategory[]; meta?: PageMeta }>("/api/v1/accounting-supplier-categories/?page_size=200&order_by=display_order&order_by=name"),
    ]);
    suppliers.value = supplierPage.items || [];
    supplierLinks.value = supplierLinkPage.items || [];
    categories.value = categoryPage.items || [];
    await ensureDefaultSupplierCategories();
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const editSupplier = (supplier: SupplierRecord) => {
  formError.value = "";
  editingSupplierId.value = supplier.id;
  Object.assign(form, {
    name: supplier.name || "",
    rut: supplier.rut || "",
    email: supplier.email || "",
    phone: supplier.phone || "",
    supplier_category_id: supplier.supplier_category_id || "",
    status: supplier.status || "active",
    notes: supplier.notes || "",
    condominium_ids: supplierLinksFor(supplier.id)
      .filter((link) => link.status !== "inactive")
      .map((link) => link.condominium_id),
  });
};

const saveSupplier = async () => {
  formError.value = "";
  errorMessage.value = "";
  if (!form.name.trim()) {
    formError.value = "Indica el nombre del proveedor.";
    return;
  }
  if (!form.condominium_ids.length) {
    formError.value = "Selecciona al menos un condominio.";
    return;
  }

  try {
    const wasEditing = Boolean(editingSupplierId.value);
    const supplierPayload = {
      company_id: company.value?.id || null,
      condominium_id: null,
      name: form.name.trim(),
      rut: emptyToNull(form.rut),
      email: emptyToNull(form.email),
      phone: emptyToNull(form.phone),
      supplier_category_id: emptyToNull(form.supplier_category_id),
      category: form.supplier_category_id
        ? categories.value.find((category) => category.id === form.supplier_category_id)?.name || null
        : null,
      status: form.status,
      notes: emptyToNull(form.notes),
      metadata: {},
    };

    let supplier: SupplierRecord;
    if (editingSupplierId.value) {
      supplier = await request<SupplierRecord>(`/api/v1/accounting-suppliers/${editingSupplierId.value}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(supplierPayload),
      });
    } else {
      const existingSupplier = findExistingSupplier();
      if (existingSupplier) {
        supplier = await request<SupplierRecord>(`/api/v1/accounting-suppliers/${existingSupplier.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(supplierPayload),
        });
      } else {
        supplier = await request<SupplierRecord>("/api/v1/accounting-suppliers/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(supplierPayload),
        });
      }
    }

    await reconcileSupplierLinks(supplier.id);
    resetForm();
    showToast(wasEditing ? "Proveedor actualizado." : "Proveedor guardado.");
    await loadSuppliers();
  } catch (error) {
    formError.value = readableError(error);
  }
};

const askDeleteSupplier = (supplier: SupplierRecord) => {
  deleteCandidate.value = supplier;
};

const cancelDelete = () => {
  deleteCandidate.value = null;
};

const confirmDelete = async () => {
  if (!deleteCandidate.value) return;
  errorMessage.value = "";
  try {
    const deletedId = deleteCandidate.value.id;
    await request(`/api/v1/accounting-suppliers/${deletedId}`, { method: "DELETE" });
    deleteCandidate.value = null;
    if (editingSupplierId.value === deletedId) resetForm();
    showToast("Proveedor eliminado.");
    await loadSuppliers();
  } catch (error) {
    errorMessage.value = readableError(error);
    deleteCandidate.value = null;
  }
};

watch(() => activeCondominium.value?.id, () => {
  resetForm();
  loadSuppliers();
}, { immediate: true });
</script>

<template>
  <section class="panel suppliers-panel">
    <div class="dashboard-hero suppliers-hero">
      <div>
        <p class="eyebrow">Contabilidad</p>
        <h2>Proveedores</h2>
        <p class="hero-copy">Gestiona fichas maestras y define en qué condominios están disponibles.</p>
      </div>
      <div class="committee-summary">
        <article>
          <span>Proveedores</span>
          <strong>{{ filteredSuppliers.length }}</strong>
        </article>
        <article>
          <span>Vínculos</span>
          <strong>{{ activeLinkedCount }}</strong>
        </article>
        <article>
          <span>Condominios</span>
          <strong>{{ condominiums.length }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
    <p v-if="toastMessage" class="success-message">{{ toastMessage }}</p>

    <div class="suppliers-layout">
      <section class="supplier-list-card">
        <div class="section-header">
          <div>
            <h2>Listado</h2>
            <p class="placeholder-copy">Proveedores vinculados a uno o más condominios.</p>
          </div>
          <button class="button orange" type="button" @click="resetForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
            <span>Nuevo proveedor</span>
          </button>
        </div>

        <label class="search-field">
          <span>Buscar</span>
          <input v-model="search" placeholder="Buscar proveedor, RUT, contacto o condominio" />
        </label>

        <div class="edifito-table-wrap entity-table-wrap">
          <table class="edifito-table entity-table">
            <thead>
              <tr>
                <th>Proveedor</th>
                <th>RUT</th>
                <th>Contacto</th>
                <th>Categoría</th>
                <th>Condominios</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="supplier in filteredSuppliers" :key="supplier.id">
                <td>
                  <strong>{{ supplier.name }}</strong>
                  <small v-if="supplier.notes" class="muted-table-note">{{ supplier.notes }}</small>
                </td>
                <td>{{ supplier.rut || "Sin RUT" }}</td>
                <td>
                  <span>{{ supplier.email || "Sin email" }}</span>
                  <small v-if="supplier.phone" class="muted-table-note">{{ supplier.phone }}</small>
                </td>
                <td>{{ supplierCategoryLabel(supplier) }}</td>
                <td>
                  <span class="condominium-summary" :title="linkedCondominiumNames(supplier.id)">
                    {{ linkedCondominiumSummary(supplier.id) }}
                  </span>
                </td>
                <td>
                  <span class="period-status-chip" :class="supplierStatusClass(supplier.status)">
                    <span aria-hidden="true"></span>
                    {{ supplierStatusLabel(supplier.status) }}
                  </span>
                </td>
                <td class="actions-cell">
                  <button class="button compact icon-action navy" type="button" aria-label="Editar proveedor" title="Editar proveedor" @click="editSupplier(supplier)">
                    <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                  </button>
                  <button class="button compact icon-action danger" type="button" aria-label="Borrar proveedor" title="Borrar proveedor" @click="askDeleteSupplier(supplier)">
                    <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                  </button>
                </td>
              </tr>
              <tr v-if="!filteredSuppliers.length && !loading">
                <td class="empty-row" colspan="7">Sin proveedores registrados.</td>
              </tr>
              <tr v-if="loading">
                <td class="empty-row" colspan="7">Cargando proveedores...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <form class="entity-form supplier-form" @submit.prevent="saveSupplier">
        <div class="form-title-row">
          <div>
            <p class="eyebrow">Proveedor</p>
            <h2>{{ selectedSupplier ? "Editar proveedor" : "Nuevo proveedor" }}</h2>
          </div>
          <span v-if="selectedSupplier" class="id-pill">ID: {{ selectedSupplier.id }}</span>
        </div>

        <p v-if="formError" class="form-error">{{ formError }}</p>

        <div class="entity-form-grid">
          <label>
            Nombre
            <input v-model="form.name" required maxlength="180" placeholder="Ej. Ascensores del Pacífico" />
          </label>
          <label>
            RUT
            <input v-model="form.rut" maxlength="30" placeholder="76.123.456-7" />
          </label>
          <label>
            Email
            <input v-model="form.email" type="email" maxlength="255" placeholder="contacto@proveedor.cl" />
          </label>
          <label>
            Teléfono
            <input v-model="form.phone" maxlength="40" placeholder="+56 9..." />
          </label>
          <label>
            Categoría
            <select v-model="form.supplier_category_id">
              <option value="">Sin categoría</option>
              <option v-for="category in activeCategories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </label>
          <label>
            Estado
            <select v-model="form.status">
              <option value="active">Activo</option>
              <option value="inactive">Inactivo</option>
              <option value="draft">Borrador</option>
            </select>
          </label>
          <label class="span-all">
            Notas
            <textarea v-model="form.notes" rows="3" placeholder="Condiciones, contacto comercial, cobertura o referencia útil." />
          </label>
        </div>

        <section class="condominium-selector">
          <div class="selector-header">
            <div>
              <h3>Condominios asociados</h3>
              <p>Marca solo los condominios donde este proveedor debe estar disponible.</p>
            </div>
            <div class="selector-actions">
              <button class="button ghost compact" type="button" @click="selectAllCondominiums">Todos</button>
              <button class="button ghost compact" type="button" @click="clearCondominiums">Limpiar</button>
            </div>
          </div>

          <div class="condominium-grid">
            <label v-for="condominium in condominiums" :key="condominium.id" class="switch-field condominium-switch">
              <input v-model="form.condominium_ids" type="checkbox" :value="condominium.id" />
              <span class="switch-slider" aria-hidden="true"></span>
              <span>{{ condominium.name }}</span>
            </label>
          </div>
        </section>

        <div class="form-actions">
          <button v-if="editingSupplierId" class="button ghost" type="button" @click="resetForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
            <span>Cancelar</span>
          </button>
          <button class="button navy" type="submit">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ editingSupplierId ? "Actualizar proveedor" : "Guardar proveedor" }}</span>
          </button>
        </div>
      </form>
    </div>

    <div v-if="deleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-supplier-title">
      <div class="confirm-modal">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Borrar proveedor</p>
            <h2 id="delete-supplier-title">{{ deleteCandidate.name }}</h2>
          </div>
          <button class="button ghost compact icon-action" type="button" aria-label="Cerrar" title="Cerrar" @click="cancelDelete">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>
        <p>Esta acción eliminará la ficha maestra del proveedor. Si ya tiene egresos asociados, el sistema no permitirá borrarlo.</p>
        <div class="form-actions">
          <button class="button ghost" type="button" @click="cancelDelete">Cancelar</button>
          <button class="button danger" type="button" @click="confirmDelete">
            <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
            <span>Borrar proveedor</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.suppliers-panel {
  display: grid;
  gap: 18px;
}

.suppliers-hero {
  align-items: center;
}

.suppliers-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.65fr);
  gap: 18px;
  align-items: start;
}

.supplier-list-card,
.supplier-form {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--white);
}

.supplier-list-card {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.section-header,
.form-title-row,
.selector-header,
.modal-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.search-field {
  display: grid;
  gap: 7px;
}

.search-field input,
.entity-form input,
.entity-form select,
.entity-form textarea {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 9px 11px;
  color: var(--text);
  background: var(--white);
  font: inherit;
}

.entity-form textarea {
  resize: vertical;
}

.entity-form {
  display: grid;
  gap: 16px;
  padding: 16px;
  background: #fbfcfe;
}

.entity-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.span-all {
  grid-column: 1 / -1;
}

.id-pill,
.condominium-summary {
  display: inline-flex;
  width: fit-content;
  max-width: 260px;
  min-height: 26px;
  align-items: center;
  border-radius: 999px;
  padding: 4px 9px;
  color: #475467;
  background: #f2f4f7;
  font-size: 12px;
}

.condominium-summary {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.muted-table-note {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 400;
}

.period-status-chip {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  gap: 7px;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 400;
}

.period-status-chip > span {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.period-status-chip.active {
  color: #067647;
  background: #ecfdf3;
}

.period-status-chip.draft {
  color: #475467;
  background: #f2f4f7;
}

.period-status-chip.blocked {
  color: #b42318;
  background: #fef3f2;
}

.condominium-selector {
  display: grid;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
  background: var(--white);
}

.selector-header h3 {
  margin: 0 0 4px;
  font-size: 16px;
}

.selector-header p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.selector-actions,
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.condominium-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.condominium-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 9px 10px;
  background: #fbfcfe;
  cursor: pointer;
  user-select: none;
}

.switch-field input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.switch-field input:checked + .switch-slider {
  background: var(--orange);
  box-shadow: inset 0 0 0 1px rgba(247, 148, 29, 0.2), 0 0 0 3px rgba(247, 148, 29, 0.12);
}

.switch-field input:checked + .switch-slider::before {
  transform: translateX(18px);
}

.switch-field input:focus-visible + .switch-slider {
  outline: 2px solid rgba(247, 148, 29, 0.45);
  outline-offset: 2px;
}

.success-message {
  margin: 0;
  color: #067647;
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 1200px) {
  .suppliers-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .entity-form-grid,
  .condominium-grid {
    grid-template-columns: 1fr;
  }

  .section-header,
  .selector-header {
    flex-direction: column;
  }
}
</style>
