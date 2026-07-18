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

type IncomeRecord = {
  id: string;
  period_id: string;
  unit_id?: string | null;
  income_type_id?: string | null;
  bank_id?: string | null;
  income_date: string;
  description: string;
  amount: number | string;
  status: string;
};

type ExpenseRecord = {
  id: string;
  period_id: string;
  supplier_id?: string | null;
  expense_date: string;
  description: string;
  amount: number | string;
  category?: string | null;
  is_common_expense: boolean;
  status: string;
};

type SimpleRecord = {
  id: string;
  name?: string;
  identifier?: string;
  code?: string | null;
};

type SupplierRecord = SimpleRecord & {
  condominium_id?: string | null;
  rut?: string | null;
  email?: string | null;
  phone?: string | null;
  category?: string | null;
  status: string;
  notes?: string | null;
};

type SupplierCondominiumLink = {
  id: string;
  supplier_id: string;
  condominium_id: string;
  status: string;
  notes?: string | null;
};

type AccountingSummary = {
  totals: {
    income: number;
    expense: number;
    common_expense: number;
    balance: number;
  };
  latest_run?: {
    id: string;
    status: string;
    total_expenses: number;
    total_reserve_fund: number;
    total_charged: number;
    charge_count: number;
    calculated_at?: string | null;
  } | null;
};

type ChargeRow = {
  id: string;
  unit_identifier: string;
  proration: number;
  expense_amount: number;
  reserve_fund_amount: number;
  total_amount: number;
};

const { request } = useApi();
const { activeCondominium, company, condominiums } = useAuth();

const tabs = [
  ["incomes", "Ingresos"],
  ["expenses", "Egresos"],
  ["common", "Gastos comunes"],
] as const;

const defaultIncomeTypes = [
  { name: "Pago gasto común", code: "common_expense_payment" },
  { name: "Abono gasto común", code: "common_expense_credit" },
  { name: "Fondo de reserva", code: "reserve_fund" },
  { name: "Multa", code: "fine" },
  { name: "Interés por mora", code: "late_fee_interest" },
  { name: "Arriendo espacio común", code: "common_area_rent" },
  { name: "Reembolso", code: "refund" },
  { name: "Regularización", code: "adjustment" },
  { name: "Otro ingreso", code: "other_income" },
] as const;

const activeTab = ref<(typeof tabs)[number][0]>("incomes");
const loading = ref(false);
const errorMessage = ref("");
const toastMessage = ref("");
const selectedPeriodId = ref("");
const periods = ref<PeriodRecord[]>([]);
const incomes = ref<IncomeRecord[]>([]);
const expenses = ref<ExpenseRecord[]>([]);
const suppliers = ref<SupplierRecord[]>([]);
const supplierLinks = ref<SupplierCondominiumLink[]>([]);
const incomeTypes = ref<SimpleRecord[]>([]);
const banks = ref<SimpleRecord[]>([]);
const units = ref<SimpleRecord[]>([]);
const summary = ref<AccountingSummary | null>(null);
const charges = ref<ChargeRow[]>([]);
const editingPeriodId = ref("");
const periodDeleteCandidate = ref<PeriodRecord | null>(null);
const incomeModalOpen = ref(false);
const expenseModalOpen = ref(false);
const supplierModalOpen = ref(false);
const editingIncomeId = ref("");
const editingExpenseId = ref("");
const editingSupplierId = ref("");
const deleteCandidate = ref<{ type: "income" | "expense"; id: string; label: string } | null>(null);
const supplierDeleteCandidate = ref<SupplierRecord | null>(null);
const unitSearch = ref("");
const unitSearchLoading = ref(false);
let unitSearchTimer: ReturnType<typeof setTimeout> | null = null;

const periodForm = reactive({
  name: "",
  start_date: "",
  end_date: "",
  reserve_fund_rate: "0.05",
  is_active: false,
});

const incomeForm = reactive({
  income_date: "",
  description: "",
  amount: "",
  unit_id: "",
  income_type_id: "",
  bank_id: "",
});

const expenseForm = reactive({
  expense_date: "",
  description: "",
  amount: "",
  supplier_id: "",
  category: "",
  is_common_expense: true,
});

const supplierForm = reactive({
  name: "",
  rut: "",
  email: "",
  phone: "",
  category: "",
  status: "active",
  notes: "",
  duplicate_all_condominiums: false,
});

const selectedPeriod = computed(() => periods.value.find((period) => period.id === selectedPeriodId.value) || null);
const periodOptions = computed(() => periods.value.map((period) => [period.id, period.name]));
const filteredIncomes = computed(() => incomes.value.filter((income) => income.period_id === selectedPeriodId.value));
const filteredExpenses = computed(() => expenses.value.filter((expense) => expense.period_id === selectedPeriodId.value));
const activeSupplierIds = computed(() => new Set(supplierLinks.value
  .filter((link) => link.condominium_id === activeCondominium.value?.id && link.status !== "inactive")
  .map((link) => link.supplier_id)));
const filteredSuppliers = computed(() => suppliers.value.filter((supplier) => activeSupplierIds.value.has(supplier.id)));
const unitLabel = (unit: SimpleRecord) => unit.identifier || unit.name || "Sin identificador";
const selectedIncomeUnit = computed(() => units.value.find((unit) => unit.id === incomeForm.unit_id) || null);
const filteredUnitOptions = computed(() => {
  const query = unitSearch.value.trim().toLowerCase();
  const matches = query
    ? units.value.filter((unit) => unitLabel(unit).toLowerCase().includes(query))
    : units.value;
  return matches.slice(0, 30);
});

const formatCLP = (value: number | string | null | undefined) => {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);
};

const formatDate = (value: string | null | undefined) => {
  if (!value) return "";
  const [datePart] = value.split("T");
  const parts = datePart.split("-");
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : value;
};

const emptyToNull = (value: string) => {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
};

const normalizedSupplierKey = (value: string | null | undefined) => String(value || "")
  .trim()
  .toLowerCase()
  .replace(/[.\-\s]/g, "");

const numericValue = (value: string) => Number(value.replace(",", ".") || 0);

const periodStatusLabel = (period: PeriodRecord) => {
  if (period.is_active) return "Activo";
  if (period.status === "closed") return "Cerrado";
  if (period.status === "blocked") return "Bloqueado";
  if (period.status === "open") return "Abierto";
  return "Borrador";
};

const periodStatusClass = (period: PeriodRecord) => {
  if (period.is_active) return "active";
  if (period.status === "closed") return "closed";
  if (period.status === "blocked") return "blocked";
  if (period.status === "open") return "open";
  return "draft";
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

const reservePercent = (value: number | string | null | undefined) => `${(Number(value || 0) * 100).toLocaleString("es-CL", { maximumFractionDigits: 2 })}%`;

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

const mergeUnits = (nextUnits: SimpleRecord[]) => {
  const byId = new Map(units.value.map((unit) => [unit.id, unit]));
  for (const unit of nextUnits) byId.set(unit.id, unit);
  units.value = [...byId.values()].sort((left, right) => unitLabel(left).localeCompare(unitLabel(right), "es"));
};

const searchUnits = async (query: string) => {
  if (!activeCondominium.value?.id) return;
  unitSearchLoading.value = true;
  try {
    const q = query.trim() ? `&q=${encodeURIComponent(query.trim())}` : "";
    const unitPage = await request<{ items?: SimpleRecord[]; meta?: PageMeta }>(`/api/v1/units/?page_size=50&order_by=identifier${q}`);
    mergeUnits(unitPage.items || []);
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    unitSearchLoading.value = false;
  }
};

const selectIncomeUnit = (unit: SimpleRecord | null) => {
  incomeForm.unit_id = unit?.id || "";
  unitSearch.value = unit ? unitLabel(unit) : "";
};

const ensureDefaultIncomeTypes = async () => {
  if (!activeCondominium.value?.id) return;
  const existingKeys = new Set(
    incomeTypes.value.flatMap((type) => [type.code, type.name?.trim().toLowerCase()].filter(Boolean) as string[]),
  );
  const missingTypes = defaultIncomeTypes.filter((type) => !existingKeys.has(type.code) && !existingKeys.has(type.name.toLowerCase()));
  if (!missingTypes.length) return;

  await Promise.all(missingTypes.map((type) => request<SimpleRecord>("/api/v1/accounting-income-types/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      condominium_id: activeCondominium.value?.id,
      name: type.name,
      code: type.code,
      status: "active",
      metadata: { system_default: true },
    }),
  })));

  const typePage = await request<{ items?: SimpleRecord[]; meta?: PageMeta }>("/api/v1/accounting-income-types/?page_size=100&order_by=name");
  incomeTypes.value = typePage.items || [];
};

const resetPeriodForm = () => {
  editingPeriodId.value = "";
  Object.assign(periodForm, { name: "", start_date: "", end_date: "", reserve_fund_rate: "0.05", is_active: false });
};

const resetIncomeForm = () => {
  editingIncomeId.value = "";
  unitSearch.value = "";
  Object.assign(incomeForm, { income_date: "", description: "", amount: "", unit_id: "", income_type_id: "", bank_id: "" });
};

const resetExpenseForm = () => {
  editingExpenseId.value = "";
  Object.assign(expenseForm, { expense_date: "", description: "", amount: "", supplier_id: "", category: "", is_common_expense: true });
};

const resetSupplierForm = () => {
  editingSupplierId.value = "";
  Object.assign(supplierForm, { name: "", rut: "", email: "", phone: "", category: "", status: "active", notes: "", duplicate_all_condominiums: false });
};

const openCreateIncome = () => {
  resetIncomeForm();
  incomeModalOpen.value = true;
};

const openEditIncome = (income: IncomeRecord) => {
  editingIncomeId.value = income.id;
  Object.assign(incomeForm, {
    income_date: income.income_date,
    description: income.description,
    amount: String(income.amount ?? ""),
    unit_id: income.unit_id || "",
    income_type_id: income.income_type_id || "",
    bank_id: income.bank_id || "",
  });
  unitSearch.value = selectedIncomeUnit.value ? unitLabel(selectedIncomeUnit.value) : "";
  incomeModalOpen.value = true;
};

const closeIncomeModal = () => {
  incomeModalOpen.value = false;
  resetIncomeForm();
};

const openCreateExpense = () => {
  resetExpenseForm();
  expenseModalOpen.value = true;
};

const openEditExpense = (expense: ExpenseRecord) => {
  editingExpenseId.value = expense.id;
  Object.assign(expenseForm, {
    expense_date: expense.expense_date,
    description: expense.description,
    amount: String(expense.amount ?? ""),
    supplier_id: expense.supplier_id || "",
    category: expense.category || "",
    is_common_expense: expense.is_common_expense,
  });
  expenseModalOpen.value = true;
};

const closeExpenseModal = () => {
  expenseModalOpen.value = false;
  resetExpenseForm();
};

const openCreateSupplier = () => {
  resetSupplierForm();
  supplierModalOpen.value = true;
};

const openEditSupplier = (supplier: SupplierRecord) => {
  editingSupplierId.value = supplier.id;
  Object.assign(supplierForm, {
    name: supplier.name || "",
    rut: supplier.rut || "",
    email: supplier.email || "",
    phone: supplier.phone || "",
    category: supplier.category || "",
    status: supplier.status || "active",
    notes: supplier.notes || "",
    duplicate_all_condominiums: false,
  });
  supplierModalOpen.value = true;
};

const closeSupplierModal = () => {
  supplierModalOpen.value = false;
  resetSupplierForm();
};

const findExistingSupplier = () => {
  const rutKey = normalizedSupplierKey(supplierForm.rut);
  if (rutKey) {
    const byRut = suppliers.value.find((supplier) => normalizedSupplierKey(supplier.rut) === rutKey);
    if (byRut) return byRut;
  }

  const nameKey = normalizedSupplierKey(supplierForm.name);
  return suppliers.value.find((supplier) => normalizedSupplierKey(supplier.name) === nameKey) || null;
};

const createSupplierLink = async (supplierId: string, condominiumId: string) => {
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

const loadPage = async () => {
  if (!activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const [periodPage, incomePage, expensePage, supplierPage, supplierLinkPage, typePage, bankPage, unitPage] = await Promise.all([
      request<{ items?: PeriodRecord[]; meta?: PageMeta }>("/api/v1/accounting-periods/?page_size=100&order_by=-start_date"),
      request<{ items?: IncomeRecord[]; meta?: PageMeta }>("/api/v1/accounting-incomes/?page_size=200&order_by=-income_date"),
      request<{ items?: ExpenseRecord[]; meta?: PageMeta }>("/api/v1/accounting-expenses/?page_size=200&order_by=-expense_date"),
      request<{ items?: SupplierRecord[]; meta?: PageMeta }>("/api/v1/accounting-suppliers/?page_size=200&order_by=name"),
      request<{ items?: SupplierCondominiumLink[]; meta?: PageMeta }>("/api/v1/accounting-supplier-condominiums/?page_size=200"),
      request<{ items?: SimpleRecord[]; meta?: PageMeta }>("/api/v1/accounting-income-types/?page_size=100&order_by=name"),
      request<{ items?: SimpleRecord[]; meta?: PageMeta }>("/api/v1/banks/?page_size=200&order_by=name"),
      request<{ items?: SimpleRecord[]; meta?: PageMeta }>("/api/v1/units/?page_size=200&order_by=identifier"),
    ]);

    periods.value = periodPage.items || [];
    incomes.value = incomePage.items || [];
    expenses.value = expensePage.items || [];
    suppliers.value = supplierPage.items || [];
    supplierLinks.value = supplierLinkPage.items || [];
    incomeTypes.value = typePage.items || [];
    banks.value = bankPage.items || [];
    units.value = unitPage.items || [];
    await ensureDefaultIncomeTypes();

    if (!selectedPeriodId.value && periods.value.length) {
      selectedPeriodId.value = periods.value.find((period) => period.is_active)?.id || periods.value[0].id;
    }
    await loadSummary();
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const loadSummary = async () => {
  if (!selectedPeriodId.value) {
    summary.value = null;
    charges.value = [];
    return;
  }
  summary.value = await request<AccountingSummary>(`/api/v1/portal/accounting/summary?period_id=${selectedPeriodId.value}`);
  await loadLatestCharges();
};

const loadLatestCharges = async () => {
  if (!selectedPeriodId.value || !summary.value?.latest_run) {
    charges.value = [];
    return;
  }
  const result = await request<{ charges: ChargeRow[] }>(`/api/v1/portal/accounting/common-expense-runs/latest-charges?period_id=${selectedPeriodId.value}`);
  charges.value = result.charges || [];
};

const editPeriod = (period: PeriodRecord) => {
  editingPeriodId.value = period.id;
  Object.assign(periodForm, {
    name: period.name,
    start_date: period.start_date,
    end_date: period.end_date,
    reserve_fund_rate: String(period.reserve_fund_rate ?? "0"),
    is_active: period.is_active,
  });
};

const askDeletePeriod = (period: PeriodRecord) => {
  periodDeleteCandidate.value = period;
};

const cancelDeletePeriod = () => {
  periodDeleteCandidate.value = null;
};

const confirmDeletePeriod = async () => {
  if (!periodDeleteCandidate.value) return;
  errorMessage.value = "";
  try {
    const deletingSelected = selectedPeriodId.value === periodDeleteCandidate.value.id;
    await request(`/api/v1/accounting-periods/${periodDeleteCandidate.value.id}`, { method: "DELETE" });
    periodDeleteCandidate.value = null;
    if (deletingSelected) selectedPeriodId.value = "";
    resetPeriodForm();
    showToast("Periodo eliminado correctamente.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
    periodDeleteCandidate.value = null;
  }
};

const savePeriod = async () => {
  if (!activeCondominium.value?.id) return;
  errorMessage.value = "";
  try {
    const wasEditing = Boolean(editingPeriodId.value);
    const path = editingPeriodId.value ? `/api/v1/accounting-periods/${editingPeriodId.value}` : "/api/v1/accounting-periods/";
    await request<PeriodRecord>(path, {
      method: editingPeriodId.value ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        condominium_id: activeCondominium.value.id,
        name: periodForm.name.trim(),
        start_date: periodForm.start_date,
        end_date: periodForm.end_date,
        reserve_fund_rate: numericValue(periodForm.reserve_fund_rate),
        is_active: periodForm.is_active,
        status: periodForm.is_active ? "open" : "draft",
        metadata: {},
      }),
    });
    resetPeriodForm();
    showToast(wasEditing ? "Periodo actualizado correctamente." : "Periodo guardado correctamente.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const saveIncome = async () => {
  if (!activeCondominium.value?.id || !selectedPeriodId.value) return;
  errorMessage.value = "";
  try {
    const wasEditing = Boolean(editingIncomeId.value);
    const path = editingIncomeId.value ? `/api/v1/accounting-incomes/${editingIncomeId.value}` : "/api/v1/accounting-incomes/";
    await request<IncomeRecord>(path, {
      method: editingIncomeId.value ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        condominium_id: activeCondominium.value.id,
        period_id: selectedPeriodId.value,
        income_date: incomeForm.income_date,
        description: incomeForm.description.trim(),
        amount: numericValue(incomeForm.amount),
        unit_id: emptyToNull(incomeForm.unit_id),
        income_type_id: emptyToNull(incomeForm.income_type_id),
        bank_id: emptyToNull(incomeForm.bank_id),
        status: "confirmed",
        metadata: {},
      }),
    });
    closeIncomeModal();
    showToast(wasEditing ? "Ingreso actualizado." : "Ingreso registrado.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const saveExpense = async () => {
  if (!activeCondominium.value?.id || !selectedPeriodId.value) return;
  errorMessage.value = "";
  try {
    const wasEditing = Boolean(editingExpenseId.value);
    const path = editingExpenseId.value ? `/api/v1/accounting-expenses/${editingExpenseId.value}` : "/api/v1/accounting-expenses/";
    await request<ExpenseRecord>(path, {
      method: editingExpenseId.value ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        condominium_id: activeCondominium.value.id,
        period_id: selectedPeriodId.value,
        expense_date: expenseForm.expense_date,
        description: expenseForm.description.trim(),
        amount: numericValue(expenseForm.amount),
        supplier_id: emptyToNull(expenseForm.supplier_id),
        category: emptyToNull(expenseForm.category),
        is_common_expense: expenseForm.is_common_expense,
        status: "approved",
        metadata: {},
      }),
    });
    closeExpenseModal();
    showToast(wasEditing ? "Egreso actualizado." : "Egreso registrado.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const saveSupplier = async () => {
  const currentCondominium = activeCondominium.value;
  if (!currentCondominium?.id) return;
  errorMessage.value = "";
  try {
    const wasEditing = Boolean(editingSupplierId.value);
    const supplierPayload = {
      company_id: company.value?.id || null,
      name: supplierForm.name.trim(),
      rut: emptyToNull(supplierForm.rut),
      email: emptyToNull(supplierForm.email),
      phone: emptyToNull(supplierForm.phone),
      category: emptyToNull(supplierForm.category),
      status: supplierForm.status,
      notes: emptyToNull(supplierForm.notes),
      metadata: {},
    };

    if (editingSupplierId.value) {
      await request<SupplierRecord>(`/api/v1/accounting-suppliers/${editingSupplierId.value}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...supplierPayload,
          condominium_id: null,
        }),
      });
    } else {
      const existingSupplier = findExistingSupplier();
      const supplier = existingSupplier || await request<SupplierRecord>("/api/v1/accounting-suppliers/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...supplierPayload,
          condominium_id: null,
        }),
      });
      const targetCondominiums = supplierForm.duplicate_all_condominiums
        ? condominiums.value
        : [currentCondominium];

      await Promise.all(targetCondominiums.map((condominium) => createSupplierLink(supplier.id, condominium.id)));
    }

    const duplicatedInAll = !wasEditing && supplierForm.duplicate_all_condominiums;
    const createdCount = duplicatedInAll ? condominiums.value.length : 1;
    closeSupplierModal();
    showToast(wasEditing
      ? "Proveedor actualizado."
      : duplicatedInAll
        ? `Proveedor creado en ${createdCount} condominios.`
        : "Proveedor registrado.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const askDeleteIncome = (income: IncomeRecord) => {
  deleteCandidate.value = { type: "income", id: income.id, label: income.description };
};

const askDeleteExpense = (expense: ExpenseRecord) => {
  deleteCandidate.value = { type: "expense", id: expense.id, label: expense.description };
};

const cancelDeleteRecord = () => {
  deleteCandidate.value = null;
};

const askDeleteSupplier = (supplier: SupplierRecord) => {
  supplierDeleteCandidate.value = supplier;
};

const cancelDeleteSupplier = () => {
  supplierDeleteCandidate.value = null;
};

const confirmDeleteSupplier = async () => {
  if (!supplierDeleteCandidate.value) return;
  errorMessage.value = "";
  try {
    const link = supplierLinks.value.find((item) =>
      item.supplier_id === supplierDeleteCandidate.value?.id
      && item.condominium_id === activeCondominium.value?.id,
    );
    if (link) {
      await request(`/api/v1/accounting-supplier-condominiums/${link.id}`, { method: "DELETE" });
    }
    supplierDeleteCandidate.value = null;
    showToast("Proveedor quitado de este condominio.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
    supplierDeleteCandidate.value = null;
  }
};

const confirmDeleteRecord = async () => {
  if (!deleteCandidate.value) return;
  errorMessage.value = "";
  try {
    const candidate = deleteCandidate.value;
    const path = candidate.type === "income" ? `/api/v1/accounting-incomes/${candidate.id}` : `/api/v1/accounting-expenses/${candidate.id}`;
    await request(path, { method: "DELETE" });
    deleteCandidate.value = null;
    showToast(candidate.type === "income" ? "Ingreso eliminado." : "Egreso eliminado.");
    await loadPage();
  } catch (error) {
    errorMessage.value = readableError(error);
    deleteCandidate.value = null;
  }
};

const calculateCommonExpenses = async () => {
  if (!selectedPeriodId.value) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const result = await request<{ charges: ChargeRow[] }>(`/api/v1/portal/accounting/common-expense-runs/calculate?period_id=${selectedPeriodId.value}`, {
      method: "POST",
    });
    charges.value = result.charges || [];
    showToast("Gastos comunes calculados.");
    await loadSummary();
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

watch(selectedPeriodId, async () => {
  charges.value = [];
  if (selectedPeriodId.value) await loadSummary();
});

watch(unitSearch, (value) => {
  if (!incomeModalOpen.value) return;
  if (selectedIncomeUnit.value && value.trim() !== unitLabel(selectedIncomeUnit.value)) {
    incomeForm.unit_id = "";
  }
  if (unitSearchTimer) clearTimeout(unitSearchTimer);
  unitSearchTimer = setTimeout(() => {
    void searchUnits(value);
  }, 250);
});

watch(() => activeCondominium.value?.id, async () => {
  selectedPeriodId.value = "";
  charges.value = [];
  await loadPage();
});

onMounted(loadPage);
</script>

<template>
  <section class="panel accounting-panel">
    <div class="accounting-header">
      <div>
        <p class="eyebrow">Contabilidad</p>
        <h2>Módulo contable</h2>
        <p class="placeholder-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="period-picker">
        <label>
          Periodo
          <select v-model="selectedPeriodId" :disabled="!periods.length">
            <option value="">Sin periodo</option>
            <option v-for="[id, name] in periodOptions" :key="id" :value="id">{{ name }}</option>
          </select>
        </label>
      </div>
    </div>

    <div class="metrics-grid">
      <div class="metric">
        <span>Ingresos</span>
        <strong>{{ formatCLP(summary?.totals.income) }}</strong>
      </div>
      <div class="metric">
        <span>Egresos</span>
        <strong>{{ formatCLP(summary?.totals.expense) }}</strong>
      </div>
      <div class="metric">
        <span>Gasto común base</span>
        <strong>{{ formatCLP(summary?.totals.common_expense) }}</strong>
      </div>
      <div class="metric">
        <span>Saldo</span>
        <strong>{{ formatCLP(summary?.totals.balance) }}</strong>
      </div>
    </div>

    <div class="entity-tabs accounting-tabs" role="tablist" aria-label="Contabilidad">
      <button
        v-for="[id, label] in tabs"
        :key="id"
        class="button compact"
        :class="activeTab === id ? 'navy' : 'ghost'"
        type="button"
        @click="activeTab = id"
      >
        <span>{{ label }}</span>
      </button>
      <button class="button ghost compact" type="button" :disabled="loading" @click="loadPage">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
    <p v-if="toastMessage" class="success-message">{{ toastMessage }}</p>

    <div v-if="activeTab === 'periods'" class="accounting-grid">
      <form class="entity-form" @submit.prevent="savePeriod">
        <h2>{{ editingPeriodId ? "Editar periodo" : "Nuevo periodo" }}</h2>
        <div class="entity-form-grid">
          <label>
            Nombre
            <input v-model="periodForm.name" required maxlength="120" placeholder="Julio 2026" />
          </label>
          <label>
            Inicio
            <input v-model="periodForm.start_date" required type="date" />
          </label>
          <label>
            Fin
            <input v-model="periodForm.end_date" required type="date" />
          </label>
          <label>
            Fondo reserva
            <input v-model="periodForm.reserve_fund_rate" required inputmode="decimal" placeholder="0.05" />
          </label>
          <label class="switch-field">
            <input v-model="periodForm.is_active" type="checkbox" />
            <span class="switch-slider" aria-hidden="true"></span>
            <span>Periodo activo</span>
          </label>
        </div>
        <div class="form-actions">
          <button v-if="editingPeriodId" class="button ghost" type="button" @click="resetPeriodForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
            <span>Cancelar</span>
          </button>
          <button class="button navy" type="submit">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ editingPeriodId ? "Actualizar periodo" : "Guardar periodo" }}</span>
          </button>
        </div>
      </form>

      <div class="edifito-table-wrap entity-table-wrap">
        <table class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th>Rango</th>
              <th>Estado</th>
              <th>Acciones</th>
              <th>Fondo reserva</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="period in periods" :key="period.id">
              <td><strong>{{ period.name }}</strong></td>
              <td>{{ formatDate(period.start_date) }} - {{ formatDate(period.end_date) }}</td>
              <td>
                <span class="period-status-chip" :class="periodStatusClass(period)">
                  <span aria-hidden="true"></span>
                  {{ periodStatusLabel(period) }}
                </span>
              </td>
              <td>
                <span class="reserve-chip">
                  <svg class="icon" aria-hidden="true"><use href="#icon-percent" /></svg>
                  {{ reservePercent(period.reserve_fund_rate) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar periodo" title="Editar periodo" @click="editPeriod(period)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar periodo" title="Borrar periodo" @click="askDeletePeriod(period)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!periods.length">
              <td class="empty-row" colspan="5">{{ loading ? "Cargando periodos..." : "Sin periodos registrados." }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="activeTab === 'incomes'" class="accounting-list-section">
      <div class="accounting-section-header">
        <div>
          <h2>Ingresos</h2>
          <p class="placeholder-copy">{{ selectedPeriod?.name || "Selecciona un periodo" }}</p>
        </div>
        <button class="button orange" type="button" :disabled="!selectedPeriodId" @click="openCreateIncome">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo ingreso</span>
        </button>
      </div>

      <form v-if="false" class="entity-form" @submit.prevent="saveIncome">
        <h2>Nuevo ingreso</h2>
        <div class="entity-form-grid">
          <label>
            Fecha
            <input v-model="incomeForm.income_date" required type="date" />
          </label>
          <label>
            Monto
            <input v-model="incomeForm.amount" required inputmode="decimal" />
          </label>
          <label>
            Unidad
            <select v-model="incomeForm.unit_id">
              <option value="">Sin unidad</option>
              <option v-for="unit in units" :key="unit.id" :value="unit.id">{{ unit.identifier }}</option>
            </select>
          </label>
          <label>
            Tipo
            <select v-model="incomeForm.income_type_id">
              <option value="">Sin tipo</option>
              <option v-for="type in incomeTypes" :key="type.id" :value="type.id">{{ type.name }}</option>
            </select>
          </label>
          <label class="span-all">
            Descripción
            <textarea v-model="incomeForm.description" required rows="3" />
          </label>
        </div>
        <div class="form-actions">
          <button class="button navy" type="submit" :disabled="!selectedPeriodId">
            <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
            <span>Registrar ingreso</span>
          </button>
        </div>
      </form>

      <div class="edifito-table-wrap entity-table-wrap">
        <table class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th>Monto</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="income in filteredIncomes" :key="income.id">
              <td>{{ formatDate(income.income_date) }}</td>
              <td><strong>{{ income.description }}</strong></td>
              <td>{{ formatCLP(income.amount) }}</td>
              <td>{{ income.status }}</td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar ingreso" title="Editar ingreso" @click="openEditIncome(income)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar ingreso" title="Borrar ingreso" @click="askDeleteIncome(income)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!filteredIncomes.length">
              <td class="empty-row" colspan="5">Sin ingresos para el periodo seleccionado.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="activeTab === 'expenses'" class="accounting-list-section">
      <div class="accounting-section-header">
        <div>
          <h2>Egresos</h2>
          <p class="placeholder-copy">{{ selectedPeriod?.name || "Selecciona un periodo" }}</p>
        </div>
        <button class="button orange" type="button" :disabled="!selectedPeriodId" @click="openCreateExpense">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo egreso</span>
        </button>
      </div>

      <form v-if="false" class="entity-form" @submit.prevent="saveExpense">
        <h2>Nuevo egreso</h2>
        <div class="entity-form-grid">
          <label>
            Fecha
            <input v-model="expenseForm.expense_date" required type="date" />
          </label>
          <label>
            Monto
            <input v-model="expenseForm.amount" required inputmode="decimal" />
          </label>
          <label>
            Proveedor
            <select v-model="expenseForm.supplier_id">
              <option value="">Sin proveedor</option>
              <option v-for="supplier in filteredSuppliers" :key="supplier.id" :value="supplier.id">{{ supplier.name }}</option>
            </select>
          </label>
          <label>
            Categoría
            <input v-model="expenseForm.category" maxlength="80" />
          </label>
          <label class="switch-field">
            <input v-model="expenseForm.is_common_expense" type="checkbox" />
            <span class="switch-slider" aria-hidden="true"></span>
            <span>Prorratear</span>
          </label>
          <label class="span-all">
            Descripción
            <textarea v-model="expenseForm.description" required rows="3" />
          </label>
        </div>
        <div class="form-actions">
          <button class="button navy" type="submit" :disabled="!selectedPeriodId">
            <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
            <span>Registrar egreso</span>
          </button>
        </div>
      </form>

      <div class="edifito-table-wrap entity-table-wrap">
        <table class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th>Categoría</th>
              <th>Monto</th>
              <th>Prorratea</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="expense in filteredExpenses" :key="expense.id">
              <td>{{ formatDate(expense.expense_date) }}</td>
              <td><strong>{{ expense.description }}</strong></td>
              <td>{{ expense.category || "" }}</td>
              <td>{{ formatCLP(expense.amount) }}</td>
              <td>{{ expense.is_common_expense ? "Si" : "No" }}</td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar egreso" title="Editar egreso" @click="openEditExpense(expense)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Borrar egreso" title="Borrar egreso" @click="askDeleteExpense(expense)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!filteredExpenses.length">
              <td class="empty-row" colspan="6">Sin egresos para el periodo seleccionado.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="activeTab === 'suppliers'" class="accounting-list-section">
      <div class="accounting-section-header">
        <div>
          <h2>Proveedores</h2>
          <p class="placeholder-copy">Alta y mantenimiento de proveedores usados en egresos.</p>
        </div>
        <button class="button orange" type="button" @click="openCreateSupplier">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nuevo proveedor</span>
        </button>
      </div>

      <div class="edifito-table-wrap entity-table-wrap">
        <table class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Proveedor</th>
              <th>RUT</th>
              <th>Contacto</th>
              <th>Categoría</th>
              <th>Estado</th>
              <th>Acciones</th>
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
              <td>{{ supplier.category || "Sin categoría" }}</td>
              <td>
                <span class="period-status-chip" :class="supplierStatusClass(supplier.status)">
                  <span aria-hidden="true"></span>
                  {{ supplierStatusLabel(supplier.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="button compact icon-action navy" type="button" aria-label="Editar proveedor" title="Editar proveedor" @click="openEditSupplier(supplier)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
                </button>
                <button class="button compact icon-action danger" type="button" aria-label="Quitar proveedor" title="Quitar proveedor de este condominio" @click="askDeleteSupplier(supplier)">
                  <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
                </button>
              </td>
            </tr>
            <tr v-if="!filteredSuppliers.length">
              <td class="empty-row" colspan="6">Sin proveedores registrados.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="activeTab === 'common'" class="common-expense-pane">
      <div class="common-actions">
        <div>
          <h2>Gasto común del periodo</h2>
          <p class="placeholder-copy">
            {{ selectedPeriod?.name || "Selecciona un periodo" }}
            <span v-if="summary?.latest_run"> · {{ summary.latest_run.charge_count }} unidades calculadas</span>
          </p>
        </div>
        <button class="button orange" type="button" :disabled="!selectedPeriodId || loading" @click="calculateCommonExpenses">
          <svg class="icon" aria-hidden="true"><use href="#icon-calculator" /></svg>
          <span>Calcular gastos comunes</span>
        </button>
      </div>

      <div class="metrics-grid">
        <div class="metric">
          <span>Total egresos base</span>
          <strong>{{ formatCLP(summary?.latest_run?.total_expenses || summary?.totals.common_expense) }}</strong>
        </div>
        <div class="metric">
          <span>Fondo reserva</span>
          <strong>{{ formatCLP(summary?.latest_run?.total_reserve_fund) }}</strong>
        </div>
        <div class="metric">
          <span>Total a cobrar</span>
          <strong>{{ formatCLP(summary?.latest_run?.total_charged) }}</strong>
        </div>
        <div class="metric">
          <span>Último cálculo</span>
          <strong class="small-metric">{{ summary?.latest_run?.calculated_at ? formatDate(summary.latest_run.calculated_at) : "Pendiente" }}</strong>
        </div>
      </div>

      <div class="edifito-table-wrap entity-table-wrap">
        <table class="edifito-table entity-table">
          <thead>
            <tr>
              <th>Unidad</th>
              <th>Prorrateo</th>
              <th>Base</th>
              <th>Fondo reserva</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="charge in charges" :key="charge.id">
              <td><strong>{{ charge.unit_identifier }}</strong></td>
              <td>{{ charge.proration }}%</td>
              <td>{{ formatCLP(charge.expense_amount) }}</td>
              <td>{{ formatCLP(charge.reserve_fund_amount) }}</td>
              <td>{{ formatCLP(charge.total_amount) }}</td>
            </tr>
            <tr v-if="!charges.length">
              <td class="empty-row" colspan="5">Ejecuta el cálculo para ver el detalle por unidad.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <div v-if="incomeModalOpen" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="income-modal-title">
    <form class="confirm-modal accounting-modal" @submit.prevent="saveIncome">
      <div class="accounting-modal-header">
        <div>
          <p class="eyebrow">Ingresos</p>
          <h2 id="income-modal-title">{{ editingIncomeId ? "Editar ingreso" : "Nuevo ingreso" }}</h2>
        </div>
        <button class="button ghost compact icon-action" type="button" aria-label="Cerrar" title="Cerrar" @click="closeIncomeModal">
          <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
        </button>
      </div>
      <div class="entity-form-grid">
        <label>
          Fecha
          <input v-model="incomeForm.income_date" required type="date" />
        </label>
        <label>
          Monto
          <input v-model="incomeForm.amount" required inputmode="decimal" />
        </label>
        <div class="income-classification span-all">
          <label class="unit-search-field">
            Unidad
            <input v-model="unitSearch" type="search" autocomplete="off" placeholder="Buscar unidad" />
            <span class="selected-unit-pill">
              {{ selectedIncomeUnit ? unitLabel(selectedIncomeUnit) : "Sin unidad" }}
              <button v-if="selectedIncomeUnit" type="button" aria-label="Quitar unidad" title="Quitar unidad" @click="selectIncomeUnit(null)">
                <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
              </button>
            </span>
            <div class="unit-search-results">
              <button class="unit-option" type="button" @click="selectIncomeUnit(null)">Sin unidad</button>
              <button v-for="unit in filteredUnitOptions" :key="unit.id" class="unit-option" type="button" @click="selectIncomeUnit(unit)">
                {{ unitLabel(unit) }}
              </button>
              <span v-if="unitSearchLoading" class="unit-search-hint">Buscando unidades...</span>
              <span v-else-if="unitSearch && !filteredUnitOptions.length" class="unit-search-hint">Sin coincidencias</span>
            </div>
          </label>
          <div class="income-side-fields">
            <label>
              Tipo
              <select v-model="incomeForm.income_type_id">
                <option value="">Sin tipo</option>
                <option v-for="type in incomeTypes" :key="type.id" :value="type.id">{{ type.name }}</option>
              </select>
            </label>
            <label>
              Banco
              <select v-model="incomeForm.bank_id">
                <option value="">Sin banco</option>
                <option v-for="bank in banks" :key="bank.id" :value="bank.id">{{ bank.name }}</option>
              </select>
            </label>
          </div>
        </div>
        <label class="span-all">
          Descripcion
          <textarea v-model="incomeForm.description" required rows="3" />
        </label>
      </div>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="closeIncomeModal">Cancelar</button>
        <button class="button navy" type="submit" :disabled="!selectedPeriodId">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>{{ editingIncomeId ? "Actualizar ingreso" : "Guardar ingreso" }}</span>
        </button>
      </div>
    </form>
  </div>

  <div v-if="expenseModalOpen" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="expense-modal-title">
    <form class="confirm-modal accounting-modal" @submit.prevent="saveExpense">
      <div class="accounting-modal-header">
        <div>
          <p class="eyebrow">Egresos</p>
          <h2 id="expense-modal-title">{{ editingExpenseId ? "Editar egreso" : "Nuevo egreso" }}</h2>
        </div>
        <button class="button ghost compact icon-action" type="button" aria-label="Cerrar" title="Cerrar" @click="closeExpenseModal">
          <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
        </button>
      </div>
      <div class="entity-form-grid">
        <label>
          Fecha
          <input v-model="expenseForm.expense_date" required type="date" />
        </label>
        <label>
          Monto
          <input v-model="expenseForm.amount" required inputmode="decimal" />
        </label>
        <label>
          Proveedor
          <select v-model="expenseForm.supplier_id">
            <option value="">Sin proveedor</option>
            <option v-for="supplier in filteredSuppliers" :key="supplier.id" :value="supplier.id">{{ supplier.name }}</option>
          </select>
        </label>
        <label>
          Categoria
          <input v-model="expenseForm.category" maxlength="80" />
        </label>
        <label class="switch-field">
          <input v-model="expenseForm.is_common_expense" type="checkbox" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Prorratear</span>
        </label>
        <label class="span-all">
          Descripcion
          <textarea v-model="expenseForm.description" required rows="3" />
        </label>
      </div>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="closeExpenseModal">Cancelar</button>
        <button class="button navy" type="submit" :disabled="!selectedPeriodId">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>{{ editingExpenseId ? "Actualizar egreso" : "Guardar egreso" }}</span>
        </button>
      </div>
    </form>
  </div>

  <div v-if="supplierModalOpen" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="supplier-modal-title">
    <form class="confirm-modal accounting-modal" @submit.prevent="saveSupplier">
      <div class="accounting-modal-header">
        <div>
          <p class="eyebrow">Proveedores</p>
          <h2 id="supplier-modal-title">{{ editingSupplierId ? "Editar proveedor" : "Nuevo proveedor" }}</h2>
        </div>
        <button class="button ghost compact icon-action" type="button" aria-label="Cerrar" title="Cerrar" @click="closeSupplierModal">
          <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
        </button>
      </div>
      <div class="entity-form-grid">
        <label>
          Nombre
          <input v-model="supplierForm.name" required maxlength="180" placeholder="Ej. Ascensores del Pacífico" />
        </label>
        <label>
          RUT
          <input v-model="supplierForm.rut" maxlength="30" placeholder="76.123.456-7" />
        </label>
        <label>
          Email
          <input v-model="supplierForm.email" type="email" maxlength="255" placeholder="contacto@proveedor.cl" />
        </label>
        <label>
          Teléfono
          <input v-model="supplierForm.phone" maxlength="40" placeholder="+56 9..." />
        </label>
        <label>
          Categoría
          <input v-model="supplierForm.category" maxlength="80" placeholder="Mantención, aseo, seguridad..." />
        </label>
        <label>
          Estado
          <select v-model="supplierForm.status">
            <option value="active">Activo</option>
            <option value="inactive">Inactivo</option>
            <option value="draft">Borrador</option>
          </select>
        </label>
        <label v-if="!editingSupplierId && condominiums.length > 1" class="switch-field span-all">
          <input v-model="supplierForm.duplicate_all_condominiums" type="checkbox" />
          <span class="switch-slider" aria-hidden="true"></span>
          <span>Crear también en todos los condominios de la empresa</span>
        </label>
        <label class="span-all">
          Notas
          <textarea v-model="supplierForm.notes" rows="3" placeholder="Condiciones, contacto comercial, cobertura o cualquier referencia útil." />
        </label>
      </div>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="closeSupplierModal">Cancelar</button>
        <button class="button navy" type="submit">
          <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
          <span>{{ editingSupplierId ? "Actualizar proveedor" : "Guardar proveedor" }}</span>
        </button>
      </div>
    </form>
  </div>

  <div v-if="deleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-record-title">
    <div class="confirm-modal">
      <p class="eyebrow">{{ deleteCandidate.type === "income" ? "Eliminar ingreso" : "Eliminar egreso" }}</p>
      <h2 id="delete-record-title">{{ deleteCandidate.label }}</h2>
      <p>Esta accion eliminara el movimiento del periodo contable seleccionado. Revisa que no forme parte de un cierre o calculo que debas conservar.</p>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="cancelDeleteRecord">Cancelar</button>
        <button class="button danger" type="button" @click="confirmDeleteRecord">
          <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
          <span>Eliminar</span>
        </button>
      </div>
    </div>
  </div>

  <div v-if="supplierDeleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-supplier-title">
    <div class="confirm-modal">
      <p class="eyebrow">Quitar proveedor</p>
      <h2 id="delete-supplier-title">{{ supplierDeleteCandidate.name }}</h2>
      <p>Esta acción quitará el proveedor del condominio activo, sin eliminar su ficha maestra de la empresa.</p>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="cancelDeleteSupplier">Cancelar</button>
        <button class="button danger" type="button" @click="confirmDeleteSupplier">
          <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
          <span>Quitar proveedor</span>
        </button>
      </div>
    </div>
  </div>

  <div v-if="periodDeleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-period-title">
    <div class="confirm-modal">
      <p class="eyebrow">Eliminar periodo</p>
      <h2 id="delete-period-title">{{ periodDeleteCandidate.name }}</h2>
      <p>
        Esta acción eliminará el periodo solo si no tiene ingresos, egresos ni cálculos de gasto común. Si ya fue usado, el sistema lo bloqueará.
      </p>
      <p v-if="periodDeleteCandidate.is_active" class="delete-warning">
        Este periodo está activo. Al eliminarlo, el condominio quedará sin periodo activo hasta que marques otro.
      </p>
      <div class="form-actions">
        <button class="button ghost" type="button" @click="cancelDeletePeriod">Cancelar</button>
        <button class="button danger" type="button" @click="confirmDeletePeriod">
          <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
          <span>Eliminar periodo</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.accounting-panel {
  display: grid;
  gap: 18px;
}

.accounting-header,
.common-actions,
.accounting-section-header,
.accounting-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.period-picker {
  min-width: min(320px, 100%);
}

.period-picker select,
.entity-form select,
.entity-form textarea,
.accounting-modal select,
.accounting-modal textarea {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 9px 11px;
  color: var(--text);
  background: var(--white);
  font: inherit;
}

.entity-form textarea,
.accounting-modal textarea {
  resize: vertical;
}

.accounting-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.accounting-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.accounting-list-section,
.accounting-modal {
  display: grid;
  gap: 16px;
}

.accounting-section-header {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px 16px;
  background: #fbfcfe;
}

.accounting-modal {
  width: min(720px, 100%);
}

.unit-search-field {
  display: grid;
  gap: 8px;
}

.income-classification {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 1fr);
  gap: 12px;
  align-items: start;
}

.income-side-fields {
  display: grid;
  gap: 12px;
}

.income-side-fields label {
  display: grid;
  gap: 6px;
}

.selected-unit-pill {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  min-height: 28px;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 5px 9px;
  color: #0f2a43;
  background: #eef6ff;
  font-size: 12px;
  font-weight: 800;
}

.selected-unit-pill button {
  display: inline-flex;
  width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 999px;
  color: inherit;
  background: transparent;
  cursor: pointer;
}

.selected-unit-pill .icon {
  width: 13px;
  height: 13px;
}

.unit-search-results {
  display: grid;
  max-height: 170px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--white);
}

.unit-option {
  border: 0;
  border-bottom: 1px solid var(--line);
  padding: 9px 10px;
  color: var(--text);
  background: transparent;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.unit-option:hover,
.unit-option:focus-visible {
  background: #fff7ed;
  outline: none;
}

.unit-option:last-of-type {
  border-bottom: 0;
}

.unit-search-hint {
  padding: 9px 10px;
  color: var(--muted);
  font-size: 13px;
}

.muted-table-note {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 400;
}

.entity-form {
  border: 1px solid var(--line);
  border-radius: 8px;
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

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.success-message {
  margin: 0;
  color: #067647;
  font-size: 13px;
  font-weight: 700;
}

.small-metric {
  font-size: 20px;
}

.period-status-chip,
.reserve-chip {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  gap: 7px;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 800;
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

.period-status-chip.open {
  color: #175cd3;
  background: #eff8ff;
}

.period-status-chip.draft {
  color: #475467;
  background: #f2f4f7;
}

.period-status-chip.closed {
  color: #5925dc;
  background: #f4f3ff;
}

.period-status-chip.blocked {
  color: #b42318;
  background: #fef3f2;
}

.reserve-chip {
  color: #854a0e;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}

.reserve-chip .icon {
  width: 14px;
  height: 14px;
}

.delete-warning {
  margin: 12px 0 0;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  padding: 10px 12px;
  color: #9a3412;
  background: #fff7ed;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .accounting-header,
  .common-actions {
    flex-direction: column;
  }

  .accounting-grid {
    grid-template-columns: 1fr;
  }

  .income-classification {
    grid-template-columns: 1fr;
  }
}
</style>
