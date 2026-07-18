<script setup lang="ts">
type OperationalEvent = {
  id: string;
  title: string;
  description?: string | null;
  planned_date: string;
  planned_start_time?: string | null;
  planned_end_time?: string | null;
  estimated_duration_hours?: number | null;
  estimated_duration_minutes?: number | null;
  assigned_profile?: string | null;
  assigned_user_id?: string | null;
  assigned_user_name?: string | null;
  assigned_user_email?: string | null;
  priority: string;
  status: string;
  event_type?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  section_name?: string | null;
  asset_name?: string | null;
  template_item_id?: string | null;
  agenda_order?: number | null;
};

type OperationalStaff = {
  user_id: string;
  full_name: string;
  email?: string | null;
  portal_profile: string;
  responsibility?: string | null;
  is_primary: boolean;
};

type OperationalPlanResponse = {
  condominium_id: string;
  condominium_name: string;
  year: number;
  month?: number | null;
  items: OperationalEvent[];
  staff: OperationalStaff[];
  summary: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    overdue: number;
  };
};

type AssemblyDetail = {
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
  attendees?: Array<{ name?: string | null; email?: string | null; role?: string | null; attendance_status?: string | null }>;
  agenda_items?: Array<{ id?: string | null; title?: string | null; description?: string | null; owner?: string | null; conclusion?: string | null; status?: string | null }>;
  conclusions?: string | null;
  event?: OperationalEvent | null;
};

type InspectionChecklistItem = {
  id: string;
  label: string;
  status: string;
  observations?: string | null;
  requires_action: boolean;
};

type InspectionDetail = OperationalEvent & {
  execution?: {
    result?: string | null;
    comments?: string | null;
    requires_follow_up?: boolean;
    checklist?: InspectionChecklistItem[];
  } | null;
};

type ExternalServiceOrder = {
  id: string;
  event_id: string;
  title: string;
  provider_name: string;
  provider_email?: string | null;
  provider_phone?: string | null;
  status: string;
  expires_at?: string | null;
  submitted_at?: string | null;
  prompt_key: string;
  public_url?: string | null;
};

type SupplierRecord = {
  id: string;
  condominium_id?: string | null;
  name: string;
  rut?: string | null;
  email?: string | null;
  phone?: string | null;
  category?: string | null;
  status?: string | null;
};

type SupplierCondominiumLink = {
  id: string;
  supplier_id: string;
  condominium_id: string;
  status?: string | null;
};

const { request } = useApi();
const { activeCondominium, token } = useAuth();

const events = ref<OperationalEvent[]>([]);
const staff = ref<OperationalStaff[]>([]);
const suppliers = ref<SupplierRecord[]>([]);
const supplierLinks = ref<SupplierCondominiumLink[]>([]);
const summary = reactive({
  total: 0,
  pending: 0,
  in_progress: 0,
  completed: 0,
  overdue: 0,
});
const loading = ref(false);
const errorMessage = ref("");
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(String(new Date().getMonth() + 1));
const selectedStatus = ref("");
const search = ref("");
const savingAssignment = ref("");
const creatingExternalOrderId = ref("");
const externalOrderMessage = ref("");
const agendaView = ref<"list" | "week">("list");
const selectedWeekStart = ref<Date | null>(null);
const showIncidentForm = ref(false);
const showTaskForm = ref(false);
const showInspectionForm = ref(false);
const showAssemblyForm = ref(false);
const showEditForm = ref(false);
const showExternalOrderForm = ref(false);
const savingIncident = ref(false);
const savingTask = ref(false);
const savingInspection = ref(false);
const savingAssembly = ref(false);
const savingEdit = ref(false);
const savingExternalOrder = ref(false);
const loadingExternalSuppliers = ref(false);
const externalOrderEvent = ref<OperationalEvent | null>(null);
const editingIncidentEventId = ref("");
const editingAssemblyId = ref("");
const editingInspectionEventId = ref("");
const draggingEventId = ref("");
const dragOverDate = ref("");
const dragTargetKey = ref("");
const deletingEventId = ref("");
const deleteCandidate = ref<OperationalEvent | null>(null);
const incidentForm = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  estimated_duration_hours: "",
  assigned_user_id: "",
  priority: "medium",
  status: "pending",
});
const taskForm = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  estimated_duration_hours: "",
  assigned_user_id: "",
  priority: "medium",
  event_type: "task",
});
const inspectionForm = reactive({
  title: "",
  description: "",
  planned_date: new Date().toISOString().slice(0, 10),
  planned_start_time: "",
  estimated_duration_hours: "",
  assigned_user_id: "",
  priority: "medium",
  result: "in_progress",
  comments: "",
  requires_follow_up: false,
  close_event: false,
  checklist: [] as InspectionChecklistItem[],
});
const assemblyForm = reactive({
  title: "",
  description: "",
  scheduled_date: new Date().toISOString().slice(0, 10),
  scheduled_start_time: "",
  estimated_duration_hours: "",
  location: "",
  modality: "presential",
  assembly_type: "ordinary",
  status: "scheduled",
  attendees: [{ name: "", email: "", role: "", attendance_status: "expected" }],
  agenda_items: [{ id: "point-1", title: "", description: "", owner: "", conclusion: "", status: "pending" }],
  conclusions: "",
});
const editForm = reactive({
  id: "",
  title: "",
  description: "",
  planned_date: "",
  planned_start_time: "",
  estimated_duration_hours: "",
  assigned_user_id: "",
  priority: "medium",
  status: "pending",
  event_type: "task",
});
const externalOrderForm = reactive({
  provider_mode: "registered" as "registered" | "manual",
  provider_supplier_id: "",
  provider_name: "",
  provider_email: "",
  provider_phone: "",
  title: "",
  instructions: "",
  prompt_key: "vendor_service_report",
  expires_in_days: "7",
  public_url: "",
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
  ["pending", "Pendiente"],
  ["in_progress", "En curso"],
  ["completed", "Completado"],
  ["cancelled", "Cancelado"],
] as const;

const inspectionResultOptions = [
  ["in_progress", "En curso"],
  ["conforme", "Conforme"],
  ["observed", "Con observaciones"],
  ["requires_action", "Requiere accion"],
  ["not_executed", "No ejecutada"],
] as const;

const checklistStatusOptions = [
  ["pending", "Pendiente"],
  ["ok", "Conforme"],
  ["observed", "Observado"],
  ["requires_action", "Requiere accion"],
] as const;

const eventTypeOptions = [
  ["task", "Generica"],
  ["administrative", "Administrativa"],
  ["assembly", "Asamblea"],
  ["meeting", "Reunion"],
  ["inspection", "Inspeccion"],
  ["maintenance", "Mantencion"],
  ["incident", "Incidencia"],
] as const;

const yearOptions = computed(() => {
  const current = new Date().getFullYear();
  return [current - 1, current, current + 1, current + 2];
});

const normalizedSearch = computed(() => normalize(search.value));

const searchedEvents = computed(() => events.value.filter((event) => {
  if (!normalizedSearch.value) return true;
  const text = normalize(`${event.title} ${event.description || ""} ${event.section_name || ""} ${event.asset_name || ""} ${event.assigned_profile || ""} ${event.assigned_user_name || ""}`);
  return text.includes(normalizedSearch.value);
}));

const externalOrderSuppliers = computed(() => {
  const condominiumId = activeCondominium.value?.id;
  if (!condominiumId) return [];
  const linkedIds = new Set(supplierLinks.value
    .filter((link) => link.condominium_id === condominiumId && link.status !== "inactive")
    .map((link) => link.supplier_id));
  return suppliers.value
    .filter((supplier) => supplier.status !== "inactive")
    .filter((supplier) => linkedIds.has(supplier.id) || supplier.condominium_id === condominiumId)
    .sort((left, right) => left.name.localeCompare(right.name));
});

const selectedExternalSupplier = computed(() => externalOrderSuppliers.value
  .find((supplier) => supplier.id === externalOrderForm.provider_supplier_id) || null);

const externalOrderQrUrl = computed(() => {
  if (!externalOrderForm.public_url) return "";
  const data = encodeURIComponent(externalOrderForm.public_url);
  return `https://api.qrserver.com/v1/create-qr-code/?size=240x240&margin=12&data=${data}`;
});

const groupedEvents = computed(() => {
  const groups = new Map<string, OperationalEvent[]>();
  for (const event of visibleEvents.value) {
    groups.set(event.planned_date, [...(groups.get(event.planned_date) || []), event]);
  }
  return Array.from(groups.entries()).map(([dateKey, items]) => ({
    dateKey,
    items: sortAgendaEvents(items),
  }));
});

const defaultWeekStartDate = computed(() => {
  const year = Number(selectedYear.value);
  const month = selectedMonth.value ? Number(selectedMonth.value) : new Date().getMonth() + 1;
  const today = new Date();
  const base = today.getFullYear() === year && today.getMonth() + 1 === month
    ? new Date(today.getFullYear(), today.getMonth(), today.getDate())
    : new Date(year, month - 1, 1);
  const mondayOffset = (base.getDay() + 6) % 7;
  base.setDate(base.getDate() - mondayOffset);
  base.setHours(0, 0, 0, 0);
  return base;
});

const weekStartDate = computed(() => selectedWeekStart.value || defaultWeekStartDate.value);

const weekRangeLabel = computed(() => {
  const start = new Date(weekStartDate.value);
  const end = new Date(weekStartDate.value);
  end.setDate(start.getDate() + 6);
  const formatter = new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short", year: "numeric" });
  return `${formatter.format(start)} - ${formatter.format(end)}`;
});

const visibleEvents = computed(() => {
  const start = new Date(weekStartDate.value);
  const end = new Date(weekStartDate.value);
  end.setDate(start.getDate() + 6);
  const startKey = toDateKey(start);
  const endKey = toDateKey(end);
  return searchedEvents.value.filter((event) => event.planned_date >= startKey && event.planned_date <= endKey);
});

const weekDays = computed(() => Array.from({ length: 7 }, (_, index) => {
  const value = new Date(weekStartDate.value);
  value.setDate(weekStartDate.value.getDate() + index);
  const dateKey = toDateKey(value);
  return {
    dateKey,
    label: new Intl.DateTimeFormat("es-CL", { weekday: "short" }).format(value),
    day: new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short" }).format(value),
    items: sortAgendaEvents(visibleEvents.value.filter((event) => event.planned_date === dateKey)),
  };
}));

const moveWeek = (offset: number) => {
  const next = new Date(weekStartDate.value);
  next.setDate(next.getDate() + offset * 7);
  next.setHours(0, 0, 0, 0);
  selectedWeekStart.value = next;
  selectedYear.value = next.getFullYear();
  selectedMonth.value = String(next.getMonth() + 1);
};

const resetWeekSelection = () => {
  selectedWeekStart.value = null;
};

const goToCurrentWeek = () => {
  const today = new Date();
  selectedYear.value = today.getFullYear();
  selectedMonth.value = String(today.getMonth() + 1);
  selectedWeekStart.value = null;
};

const loadPlan = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.set("year", String(selectedYear.value));
    if (selectedMonth.value) params.set("month", selectedMonth.value);
    if (selectedStatus.value) params.set("status", selectedStatus.value);
    const data = await request<OperationalPlanResponse>(`/api/v1/portal/operational-plan/?${params}`);
    events.value = data.items || [];
    staff.value = data.staff || [];
    summary.total = data.summary?.total || 0;
    summary.pending = data.summary?.pending || 0;
    summary.in_progress = data.summary?.in_progress || 0;
    summary.completed = data.summary?.completed || 0;
    summary.overdue = data.summary?.overdue || 0;
  } catch (error) {
    events.value = [];
    staff.value = [];
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const loadExternalOrderSuppliers = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loadingExternalSuppliers.value = true;
  try {
    const [supplierPage, supplierLinkPage] = await Promise.all([
      request<{ items?: SupplierRecord[] }>("/api/v1/accounting-suppliers/?page_size=200&order_by=name"),
      request<{ items?: SupplierCondominiumLink[] }>("/api/v1/accounting-supplier-condominiums/?page_size=200"),
    ]);
    suppliers.value = supplierPage.items || [];
    supplierLinks.value = supplierLinkPage.items || [];
  } catch (error) {
    externalOrderMessage.value = `No se pudieron cargar proveedores guardados: ${readableError(error)}`;
  } finally {
    loadingExternalSuppliers.value = false;
  }
};

const applyExternalSupplier = () => {
  const supplier = selectedExternalSupplier.value;
  if (!supplier) return;
  externalOrderForm.provider_name = supplier.name || "";
  externalOrderForm.provider_email = supplier.email || "";
  externalOrderForm.provider_phone = supplier.phone || "";
};

const setExternalProviderMode = (mode: "registered" | "manual") => {
  externalOrderForm.provider_mode = mode;
  externalOrderForm.provider_supplier_id = "";
  externalOrderForm.provider_name = "";
  externalOrderForm.provider_email = "";
  externalOrderForm.provider_phone = "";
  externalOrderForm.public_url = "";
  if (mode === "registered" && !suppliers.value.length) {
    loadExternalOrderSuppliers();
  }
};

watch(() => externalOrderForm.provider_supplier_id, () => {
  applyExternalSupplier();
  externalOrderForm.public_url = "";
});

const assignEvent = async (event: OperationalEvent, assignedUserId: string) => {
  savingAssignment.value = event.id;
  errorMessage.value = "";
  try {
    const updated = await request<OperationalEvent>(`/api/v1/portal/operational-plan/events/${event.id}/assignment`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assigned_user_id: assignedUserId || null }),
    });
    replaceEvent(updated);
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingAssignment.value = "";
  }
};

const openExternalOrderForm = (event: OperationalEvent) => {
  externalOrderEvent.value = event;
  externalOrderForm.provider_mode = "registered";
  externalOrderForm.provider_supplier_id = "";
  externalOrderForm.provider_name = "";
  externalOrderForm.provider_email = "";
  externalOrderForm.provider_phone = "";
  externalOrderForm.title = event.title;
  externalOrderForm.instructions = event.description || "";
  externalOrderForm.prompt_key = suggestedPromptKey(event);
  externalOrderForm.expires_in_days = "7";
  externalOrderForm.public_url = "";
  externalOrderMessage.value = "";
  errorMessage.value = "";
  showExternalOrderForm.value = true;
  loadExternalOrderSuppliers();
};

const closeExternalOrderForm = () => {
  if (savingExternalOrder.value) return;
  showExternalOrderForm.value = false;
  externalOrderEvent.value = null;
};

const suggestedPromptKey = (event: OperationalEvent) => {
  const text = normalize(`${event.title} ${event.asset_name || ""} ${event.description || ""}`);
  return text.includes("ascensor") || text.includes("elevador")
    ? "elevator_inspection_report"
    : "vendor_service_report";
};

const createExternalServiceOrder = async () => {
  if (!externalOrderEvent.value) return;
  if (externalOrderForm.provider_mode === "registered" && selectedExternalSupplier.value) {
    applyExternalSupplier();
  }
  if (!externalOrderForm.provider_name.trim()) {
    errorMessage.value = "Indica un proveedor guardado o escribe un proveedor puntual.";
    return;
  }
  savingExternalOrder.value = true;
  creatingExternalOrderId.value = externalOrderEvent.value.id;
  externalOrderMessage.value = "";
  errorMessage.value = "";
  try {
    const order = await request<ExternalServiceOrder>(`/api/v1/portal/operational-plan/events/${externalOrderEvent.value.id}/external-service-orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider_name: externalOrderForm.provider_name,
        provider_email: externalOrderForm.provider_email || null,
        provider_phone: externalOrderForm.provider_phone || null,
        title: externalOrderForm.title || externalOrderEvent.value.title,
        instructions: externalOrderForm.instructions || null,
        prompt_key: externalOrderForm.prompt_key || "vendor_service_report",
        expires_in_days: Number(externalOrderForm.expires_in_days) || 7,
        public_base_url: import.meta.client ? window.location.origin : null,
      }),
    });
    externalOrderForm.public_url = order.public_url || "";
    externalOrderMessage.value = `Link creado para ${order.provider_name}.`;
    if (order.public_url && import.meta.client && navigator.clipboard) {
      await navigator.clipboard.writeText(order.public_url);
      externalOrderMessage.value = `Link creado y copiado para ${order.provider_name}.`;
    }
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    creatingExternalOrderId.value = "";
    savingExternalOrder.value = false;
  }
};

const copyExternalOrderLink = async () => {
  if (!externalOrderForm.public_url || !import.meta.client || !navigator.clipboard) return;
  await navigator.clipboard.writeText(externalOrderForm.public_url);
  externalOrderMessage.value = "Link copiado al portapapeles.";
};

const replaceEvent = (updated: OperationalEvent) => {
  events.value = events.value.map((item) => item.id === updated.id ? updated : item);
  recomputeSummary();
};

const recomputeSummary = () => {
  const today = toDateKey(new Date());
  summary.total = events.value.length;
  summary.pending = events.value.filter((event) => event.status === "pending").length;
  summary.in_progress = events.value.filter((event) => event.status === "in_progress").length;
  summary.completed = events.value.filter((event) => event.status === "completed" || event.status === "done").length;
  summary.overdue = events.value.filter((event) => !["completed", "done", "cancelled"].includes(event.status) && event.planned_date < today).length;
};

const moveEventToDate = async (event: OperationalEvent, plannedDate: string) => {
  if (event.planned_date === plannedDate || deletingEventId.value === event.id) return;
  errorMessage.value = "";
  try {
    const updated = await request<OperationalEvent>(`/api/v1/portal/operational-plan/events/${event.id}/schedule`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ planned_date: plannedDate }),
    });
    events.value = events.value.map((item) => item.id === updated.id ? updated : item);
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const sortAgendaEvents = (items: OperationalEvent[]) => [...items].sort((left, right) => {
  const orderCompare = (left.agenda_order || 0) - (right.agenda_order || 0);
  if (orderCompare) return orderCompare;
  const timeCompare = (left.planned_start_time || "").localeCompare(right.planned_start_time || "");
  return timeCompare || left.title.localeCompare(right.title);
});

const startEventDrag = (event: DragEvent, item: OperationalEvent) => {
  draggingEventId.value = item.id;
  event.dataTransfer?.setData("text/plain", item.id);
  if (event.dataTransfer) event.dataTransfer.effectAllowed = "move";
};

const endEventDrag = () => {
  draggingEventId.value = "";
  dragOverDate.value = "";
  dragTargetKey.value = "";
};

const setDropTarget = (dayDate: string, beforeEventId = "") => {
  dragOverDate.value = dayDate;
  dragTargetKey.value = `${dayDate}:${beforeEventId || "end"}`;
};

const beforeIdFromCardPosition = (
  event: DragEvent,
  dayItems: OperationalEvent[],
  index: number,
) => {
  const target = event.currentTarget as HTMLElement | null;
  if (!target) return dayItems[index]?.id || "";
  const rect = target.getBoundingClientRect();
  const isUpperHalf = event.clientY < rect.top + rect.height / 2;
  return isUpperHalf ? dayItems[index]?.id || "" : dayItems[index + 1]?.id || "";
};

const setCardDropTarget = (
  event: DragEvent,
  dayDate: string,
  dayItems: OperationalEvent[],
  index: number,
) => {
  setDropTarget(dayDate, beforeIdFromCardPosition(event, dayItems, index));
};

const dropEventOnCard = async (
  event: DragEvent,
  dayDate: string,
  dayItems: OperationalEvent[],
  index: number,
) => {
  await dropEventOnPosition(dayDate, beforeIdFromCardPosition(event, dayItems, index));
};

const dropEventOnPosition = async (dayDate: string, beforeEventId = "") => {
  const draggedEvent = events.value.find((item) => item.id === draggingEventId.value);
  endEventDrag();
  if (!draggedEvent) return;
  if (beforeEventId === draggedEvent.id) return;
  await reorderEventToPosition(draggedEvent, dayDate, beforeEventId);
};

const reorderEventToPosition = async (event: OperationalEvent, dayDate: string, beforeEventId = "") => {
  if (deletingEventId.value === event.id) return;
  const targetEvents = sortAgendaEvents(events.value.filter((item) => item.planned_date === dayDate && item.id !== event.id));
  const insertIndex = beforeEventId ? targetEvents.findIndex((item) => item.id === beforeEventId) : targetEvents.length;
  const nextEvents = [...targetEvents];
  nextEvents.splice(insertIndex >= 0 ? insertIndex : nextEvents.length, 0, { ...event, planned_date: dayDate });
  const orderedEventIds = nextEvents.map((item) => item.id);

  errorMessage.value = "";
  try {
    const updated = await request<OperationalEvent[]>("/api/v1/portal/operational-plan/events/reorder", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ planned_date: dayDate, ordered_event_ids: orderedEventIds }),
    });
    const updatedById = new Map(updated.map((item) => [item.id, item]));
    events.value = events.value.map((item) => updatedById.get(item.id) || item);
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const sendEventToNextWeek = async (event: OperationalEvent) => {
  const targetDate = targetDateForWeekOffset(1);
  if (!targetDate) return;
  await reorderEventToPosition(event, targetDate);
};

const sendEventToPreviousWeek = async (event: OperationalEvent) => {
  const targetDate = targetDateForWeekOffset(-1);
  if (!targetDate) return;
  await reorderEventToPosition(event, targetDate);
};

const todayDate = () => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
};

const targetDateForWeekOffset = (offset: number) => {
  const targetStart = new Date(weekStartDate.value);
  targetStart.setDate(targetStart.getDate() + offset * 7);
  targetStart.setHours(0, 0, 0, 0);

  const targetEnd = new Date(targetStart);
  targetEnd.setDate(targetStart.getDate() + 6);

  const today = todayDate();
  if (targetEnd < today) return offset > 0 ? toDateKey(today) : "";
  return toDateKey(targetStart < today ? today : targetStart);
};

const canSendToPreviousWeek = computed(() => Boolean(targetDateForWeekOffset(-1)));

const weekMoveTitle = (offset: number) => {
  const targetDate = targetDateForWeekOffset(offset);
  if (!targetDate) return "No se puede mover al pasado";
  return offset < 0 ? `Enviar a la semana anterior (${shortDate(targetDate)})` : `Enviar a la próxima semana (${shortDate(targetDate)})`;
};

const openDeleteEvent = (event: OperationalEvent) => {
  deleteCandidate.value = event;
};

const closeDeleteEvent = () => {
  if (deletingEventId.value) return;
  deleteCandidate.value = null;
};

const confirmDeleteEvent = async () => {
  if (!deleteCandidate.value) return;
  const candidate = deleteCandidate.value;
  deletingEventId.value = candidate.id;
  errorMessage.value = "";
  try {
    await request(`/api/v1/portal/operational-plan/events/${candidate.id}`, { method: "DELETE" });
    events.value = events.value.filter((event) => event.id !== candidate.id);
    summary.total = Math.max(0, summary.total - 1);
    if (candidate.status === "pending") summary.pending = Math.max(0, summary.pending - 1);
    if (candidate.status === "in_progress") summary.in_progress = Math.max(0, summary.in_progress - 1);
    if (candidate.status === "completed" || candidate.status === "done") summary.completed = Math.max(0, summary.completed - 1);
    if (!["completed", "done", "cancelled"].includes(candidate.status) && candidate.planned_date < toDateKey(new Date())) {
      summary.overdue = Math.max(0, summary.overdue - 1);
    }
    deleteCandidate.value = null;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    deletingEventId.value = "";
  }
};

const openIncidentForm = () => {
  editingIncidentEventId.value = "";
  incidentForm.title = "";
  incidentForm.description = "";
  incidentForm.planned_date = toDateKey(new Date());
  incidentForm.planned_start_time = "";
  incidentForm.estimated_duration_hours = "";
  incidentForm.assigned_user_id = "";
  incidentForm.priority = "medium";
  incidentForm.status = "pending";
  showIncidentForm.value = true;
};

const closeIncidentForm = () => {
  if (savingIncident.value) return;
  showIncidentForm.value = false;
  editingIncidentEventId.value = "";
};

const openTaskForm = () => {
  taskForm.title = "";
  taskForm.description = "";
  taskForm.planned_date = toDateKey(new Date());
  taskForm.planned_start_time = "";
  taskForm.estimated_duration_hours = "";
  taskForm.assigned_user_id = "";
  taskForm.priority = "medium";
  taskForm.event_type = "task";
  showTaskForm.value = true;
};

const openInspectionForm = () => {
  editingInspectionEventId.value = "";
  inspectionForm.title = "";
  inspectionForm.description = "";
  inspectionForm.planned_date = toDateKey(new Date());
  inspectionForm.planned_start_time = "";
  inspectionForm.estimated_duration_hours = "";
  inspectionForm.assigned_user_id = "";
  inspectionForm.priority = "medium";
  inspectionForm.result = "in_progress";
  inspectionForm.comments = "";
  inspectionForm.requires_follow_up = false;
  inspectionForm.close_event = false;
  inspectionForm.checklist = [{
    id: "main",
    label: "",
    status: "pending",
    observations: "",
    requires_action: false,
  }];
  showInspectionForm.value = true;
};

const closeInspectionForm = () => {
  if (savingInspection.value) return;
  showInspectionForm.value = false;
  editingInspectionEventId.value = "";
};

const addInspectionChecklistItem = () => {
  inspectionForm.checklist.push({
    id: `manual-${Date.now()}-${inspectionForm.checklist.length + 1}`,
    label: "",
    status: "pending",
    observations: "",
    requires_action: false,
  });
};

const removeInspectionChecklistItem = (index: number) => {
  inspectionForm.checklist.splice(index, 1);
  if (!inspectionForm.checklist.length) addInspectionChecklistItem();
};

const closeTaskForm = () => {
  if (savingTask.value) return;
  showTaskForm.value = false;
};

const resetAssemblyForm = () => {
  editingAssemblyId.value = "";
  assemblyForm.title = "";
  assemblyForm.description = "";
  assemblyForm.scheduled_date = toDateKey(new Date());
  assemblyForm.scheduled_start_time = "";
  assemblyForm.estimated_duration_hours = "";
  assemblyForm.location = "";
  assemblyForm.modality = "presential";
  assemblyForm.assembly_type = "ordinary";
  assemblyForm.status = "scheduled";
  assemblyForm.attendees = [{ name: "", email: "", role: "", attendance_status: "expected" }];
  assemblyForm.agenda_items = [{ id: "point-1", title: "", description: "", owner: "", conclusion: "", status: "pending" }];
  assemblyForm.conclusions = "";
};

const openAssemblyForm = () => {
  resetAssemblyForm();
  showAssemblyForm.value = true;
};

const closeAssemblyForm = () => {
  if (savingAssembly.value) return;
  showAssemblyForm.value = false;
  editingAssemblyId.value = "";
};

const addAssemblyAttendee = () => {
  assemblyForm.attendees.push({ name: "", email: "", role: "", attendance_status: "expected" });
};

const removeAssemblyAttendee = (index: number) => {
  assemblyForm.attendees.splice(index, 1);
  if (!assemblyForm.attendees.length) addAssemblyAttendee();
};

const addAssemblyPoint = () => {
  assemblyForm.agenda_items.push({
    id: `point-${Date.now()}-${assemblyForm.agenda_items.length + 1}`,
    title: "",
    description: "",
    owner: "",
    conclusion: "",
    status: "pending",
  });
};

const removeAssemblyPoint = (index: number) => {
  assemblyForm.agenda_items.splice(index, 1);
  if (!assemblyForm.agenda_items.length) addAssemblyPoint();
};

const openIncidentEdit = (event: OperationalEvent) => {
  editingIncidentEventId.value = event.id;
  incidentForm.title = event.title || "";
  incidentForm.description = event.description || "";
  incidentForm.planned_date = event.planned_date;
  incidentForm.planned_start_time = event.planned_start_time || "";
  incidentForm.estimated_duration_hours = event.estimated_duration_hours ? String(event.estimated_duration_hours) : "";
  incidentForm.assigned_user_id = event.assigned_user_id || "";
  incidentForm.priority = event.priority || "medium";
  incidentForm.status = event.status || "pending";
  showIncidentForm.value = true;
};

const openAssemblyEdit = async (event: OperationalEvent) => {
  if (!event.source_id) {
    openGenericEditEvent(event);
    return;
  }
  errorMessage.value = "";
  try {
    const detail = await request<AssemblyDetail>(`/api/v1/portal/assemblies/${event.source_id}`);
    editingAssemblyId.value = detail.id;
    assemblyForm.title = detail.title || "";
    assemblyForm.description = detail.description || "";
    assemblyForm.scheduled_date = detail.scheduled_date;
    assemblyForm.scheduled_start_time = detail.scheduled_start_time || "";
    assemblyForm.estimated_duration_hours = detail.estimated_duration_hours ? String(detail.estimated_duration_hours) : "";
    assemblyForm.location = detail.location || "";
    assemblyForm.modality = detail.modality || "presential";
    assemblyForm.assembly_type = detail.assembly_type || "ordinary";
    assemblyForm.status = detail.status || "scheduled";
    assemblyForm.attendees = detail.attendees?.length
      ? detail.attendees.map((item) => ({
          name: item.name || "",
          email: item.email || "",
          role: item.role || "",
          attendance_status: item.attendance_status || "expected",
        }))
      : [{ name: "", email: "", role: "", attendance_status: "expected" }];
    assemblyForm.agenda_items = detail.agenda_items?.length
      ? detail.agenda_items.map((item, index) => ({
          id: item.id || `point-${index + 1}`,
          title: item.title || "",
          description: item.description || "",
          owner: item.owner || "",
          conclusion: item.conclusion || "",
          status: item.status || "pending",
        }))
      : [{ id: "point-1", title: "", description: "", owner: "", conclusion: "", status: "pending" }];
    assemblyForm.conclusions = detail.conclusions || "";
    showAssemblyForm.value = true;
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const openInspectionEdit = async (event: OperationalEvent) => {
  errorMessage.value = "";
  try {
    const detail = await request<InspectionDetail>(`/api/v1/portal/inspections/${event.id}`);
    editingInspectionEventId.value = event.id;
    inspectionForm.title = detail.title || event.title || "";
    inspectionForm.description = detail.description || event.description || "";
    inspectionForm.planned_date = detail.planned_date || event.planned_date;
    inspectionForm.planned_start_time = detail.planned_start_time || event.planned_start_time || "";
    inspectionForm.estimated_duration_hours = detail.estimated_duration_hours ? String(detail.estimated_duration_hours) : "";
    inspectionForm.assigned_user_id = detail.assigned_user_id || event.assigned_user_id || "";
    inspectionForm.priority = detail.priority || event.priority || "medium";
    inspectionForm.result = detail.execution?.result || (detail.status === "completed" ? "conforme" : "in_progress");
    inspectionForm.comments = detail.execution?.comments || "";
    inspectionForm.requires_follow_up = Boolean(detail.execution?.requires_follow_up);
    inspectionForm.close_event = detail.status === "completed";
    inspectionForm.checklist = (detail.execution?.checklist?.length ? detail.execution.checklist : [{
      id: "main",
      label: detail.title || event.title,
      status: "pending",
      observations: "",
      requires_action: false,
    }]).map((item) => ({ ...item }));
    showInspectionForm.value = true;
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const openGenericEditEvent = (event: OperationalEvent) => {
  editForm.id = event.id;
  editForm.title = event.title || "";
  editForm.description = event.description || "";
  editForm.planned_date = event.planned_date;
  editForm.planned_start_time = event.planned_start_time || "";
  editForm.estimated_duration_hours = event.estimated_duration_hours ? String(event.estimated_duration_hours) : "";
  editForm.assigned_user_id = event.assigned_user_id || "";
  editForm.priority = event.priority || "medium";
  editForm.status = event.status || "pending";
  editForm.event_type = event.event_type || "task";
  showEditForm.value = true;
};

const openEditEvent = (event: OperationalEvent) => {
  if (isAssemblyEvent(event)) {
    void openAssemblyEdit(event);
    return;
  }
  if (isUnplannedIncident(event)) {
    openIncidentEdit(event);
    return;
  }
  if (isInspectionEvent(event)) {
    void openInspectionEdit(event);
    return;
  }
  openGenericEditEvent(event);
};

const closeEditEvent = () => {
  if (savingEdit.value) return;
  showEditForm.value = false;
};

const editEventTitle = computed(() => {
  if (editForm.event_type === "inspection") return "Editar inspeccion";
  if (editForm.event_type === "maintenance") return "Editar mantencion";
  if (editForm.event_type === "administrative") return "Editar tarea administrativa";
  if (editForm.event_type === "meeting") return "Editar reunion";
  return "Editar tarea";
});

const updateEditedEvent = async () => {
  if (!editForm.id || !editForm.title.trim()) {
    errorMessage.value = "Indica el título de la tarea.";
    return;
  }
  savingEdit.value = true;
  errorMessage.value = "";
  try {
    const updated = await request<OperationalEvent>(`/api/v1/portal/operational-plan/events/${editForm.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: editForm.title.trim(),
        description: editForm.description.trim() || null,
        planned_date: editForm.planned_date,
        planned_start_time: editForm.planned_start_time || null,
        estimated_duration_hours: optionalNumber(editForm.estimated_duration_hours),
        assigned_user_id: editForm.assigned_user_id || null,
        priority: editForm.priority,
        status: editForm.status,
        event_type: editForm.event_type,
      }),
    });
    replaceEvent(updated);
    showEditForm.value = false;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingEdit.value = false;
  }
};

const addCreatedEventToAgenda = (created: OperationalEvent) => {
  events.value = [...events.value, created].sort((left, right) => {
    const dateCompare = left.planned_date.localeCompare(right.planned_date);
    return dateCompare || left.title.localeCompare(right.title);
  });
  summary.total += 1;
  summary.pending += 1;
  selectedYear.value = Number(created.planned_date.slice(0, 4));
  selectedMonth.value = String(Number(created.planned_date.slice(5, 7)));
  const createdDate = new Date(`${created.planned_date}T00:00:00`);
  const mondayOffset = (createdDate.getDay() + 6) % 7;
  createdDate.setDate(createdDate.getDate() - mondayOffset);
  selectedWeekStart.value = createdDate;
};

const createManualTask = async () => {
  if (!taskForm.title.trim()) {
    errorMessage.value = "Indica el título de la tarea.";
    return;
  }
  savingTask.value = true;
  errorMessage.value = "";
  try {
    if (taskForm.event_type === "assembly") {
      const created = await request<{ event?: OperationalEvent }>("/api/v1/portal/assemblies/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: taskForm.title.trim(),
          description: taskForm.description.trim() || null,
          assembly_type: "ordinary",
          status: "scheduled",
          scheduled_date: taskForm.planned_date,
          scheduled_start_time: taskForm.planned_start_time || null,
          estimated_duration_hours: optionalNumber(taskForm.estimated_duration_hours),
          location: null,
          modality: "presential",
          attendees: [],
          agenda_items: [],
          conclusions: null,
        }),
      });
      if (created.event) addCreatedEventToAgenda(created.event);
      else await loadPlan();
    } else if (taskForm.event_type === "incident") {
      const created = await request<OperationalEvent>("/api/v1/portal/operational-plan/unplanned-incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: taskForm.title.trim(),
          description: taskForm.description.trim() || null,
          planned_date: taskForm.planned_date,
          planned_start_time: taskForm.planned_start_time || null,
          estimated_duration_hours: optionalNumber(taskForm.estimated_duration_hours),
          assigned_user_id: taskForm.assigned_user_id || null,
          priority: taskForm.priority,
        }),
      });
      addCreatedEventToAgenda(created);
    } else {
      const created = await request<OperationalEvent>("/api/v1/portal/operational-plan/manual-tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: taskForm.title.trim(),
          description: taskForm.description.trim() || null,
          planned_date: taskForm.planned_date,
          planned_start_time: taskForm.planned_start_time || null,
          estimated_duration_hours: optionalNumber(taskForm.estimated_duration_hours),
          assigned_user_id: taskForm.assigned_user_id || null,
          priority: taskForm.priority,
          event_type: taskForm.event_type,
        }),
      });
      addCreatedEventToAgenda(created);
    }
    showTaskForm.value = false;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingTask.value = false;
  }
};

const createInspection = async () => {
  if (!inspectionForm.title.trim()) {
    errorMessage.value = "Indica el título de la inspección.";
    return;
  }
  savingInspection.value = true;
  errorMessage.value = "";
  try {
    const eventPayload = {
      title: inspectionForm.title.trim(),
      description: inspectionForm.description.trim() || null,
      planned_date: inspectionForm.planned_date,
      planned_start_time: inspectionForm.planned_start_time || null,
      estimated_duration_hours: optionalNumber(inspectionForm.estimated_duration_hours),
      assigned_user_id: inspectionForm.assigned_user_id || null,
      priority: inspectionForm.priority,
      event_type: "inspection",
    };
    const savedEvent = editingInspectionEventId.value
      ? await request<OperationalEvent>(`/api/v1/portal/operational-plan/events/${editingInspectionEventId.value}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(eventPayload),
        })
      : await request<OperationalEvent>("/api/v1/portal/operational-plan/manual-tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(eventPayload),
        });
    const checklist = inspectionForm.checklist
      .filter((item) => item.label.trim() || item.observations?.trim())
      .map((item, index) => ({
        id: item.id || `item-${index + 1}`,
        label: item.label.trim() || inspectionForm.title.trim(),
        status: item.status,
        observations: item.observations?.trim() || null,
        requires_action: item.requires_action,
      }));
    await request(`/api/v1/portal/inspections/${savedEvent.id}/execution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        result: inspectionForm.result,
        comments: inspectionForm.comments.trim() || null,
        requires_follow_up: inspectionForm.requires_follow_up,
        close_event: inspectionForm.close_event,
        checklist: checklist.length ? checklist : [{
          id: "main",
          label: inspectionForm.title.trim(),
          status: "pending",
          observations: null,
          requires_action: false,
        }],
      }),
    });
    if (editingInspectionEventId.value) replaceEvent(savedEvent);
    else addCreatedEventToAgenda(savedEvent);
    await loadPlan();
    showInspectionForm.value = false;
    editingInspectionEventId.value = "";
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingInspection.value = false;
  }
};

const createAssembly = async () => {
  if (!assemblyForm.title.trim()) {
    errorMessage.value = "Indica el nombre de la asamblea.";
    return;
  }
  savingAssembly.value = true;
  errorMessage.value = "";
  try {
    const endpoint = editingAssemblyId.value
      ? `/api/v1/portal/assemblies/${editingAssemblyId.value}`
      : "/api/v1/portal/assemblies/";
    const method = editingAssemblyId.value ? "PATCH" : "POST";
    const saved = await request<{ event?: OperationalEvent }>(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: assemblyForm.title.trim(),
        description: assemblyForm.description.trim() || null,
        assembly_type: assemblyForm.assembly_type,
        status: assemblyForm.status,
        scheduled_date: assemblyForm.scheduled_date,
        scheduled_start_time: assemblyForm.scheduled_start_time || null,
        estimated_duration_hours: optionalNumber(assemblyForm.estimated_duration_hours),
        location: assemblyForm.location.trim() || null,
        modality: assemblyForm.modality,
        attendees: assemblyForm.attendees.filter((item) => item.name.trim()).map((item) => ({
          name: item.name.trim(),
          email: item.email.trim() || null,
          role: item.role.trim() || null,
          attendance_status: item.attendance_status,
        })),
        agenda_items: assemblyForm.agenda_items.filter((item) => item.title.trim()).map((item) => ({
          id: item.id,
          title: item.title.trim(),
          description: item.description.trim() || null,
          owner: item.owner.trim() || null,
          conclusion: item.conclusion.trim() || null,
          status: item.status,
        })),
        conclusions: assemblyForm.conclusions.trim() || null,
      }),
    });
    if (saved.event && editingAssemblyId.value) replaceEvent(saved.event);
    else if (saved.event) addCreatedEventToAgenda(saved.event);
    else await loadPlan();
    showAssemblyForm.value = false;
    editingAssemblyId.value = "";
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingAssembly.value = false;
  }
};

const createUnplannedIncident = async () => {
  if (!incidentForm.title.trim()) {
    errorMessage.value = "Indica el título de la incidencia.";
    return;
  }
  savingIncident.value = true;
  errorMessage.value = "";
  try {
    const endpoint = editingIncidentEventId.value
      ? `/api/v1/portal/operational-plan/unplanned-incidents/${editingIncidentEventId.value}`
      : "/api/v1/portal/operational-plan/unplanned-incidents";
    const method = editingIncidentEventId.value ? "PATCH" : "POST";
    const saved = await request<OperationalEvent>(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: incidentForm.title.trim(),
        description: incidentForm.description.trim() || null,
        planned_date: incidentForm.planned_date,
        planned_start_time: incidentForm.planned_start_time || null,
        estimated_duration_hours: optionalNumber(incidentForm.estimated_duration_hours),
        assigned_user_id: incidentForm.assigned_user_id || null,
        priority: incidentForm.priority,
        status: incidentForm.status,
      }),
    });
    if (editingIncidentEventId.value) replaceEvent(saved);
    else addCreatedEventToAgenda(saved);
    showIncidentForm.value = false;
    editingIncidentEventId.value = "";
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    savingIncident.value = false;
  }
};

const formatDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
};

const shortDate = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "short" }).format(new Date(year, month - 1, day));
};

const optionalNumber = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const truncatedCardTitle = (value: string) => {
  const maxLength = 42;
  const clean = value.trim();
  return clean.length > maxLength ? `${clean.slice(0, maxLength).trim()}...` : clean;
};

const toDateKey = (value: Date) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const normalize = (value: string) => value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo cargar el plan operativo.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

const statusLabel = (status: string | null | undefined) => {
  if (status === "pending") return "Pendiente";
  if (status === "in_progress") return "En curso";
  if (status === "completed" || status === "done") return "Completado";
  if (status === "cancelled") return "Cancelado";
  return status || "Sin estado";
};

const statusBadgeClass = (status: string | null | undefined) => {
  if (status === "pending") return "is-pending";
  if (status === "in_progress") return "is-progress";
  if (status === "completed" || status === "done") return "is-active";
  if (status === "cancelled") return "is-inactive";
  return "is-neutral";
};

const priorityLabel = (priority: string | null | undefined) => {
  if (priority === "urgent") return "Urgente";
  if (priority === "high") return "Alta";
  if (priority === "medium") return "Media";
  if (priority === "low") return "Baja";
  return priority || "Sin prioridad";
};

const priorityClass = (priority: string | null | undefined) => {
  if (priority === "urgent") return "is-urgent";
  if (priority === "high") return "is-high";
  if (priority === "low") return "is-low";
  return "is-medium";
};

const profileLabel = (profile: string | null | undefined) => {
  if (profile === "project_manager") return "Project manager";
  if (profile === "supervisor") return "Supervisor";
  if (profile === "ejecutivo" || profile === "executive") return "Ejecutivo/a";
  if (profile === "conserje") return "Conserje";
  return profile || "Sin responsable";
};

const sourceLabel = (sourceType: string | null | undefined) => {
  if (sourceType === "unplanned_incident") return "Incidencia no programada";
  if (sourceType === "manual_task") return "Tarea manual";
  if (sourceType === "maintenance_template") return "Planificada";
  if (sourceType === "inspection_template") return "Planificada";
  return sourceType || "Planificada";
};

const eventTypeLabel = (eventType: string | null | undefined) => {
  if (eventType === "administrative") return "Administrativa";
  if (eventType === "assembly") return "Asamblea";
  if (eventType === "meeting") return "Reunion";
  if (eventType === "inspection") return "Inspeccion";
  if (eventType === "maintenance") return "Mantencion";
  if (eventType === "incident") return "Incidencia";
  return "Generica";
};

const eventFunctionalLabel = (event: OperationalEvent) => {
  if (event.event_type) return eventTypeLabel(event.event_type);
  if (event.source_type === "unplanned_incident") return "Incidencia no programada";
  return eventTypeLabel(event.event_type);
};

const isUnplannedIncident = (event: OperationalEvent) => event.event_type ? event.event_type === "incident" : event.source_type === "unplanned_incident";
const isAssemblyEvent = (event: OperationalEvent) => event.event_type === "assembly" || event.source_type === "assembly";
const isInspectionEvent = (event: OperationalEvent) => event.event_type === "inspection";
const isManualTask = (event: OperationalEvent) => event.source_type === "manual_task";

const staffOptionLabel = (member: OperationalStaff) => {
  const profile = profileLabel(member.portal_profile);
  const position = member.responsibility ? ` · ${member.responsibility}` : "";
  return `${member.full_name} · ${profile}${position}`;
};

const assigneeLabel = (event: OperationalEvent) => event.assigned_user_name || "Sin persona asignada";

watch([selectedYear, selectedMonth, selectedStatus], loadPlan);
watch([() => activeCondominium.value?.id, token], loadPlan);
onMounted(loadPlan);
</script>

<template>
  <section class="panel operational-panel">
    <div class="dashboard-hero operational-hero">
      <div>
        <p class="eyebrow">Agenda operativa</p>
        <h2>Plan operativo del condominio</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary operational-summary">
        <article>
          <span>Total</span>
          <strong>{{ summary.total }}</strong>
        </article>
        <article>
          <span>Pendientes</span>
          <strong>{{ summary.pending }}</strong>
        </article>
        <article class="is-overdue">
          <span>Vencidos</span>
          <strong>{{ summary.overdue }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
    <p v-if="externalOrderMessage" class="form-success result-message">{{ externalOrderMessage }}</p>

    <div class="operational-toolbar">
      <label>
        Año
        <select v-model.number="selectedYear" @change="resetWeekSelection">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
        </select>
      </label>
      <label>
        Mes
        <select v-model="selectedMonth" @change="resetWeekSelection">
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
        <input v-model="search" type="search" placeholder="Buscar tarea, sección o responsable" />
      </label>
      <button class="button ghost" type="button" :disabled="loading" @click="loadPlan">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <div class="operational-view-row">
      <div class="view-toggle" role="group" aria-label="Vista de agenda">
        <button class="button compact" :class="agendaView === 'list' ? 'navy' : 'ghost'" type="button" @click="agendaView = 'list'">
          <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
          <span>Listado</span>
        </button>
        <button class="button compact" :class="agendaView === 'week' ? 'navy' : 'ghost'" type="button" @click="agendaView = 'week'">
          <svg class="icon" aria-hidden="true"><use href="#icon-calendar" /></svg>
          <span>Semana</span>
        </button>
      </div>
      <div class="operational-actions">
        <button class="button assembly-action" type="button" @click="openAssemblyForm">
          <svg class="icon" aria-hidden="true"><use href="#icon-users" /></svg>
          <span>Nueva asamblea</span>
        </button>
        <button class="button inspection-action" type="button" @click="openInspectionForm">
          <svg class="icon" aria-hidden="true"><use href="#icon-clipboard" /></svg>
          <span>Nueva inspeccion</span>
        </button>
        <button class="button manual-task-action" type="button" @click="openTaskForm">
          <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
          <span>Nueva tarea</span>
        </button>
        <button class="button incident-action" type="button" @click="openIncidentForm">
          <svg class="icon" aria-hidden="true"><use href="#icon-alert" /></svg>
          <span>Nueva incidencia</span>
        </button>
      </div>
    </div>

    <div class="week-navigation">
      <button class="button ghost compact" type="button" @click="moveWeek(-1)">
        <svg class="icon" aria-hidden="true"><use href="#icon-chevron-left" /></svg>
        <span>Semana anterior</span>
      </button>
      <strong>{{ weekRangeLabel }}</strong>
      <button class="button ghost compact" type="button" @click="goToCurrentWeek">
        <svg class="icon" aria-hidden="true"><use href="#icon-calendar" /></svg>
        <span>Semana actual</span>
      </button>
      <button class="button ghost compact" type="button" @click="moveWeek(1)">
        <span>Semana siguiente</span>
        <svg class="icon" aria-hidden="true"><use href="#icon-chevron-right" /></svg>
      </button>
    </div>

    <div class="metrics-grid operational-metrics">
      <article class="metric"><span>En curso</span><strong>{{ summary.in_progress }}</strong><small>Actualmente gestionándose</small></article>
      <article class="metric"><span>Completados</span><strong>{{ summary.completed }}</strong><small>Eventos cerrados</small></article>
      <article class="metric"><span>Mostrados</span><strong>{{ visibleEvents.length }}</strong><small>Tras aplicar búsqueda</small></article>
      <article class="metric"><span>Condominio</span><strong class="metric-name">{{ activeCondominium?.name || "Sin contexto" }}</strong><small>Contexto activo</small></article>
    </div>

    <div v-if="agendaView === 'week'" class="week-board" aria-label="Vista semanal de agenda operativa">
      <section v-for="day in weekDays" :key="day.dateKey" class="week-column">
        <header>
          <span>{{ day.label }}</span>
          <strong>{{ day.day }}</strong>
        </header>
        <div
          class="week-column-body"
          :class="{ 'is-drop-target': dragOverDate === day.dateKey }"
          @dragover.prevent="setDropTarget(day.dateKey)"
          @dragleave="dragOverDate === day.dateKey && (dragOverDate = '')"
          @drop.prevent="dropEventOnPosition(day.dateKey)"
        >
          <div
            v-for="(event, index) in day.items"
            :key="event.id"
            class="week-card-wrap"
          >
            <div
              class="week-drop-zone is-between"
              :class="{ 'is-active': dragTargetKey === `${day.dateKey}:${event.id}` }"
              @dragover.prevent.stop="setDropTarget(day.dateKey, event.id)"
              @drop.prevent.stop="dropEventOnPosition(day.dateKey, event.id)"
            ></div>
            <article
              class="week-task-card"
              :class="{ 'is-unplanned': isUnplannedIncident(event), 'is-manual': isManualTask(event), 'is-assembly': isAssemblyEvent(event), 'is-inspection': isInspectionEvent(event) }"
              draggable="true"
              @dragstart="startEventDrag($event, event)"
              @dragend="endEventDrag"
              @dragover.prevent.stop="setCardDropTarget($event, day.dateKey, day.items, index)"
              @drop.prevent.stop="dropEventOnCard($event, day.dateKey, day.items, index)"
              @click="openEditEvent(event)"
            >
              <div class="week-card-actions">
                <button
                  class="week-card-action is-provider"
                  type="button"
                  :disabled="creatingExternalOrderId === event.id"
                  aria-label="Crear link proveedor"
                  title="Crear link proveedor"
                  @click.stop="openExternalOrderForm(event)"
                >
                  <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
                </button>
                <button
                  class="week-card-action is-remove"
                  type="button"
                  :disabled="deletingEventId === event.id"
                  aria-label="Eliminar de la agenda"
                  title="Eliminar de la agenda"
                  @click.stop="openDeleteEvent(event)"
                >
                  <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
                </button>
              </div>
              <h3>{{ truncatedCardTitle(event.title) }}</h3>
              <span class="status-badge week-status" :class="statusBadgeClass(event.status)">
                <span aria-hidden="true"></span>
                {{ statusLabel(event.status) }}
              </span>
              <p v-if="isUnplannedIncident(event)" class="week-source">{{ eventFunctionalLabel(event) }}</p>
              <p class="week-condominium">{{ activeCondominium?.name || "Sin condominio" }}</p>
              <p class="week-assignee" :title="assigneeLabel(event)">{{ assigneeLabel(event) }}</p>
              <div class="week-move-actions">
                <button
                  v-if="canSendToPreviousWeek"
                  class="week-card-action is-previous-week"
                  type="button"
                  :disabled="deletingEventId === event.id"
                  aria-label="Enviar a la semana anterior"
                  :title="weekMoveTitle(-1)"
                  @click.stop="sendEventToPreviousWeek(event)"
                >
                  <svg class="icon" aria-hidden="true"><use href="#icon-chevrons-left" /></svg>
                </button>
                <button
                  class="week-card-action is-next-week"
                  type="button"
                  :disabled="deletingEventId === event.id"
                  aria-label="Enviar a la proxima semana"
                  :title="weekMoveTitle(1)"
                  @click.stop="sendEventToNextWeek(event)"
                >
                  <svg class="icon" aria-hidden="true"><use href="#icon-chevrons-right" /></svg>
                </button>
              </div>
            </article>
          </div>
          <div
            class="week-drop-zone"
            :class="{ 'is-active': dragTargetKey === `${day.dateKey}:end` }"
            @dragover.prevent.stop="setDropTarget(day.dateKey)"
            @drop.prevent.stop="dropEventOnPosition(day.dateKey)"
          ></div>
          <p v-if="!day.items.length && !draggingEventId" class="week-empty">Sin tareas</p>
        </div>
      </section>
    </div>

    <div v-else-if="groupedEvents.length" class="operational-agenda">
      <section v-for="group in groupedEvents" :key="group.dateKey" class="operational-day">
        <header>
          <div>
            <span>{{ shortDate(group.dateKey) }}</span>
            <h3>{{ formatDate(group.dateKey) }}</h3>
          </div>
          <strong>{{ group.items.length }} eventos</strong>
        </header>
        <div class="operational-events">
          <article
            v-for="event in group.items"
            :key="event.id"
            class="operational-event"
            :class="{ 'is-manual': isManualTask(event), 'is-unplanned': isUnplannedIncident(event), 'is-assembly': isAssemblyEvent(event), 'is-inspection': isInspectionEvent(event) }"
            @click="openEditEvent(event)"
          >
            <div class="event-date-dot" aria-hidden="true"></div>
            <div class="event-content">
              <div class="event-title-row">
                <div>
                  <p class="event-section">{{ eventFunctionalLabel(event) }} · {{ event.section_name || "Sin sección" }}</p>
                  <h3>{{ event.title }}</h3>
                </div>
                <div class="event-row-right">
                  <span class="status-badge" :class="statusBadgeClass(event.status)">
                    <span aria-hidden="true"></span>
                    {{ statusLabel(event.status) }}
                  </span>
                  <div class="event-row-actions">
                    <button
                      class="week-card-action is-provider"
                      type="button"
                      :disabled="creatingExternalOrderId === event.id"
                      aria-label="Crear link proveedor"
                      title="Crear link proveedor"
                      @click.stop="openExternalOrderForm(event)"
                    >
                      <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
                    </button>
                    <button
                      v-if="canSendToPreviousWeek"
                      class="week-card-action is-previous-week"
                      type="button"
                      :disabled="deletingEventId === event.id"
                      aria-label="Enviar a la semana anterior"
                      :title="weekMoveTitle(-1)"
                      @click.stop="sendEventToPreviousWeek(event)"
                    >
                      <svg class="icon" aria-hidden="true"><use href="#icon-chevrons-left" /></svg>
                    </button>
                    <button
                      class="week-card-action is-next-week"
                      type="button"
                      :disabled="deletingEventId === event.id"
                      aria-label="Enviar a la próxima semana"
                      :title="weekMoveTitle(1)"
                      @click.stop="sendEventToNextWeek(event)"
                    >
                      <svg class="icon" aria-hidden="true"><use href="#icon-chevrons-right" /></svg>
                    </button>
                    <button
                      class="week-card-action is-remove"
                      type="button"
                      :disabled="deletingEventId === event.id"
                      aria-label="Eliminar de la agenda"
                      title="Eliminar de la agenda"
                      @click.stop="openDeleteEvent(event)"
                    >
                      <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
                    </button>
                  </div>
                </div>
              </div>
              <p v-if="event.description" class="event-description">{{ event.description }}</p>
              <div class="event-meta">
                <span v-if="event.asset_name">
                  <svg class="icon" aria-hidden="true"><use href="#icon-building" /></svg>
                  {{ event.asset_name }}
                </span>
                <span>
                  <svg class="icon" aria-hidden="true"><use href="#icon-users" /></svg>
                  {{ profileLabel(event.assigned_profile) }}
                </span>
                <label class="event-assignee" @click.stop>
                  <svg class="icon" aria-hidden="true"><use href="#icon-user" /></svg>
                  <select
                    :value="event.assigned_user_id || ''"
                    :disabled="savingAssignment === event.id || !staff.length"
                    :title="event.assigned_user_name || 'Asignar responsable'"
                    @change="assignEvent(event, ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="">Sin persona asignada</option>
                    <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                      {{ staffOptionLabel(member) }}
                    </option>
                  </select>
                </label>
                <span class="priority-pill" :class="priorityClass(event.priority)">
                  {{ priorityLabel(event.priority) }}
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-calendar" /></svg>
      </span>
      <h2>Sin eventos operativos</h2>
      <p class="placeholder-copy">Genera la planificación desde el plan de mantenciones para visualizarla aquí.</p>
    </div>
    <div v-if="showEditForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="edit-event-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="updateEditedEvent">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Agenda operativa</p>
            <h2 id="edit-event-title">{{ editEventTitle }}</h2>
            <p class="placeholder-copy">Actualiza la planificacion, responsable o estado de esta tarjeta.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="savingEdit" title="Cerrar" @click="closeEditEvent">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label class="span-two">
            Titulo
            <input v-model="editForm.title" type="text" maxlength="180" required />
          </label>
          <label>
            Fecha
            <input v-model="editForm.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="editForm.planned_start_time" type="time" />
          </label>
          <label>
            Duración estimada (horas)
            <input v-model="editForm.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 0.5" />
          </label>
          <label>
            Prioridad
            <select v-model="editForm.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label v-if="editForm.event_type === 'assembly'">
            Tipo
            <input value="Asamblea" type="text" disabled />
          </label>
          <label v-else>
            Tipo
            <select v-model="editForm.event_type">
              <option v-for="[value, label] in eventTypeOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label>
            Estado
            <select v-model="editForm.status">
              <option value="pending">Pendiente</option>
              <option value="in_progress">En curso</option>
              <option value="completed">Completado</option>
              <option value="cancelled">Cancelado</option>
            </select>
          </label>
          <label class="span-two">
            Responsable
            <select v-model="editForm.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label class="wide-field">
            Descripcion
            <textarea v-model="editForm.description" rows="4"></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingEdit" @click="closeEditEvent">
            Cancelar
          </button>
          <button class="button navy" type="submit" :disabled="savingEdit">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingEdit ? "Guardando..." : "Guardar cambios" }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="showIncidentForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="incident-form-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="createUnplannedIncident">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Agenda operativa</p>
            <h2 id="incident-form-title">{{ editingIncidentEventId ? "Editar incidencia" : "Nueva incidencia no programada" }}</h2>
            <p class="placeholder-copy">Se añadirá como tarea pendiente dentro de la planificación del condominio activo.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="savingIncident" title="Cerrar" @click="closeIncidentForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label>
            Título
            <input v-model="incidentForm.title" type="text" maxlength="180" placeholder="Ej. Fuga de agua en sala de bombas" required />
          </label>
          <label>
            Fecha
            <input v-model="incidentForm.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="incidentForm.planned_start_time" type="time" />
          </label>
          <label>
            Duración estimada (horas)
            <input v-model="incidentForm.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 0.5" />
          </label>
          <label>
            Prioridad
            <select v-model="incidentForm.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label v-if="editingIncidentEventId">
            Estado
            <select v-model="incidentForm.status">
              <option value="pending">Pendiente</option>
              <option value="in_progress">En curso</option>
              <option value="completed">Completado</option>
              <option value="cancelled">Cancelado</option>
            </select>
          </label>
          <label>
            Responsable
            <select v-model="incidentForm.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="incidentForm.description" rows="4" placeholder="Describe brevemente qué ocurrió y qué se necesita resolver."></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingIncident" @click="closeIncidentForm">
            Cancelar
          </button>
          <button class="button incident-action" type="submit" :disabled="savingIncident">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingIncident ? "Guardando..." : (editingIncidentEventId ? "Guardar cambios" : "Añadir a la agenda") }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="showInspectionForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="inspection-form-title">
      <form class="confirm-modal inspection-execution-modal" @submit.prevent="createInspection">
        <div class="inspection-modal-header">
          <div>
            <p class="eyebrow">Inspeccion</p>
            <h2 id="inspection-form-title">{{ editingInspectionEventId ? "Editar inspeccion" : "Nueva inspeccion" }}</h2>
            <p class="placeholder-copy">Registra la inspeccion con su responsable, resultado y checklist de revision.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="savingInspection" title="Cerrar" @click="closeInspectionForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label class="span-two">
            Titulo
            <input v-model="inspectionForm.title" type="text" maxlength="180" placeholder="Ej. Revisar sala de bombas" required />
          </label>
          <label>
            Fecha
            <input v-model="inspectionForm.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="inspectionForm.planned_start_time" type="time" />
          </label>
          <label>
            Duracion estimada (horas)
            <input v-model="inspectionForm.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 0.5" />
          </label>
          <label>
            Prioridad
            <select v-model="inspectionForm.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label>
            Responsable
            <select v-model="inspectionForm.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label>
            Resultado
            <select v-model="inspectionForm.result">
              <option v-for="[value, label] in inspectionResultOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label class="switch-field inspection-switch">
            <input v-model="inspectionForm.requires_follow_up" type="checkbox" />
            <span>Requiere seguimiento</span>
          </label>
          <label class="switch-field inspection-switch">
            <input v-model="inspectionForm.close_event" type="checkbox" />
            <span>Cerrar inspeccion</span>
          </label>
          <label class="wide-field">
            Descripcion
            <textarea v-model="inspectionForm.description" rows="3" placeholder="Describe brevemente que debe revisarse."></textarea>
          </label>
          <label class="wide-field">
            Observaciones generales
            <textarea v-model="inspectionForm.comments" rows="3" placeholder="Resumen de lo revisado, hallazgos o proximos pasos."></textarea>
          </label>
        </div>

        <section class="inspection-checklist">
          <div class="inspection-checklist-header">
            <h3>Checklist</h3>
            <button class="button ghost" type="button" @click="addInspectionChecklistItem">
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Agregar item</span>
            </button>
          </div>
          <article v-for="(item, index) in inspectionForm.checklist" :key="item.id" class="inspection-checklist-item">
            <label>
              Item
              <input v-model="item.label" type="text" :placeholder="index === 0 ? inspectionForm.title || 'Punto a revisar' : 'Punto a revisar'" />
            </label>
            <label>
              Estado
              <select v-model="item.status">
                <option v-for="[value, label] in checklistStatusOptions" :key="value" :value="value">{{ label }}</option>
              </select>
            </label>
            <label class="switch-field inspection-switch">
              <input v-model="item.requires_action" type="checkbox" />
              <span>Accion requerida</span>
            </label>
            <label class="wide-field">
              Observaciones
              <textarea v-model="item.observations" rows="2" placeholder="Detalle del hallazgo, si aplica."></textarea>
            </label>
            <button class="button danger icon-only" type="button" title="Quitar item" @click="removeInspectionChecklistItem(index)">
              <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
            </button>
          </article>
        </section>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingInspection" @click="closeInspectionForm">Cancelar</button>
          <button class="button inspection-action" type="submit" :disabled="savingInspection">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingInspection ? "Guardando..." : (editingInspectionEventId ? "Guardar inspeccion" : "Anadir inspeccion") }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="showTaskForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="task-form-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="createManualTask">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Agenda operativa</p>
            <h2 id="task-form-title">{{ taskForm.event_type === "inspection" ? "Nueva inspeccion" : "Nueva tarea" }}</h2>
            <p class="placeholder-copy">Se añadirá como tarea pendiente dentro de la planificación del condominio activo.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="savingTask" title="Cerrar" @click="closeTaskForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label>
            Título
            <input v-model="taskForm.title" type="text" maxlength="180" placeholder="Ej. Revisar sala de bombas" required />
          </label>
          <label>
            Fecha
            <input v-model="taskForm.planned_date" type="date" required />
          </label>
          <label>
            Hora estimada
            <input v-model="taskForm.planned_start_time" type="time" />
          </label>
          <label>
            Duración estimada (horas)
            <input v-model="taskForm.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 0.5" />
          </label>
          <label>
            Prioridad
            <select v-model="taskForm.priority">
              <option value="low">Baja</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </select>
          </label>
          <label>
            Tipo
            <select v-model="taskForm.event_type">
              <option v-for="[value, label] in eventTypeOptions" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label>
            Responsable
            <select v-model="taskForm.assigned_user_id">
              <option value="">Sin persona asignada</option>
              <option v-for="member in staff" :key="member.user_id" :value="member.user_id">
                {{ staffOptionLabel(member) }}
              </option>
            </select>
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="taskForm.description" rows="4" placeholder="Describe brevemente qué debe realizarse."></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingTask" @click="closeTaskForm">
            Cancelar
          </button>
          <button class="button navy" type="submit" :disabled="savingTask">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingTask ? "Guardando..." : "Añadir a la agenda" }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="showAssemblyForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="assembly-form-title">
      <form class="confirm-modal assembly-modal" @submit.prevent="createAssembly">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Agenda operativa</p>
            <h2 id="assembly-form-title">{{ editingAssemblyId ? "Editar asamblea" : "Nueva asamblea" }}</h2>
            <p class="placeholder-copy">Se creará como entidad de asamblea y quedará visible en la agenda del condominio activo.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="savingAssembly" title="Cerrar" @click="closeAssemblyForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <label class="span-two">
            Nombre
            <input v-model="assemblyForm.title" type="text" maxlength="180" placeholder="Ej. Asamblea ordinaria de copropietarios" required />
          </label>
          <label>
            Fecha
            <input v-model="assemblyForm.scheduled_date" type="date" required />
          </label>
          <label>
            Hora
            <input v-model="assemblyForm.scheduled_start_time" type="time" />
          </label>
          <label>
            Tipo
            <select v-model="assemblyForm.assembly_type">
              <option value="ordinary">Ordinaria</option>
              <option value="extraordinary">Extraordinaria</option>
              <option value="committee">Comité</option>
              <option value="informative">Informativa</option>
            </select>
          </label>
          <label>
            Modalidad
            <select v-model="assemblyForm.modality">
              <option value="presential">Presencial</option>
              <option value="online">Online</option>
              <option value="hybrid">Híbrida</option>
            </select>
          </label>
          <label>
            Estado
            <select v-model="assemblyForm.status">
              <option value="scheduled">Programada</option>
              <option value="in_progress">En curso</option>
              <option value="closed">Cerrada</option>
              <option value="cancelled">Cancelada</option>
            </select>
          </label>
          <label>
            Duración estimada (horas)
            <input v-model="assemblyForm.estimated_duration_hours" type="number" min="0.25" step="0.25" placeholder="Ej. 1.5" />
          </label>
          <label>
            Lugar
            <input v-model="assemblyForm.location" type="text" maxlength="180" placeholder="Ej. Salón multiuso" />
          </label>
          <label class="wide-field">
            Descripción
            <textarea v-model="assemblyForm.description" rows="3"></textarea>
          </label>
        </div>

        <section class="assembly-editor-block">
          <div class="section-heading-row">
            <div>
              <h3>Asistentes</h3>
              <p class="placeholder-copy">Registra convocados o asistentes principales.</p>
            </div>
            <button class="button ghost compact" type="button" @click="addAssemblyAttendee">
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Agregar</span>
            </button>
          </div>
          <div class="assembly-list-editor">
            <div v-for="(attendee, index) in assemblyForm.attendees" :key="index" class="assembly-inline-row">
              <input v-model="attendee.name" type="text" placeholder="Nombre" />
              <input v-model="attendee.email" type="email" placeholder="Email" />
              <input v-model="attendee.role" type="text" placeholder="Rol / unidad" />
              <select v-model="attendee.attendance_status">
                <option value="expected">Convocado</option>
                <option value="present">Presente</option>
                <option value="absent">Ausente</option>
                <option value="represented">Representado</option>
              </select>
              <button class="button danger compact icon-action" type="button" title="Quitar asistente" @click="removeAssemblyAttendee(index)">
                <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
              </button>
            </div>
          </div>
        </section>

        <section class="assembly-editor-block">
          <div class="section-heading-row">
            <div>
              <h3>Puntos a tratar</h3>
              <p class="placeholder-copy">Después podrás completar conclusiones y generar el resumen PDF.</p>
            </div>
            <button class="button ghost compact" type="button" @click="addAssemblyPoint">
              <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
              <span>Agregar</span>
            </button>
          </div>
          <div class="assembly-list-editor">
            <div v-for="(point, index) in assemblyForm.agenda_items" :key="point.id || index" class="assembly-point-row">
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
              <button class="button danger compact icon-action" type="button" title="Quitar punto" @click="removeAssemblyPoint(index)">
                <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
              </button>
            </div>
          </div>
        </section>

        <label>
          Conclusiones generales
          <textarea v-model="assemblyForm.conclusions" rows="3"></textarea>
        </label>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingAssembly" @click="closeAssemblyForm">
            Cancelar
          </button>
          <button class="button navy" type="submit" :disabled="savingAssembly">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ savingAssembly ? "Guardando..." : "Crear asamblea" }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="showExternalOrderForm" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="external-order-title">
      <form class="confirm-modal operational-incident-modal" @submit.prevent="createExternalServiceOrder">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Proveedor externo</p>
            <h2 id="external-order-title">Crear link de servicio</h2>
            <p class="placeholder-copy">El proveedor abrira un formulario publico para informar el trabajo realizado sin entrar al portal.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="savingExternalOrder" title="Cerrar" @click="closeExternalOrderForm">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>

        <div class="entity-form-grid">
          <div class="wide-field external-provider-mode">
            <button
              class="button"
              :class="externalOrderForm.provider_mode === 'registered' ? 'navy' : 'ghost'"
              type="button"
              @click="setExternalProviderMode('registered')"
            >
              Proveedor guardado
            </button>
            <button
              class="button"
              :class="externalOrderForm.provider_mode === 'manual' ? 'navy' : 'ghost'"
              type="button"
              @click="setExternalProviderMode('manual')"
            >
              Proveedor puntual
            </button>
          </div>
          <label v-if="externalOrderForm.provider_mode === 'registered'" class="wide-field">
            Seleccionar proveedor
            <select v-model="externalOrderForm.provider_supplier_id" :disabled="loadingExternalSuppliers">
              <option value="">{{ loadingExternalSuppliers ? "Cargando proveedores..." : "Selecciona un proveedor guardado" }}</option>
              <option v-for="supplier in externalOrderSuppliers" :key="supplier.id" :value="supplier.id">
                {{ supplier.name }}
              </option>
            </select>
            <small v-if="!loadingExternalSuppliers && !externalOrderSuppliers.length" class="form-hint">
              No hay proveedores guardados para este condominio. Puedes usar proveedor puntual.
            </small>
          </label>
          <label>
            Proveedor
            <input v-model="externalOrderForm.provider_name" type="text" maxlength="160" placeholder="Ej. Ascensores Andinos" required />
          </label>
          <label>
            Email proveedor
            <input v-model="externalOrderForm.provider_email" type="email" maxlength="255" placeholder="contacto@proveedor.cl" />
          </label>
          <label>
            Telefono
            <input v-model="externalOrderForm.provider_phone" type="text" maxlength="40" />
          </label>
          <label>
            Vigencia del link
            <select v-model="externalOrderForm.expires_in_days">
              <option value="3">3 dias</option>
              <option value="7">7 dias</option>
              <option value="15">15 dias</option>
              <option value="30">30 dias</option>
            </select>
          </label>
          <label>
            Template IA
            <select v-model="externalOrderForm.prompt_key">
              <option value="vendor_service_report">Informe proveedor externo</option>
              <option value="elevator_inspection_report">Informe revision ascensor</option>
              <option value="operational_report_draft">Informe operativo general</option>
            </select>
          </label>
          <label>
            Titulo
            <input v-model="externalOrderForm.title" type="text" maxlength="180" required />
          </label>
          <label class="wide-field">
            Instrucciones para el proveedor
            <textarea v-model="externalOrderForm.instructions" rows="4"></textarea>
          </label>
          <label v-if="externalOrderForm.public_url" class="wide-field">
            Link generado
            <input v-model="externalOrderForm.public_url" type="text" readonly />
          </label>
          <div v-if="externalOrderForm.public_url" class="wide-field external-order-share">
            <div class="external-order-qr-card">
              <span>QR del link</span>
              <img :src="externalOrderQrUrl" alt="QR del link de servicio" />
            </div>
            <div class="external-order-share-actions">
              <p>El proveedor puede abrir el formulario con el link o escaneando este QR.</p>
              <button class="button ghost" type="button" @click="copyExternalOrderLink">
                Copiar link
              </button>
              <a class="button ghost" :href="externalOrderQrUrl" target="_blank" rel="noopener">
                Abrir QR
              </a>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="savingExternalOrder" @click="closeExternalOrderForm">
            Cerrar
          </button>
          <button class="button navy" type="submit" :disabled="savingExternalOrder">
            <svg class="icon" aria-hidden="true"><use href="#icon-plus" /></svg>
            <span>{{ savingExternalOrder ? "Creando..." : externalOrderForm.public_url ? "Crear nuevo link" : "Crear link" }}</span>
          </button>
        </div>
      </form>
    </div>
    <div v-if="deleteCandidate" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-event-title">
      <div class="confirm-modal">
        <div class="modal-title-row">
          <div>
            <p class="eyebrow">Agenda operativa</p>
            <h2 id="delete-event-title">Eliminar de la planificación</h2>
            <p class="placeholder-copy">
              Se eliminará "{{ deleteCandidate.title }}" de la semana operativa del condominio activo.
            </p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="!!deletingEventId" title="Cerrar" @click="closeDeleteEvent">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </div>
        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="!!deletingEventId" @click="closeDeleteEvent">
            Cancelar
          </button>
          <button class="button danger" type="button" :disabled="!!deletingEventId" @click="confirmDeleteEvent">
            <svg class="icon" aria-hidden="true"><use href="#icon-trash" /></svg>
            <span>{{ deletingEventId ? "Eliminando..." : "Eliminar" }}</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
