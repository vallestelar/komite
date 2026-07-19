<script setup lang="ts">
type OperationalNotification = {
  id: string;
  title: string;
  summary?: string | null;
  body?: string | null;
  draft_body?: string | null;
  final_body?: string | null;
  status: string;
  priority: string;
  send_status: string;
  send_channel: string;
  event_id?: string | null;
  event_title?: string | null;
  external_service_order_id?: string | null;
  provider_name?: string | null;
  provider_email?: string | null;
  provider_phone?: string | null;
  report_id?: string | null;
  ai_request_id?: string | null;
  validated_at?: string | null;
  mobile_payload?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type NotificationListResponse = {
  items: OperationalNotification[];
};

type PreviewInline = {
  text: string;
  bold: boolean;
};

type PreviewBlock =
  | { type: "heading"; level: number; content: PreviewInline[] }
  | { type: "paragraph"; content: PreviewInline[] }
  | { type: "list"; ordered: boolean; items: PreviewInline[][] };

const emit = defineEmits<{
  changed: [];
}>();

const config = useRuntimeConfig();
const { request } = useApi();
const { activeCondominium, token } = useAuth();

const notifications = ref<OperationalNotification[]>([]);
const selectedId = ref("");
const filter = ref("review");
const loading = ref(false);
const saving = ref(false);
const validating = ref(false);
const actionNotificationId = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const finalText = ref("");
const showPreview = ref(false);
const sendMessage = ref("");
const pdfPreviewUrl = ref("");
const loadingPdfPreview = ref(false);
const pdfPreviewError = ref("");
const notificationSummary = ref({ pending_count: 0, in_review_count: 0, ready_to_send_count: 0 });

const statusFilters = [
  { id: "review", label: "Pendientes", statuses: "pending_review,in_review" },
  { id: "ready", label: "Informes para enviar", statuses: "ready_to_send,validated" },
  { id: "history", label: "Historial", statuses: "sent,dismissed" },
];

const selectedNotification = computed(() => notifications.value.find((item) => item.id === selectedId.value) || notifications.value[0] || null);

const pendingCount = computed(() => notificationSummary.value.pending_count + notificationSummary.value.in_review_count);
const readyCount = computed(() => notificationSummary.value.ready_to_send_count);
const validatedCount = computed(() => notifications.value.filter((item) => ["ready_to_send", "validated", "sent"].includes(item.status)).length);
const notificationFilterCount = (id: string) => {
  if (id === "review") return pendingCount.value;
  if (id === "ready") return readyCount.value;
  return null;
};

const currentFilter = computed(() => statusFilters.find((item) => item.id === filter.value) || statusFilters[0]);
const isHistoryFilter = computed(() => filter.value === "history");
const isLocked = computed(() => selectedNotification.value ? ["ready_to_send", "validated", "sent", "dismissed"].includes(selectedNotification.value.status) : true);
const canDismiss = computed(() => selectedNotification.value ? ["pending_review", "in_review"].includes(selectedNotification.value.status) : false);
const previewBlocks = computed(() => renderPreviewBlocks(finalText.value));
const shouldShowPdfPreview = computed(() => selectedNotification.value?.status === "ready_to_send");

const clearPdfPreview = () => {
  if (pdfPreviewUrl.value && import.meta.client) {
    URL.revokeObjectURL(pdfPreviewUrl.value);
  }
  pdfPreviewUrl.value = "";
  pdfPreviewError.value = "";
};

const loadNotifications = async () => {
  if (!token.value || !activeCondominium.value?.id) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const query = currentFilter.value.statuses ? `?status_filter=${encodeURIComponent(currentFilter.value.statuses)}` : "";
    const data = await request<NotificationListResponse>(`/api/v1/portal/notifications/${query}`);
    notifications.value = data.items || [];
    if (!notifications.value.some((item) => item.id === selectedId.value)) {
      selectedId.value = notifications.value[0]?.id || "";
    }
    finalText.value = selectedNotification.value?.final_body || selectedNotification.value?.draft_body || "";
  } catch (error) {
    notifications.value = [];
    selectedId.value = "";
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const loadFilterWithSelection = async (filterId: string, notificationId: string) => {
  filter.value = filterId;
  selectedId.value = notificationId;
  await loadNotifications();
  selectedId.value = notifications.value.some((item) => item.id === notificationId)
    ? notificationId
    : notifications.value[0]?.id || "";
};

const loadNotificationSummary = async () => {
  if (!token.value || !activeCondominium.value?.id) {
    notificationSummary.value = { pending_count: 0, in_review_count: 0, ready_to_send_count: 0 };
    return;
  }
  try {
    notificationSummary.value = await request<{ pending_count: number; in_review_count: number; ready_to_send_count: number }>("/api/v1/portal/notifications/summary");
  } catch {
    notificationSummary.value = { pending_count: 0, in_review_count: 0, ready_to_send_count: 0 };
  }
};

const refreshNotifications = async () => {
  await Promise.all([loadNotifications(), loadNotificationSummary()]);
};

const selectNotification = (notification: OperationalNotification) => {
  selectedId.value = notification.id;
  successMessage.value = "";
  errorMessage.value = "";
  finalText.value = notification.final_body || notification.draft_body || "";
};

const saveDraft = async () => {
  if (!selectedNotification.value) return;
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const saved = await request<OperationalNotification>(`/api/v1/portal/notifications/${selectedNotification.value.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ final_body: finalText.value, status: "in_review" }),
    });
    notifications.value = notifications.value.map((item) => item.id === saved.id ? saved : item);
    successMessage.value = "Cambios guardados.";
    loadNotificationSummary();
    emit("changed");
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    saving.value = false;
  }
};

const changeNotificationStatus = async (status: "pending_review" | "ready_to_send") => {
  if (!selectedNotification.value) return;
  await moveNotificationStatus(selectedNotification.value, status);
};

const moveNotificationStatus = async (notification: OperationalNotification, status: "pending_review" | "ready_to_send") => {
  saving.value = true;
  actionNotificationId.value = notification.id;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const finalBody = notification.id === selectedNotification.value?.id
      ? finalText.value
      : notification.final_body || notification.draft_body || "";
    const saved = await request<OperationalNotification>(`/api/v1/portal/notifications/${notification.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ final_body: finalBody, status }),
    });
    if (currentFilter.value.statuses.split(",").includes(saved.status)) {
      notifications.value = notifications.value.map((item) => item.id === saved.id ? saved : item);
      selectNotification(saved);
    } else {
      notifications.value = notifications.value.filter((item) => item.id !== saved.id);
      selectedId.value = notifications.value[0]?.id || "";
    }
    successMessage.value = status === "ready_to_send"
      ? "Informe movido a Informes para enviar."
      : "Autorizacion movida a Pendientes.";
    await loadNotificationSummary();
    emit("changed");
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    actionNotificationId.value = "";
    saving.value = false;
  }
};

const validateNotification = async () => {
  if (!selectedNotification.value) return;
  if (!finalText.value.trim()) {
    errorMessage.value = "El texto final no puede estar vacio.";
    return;
  }
  validating.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const saved = await request<OperationalNotification>(`/api/v1/portal/notifications/${selectedNotification.value.id}/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ final_body: finalText.value, title: selectedNotification.value.title }),
    });
    showPreview.value = false;
    successMessage.value = "Informe validado y preparado para envio movil.";
    await Promise.all([loadFilterWithSelection("ready", saved.id), loadNotificationSummary()]);
    emit("changed");
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    validating.value = false;
  }
};

const openPreview = () => {
  if (!selectedNotification.value) return;
  if (!finalText.value.trim()) {
    errorMessage.value = "El texto final no puede estar vacio.";
    return;
  }
  errorMessage.value = "";
  successMessage.value = "";
  showPreview.value = true;
};

const prepareSend = () => {
  sendMessage.value = "El envio quedo preparado. El envio movil se conectara en el siguiente paso.";
  successMessage.value = sendMessage.value;
};

const apiBase = computed(() => {
  if (import.meta.client) return localStorage.getItem("komite_api_base") || config.public.apiBase;
  return config.public.apiBase;
});

const fetchNotificationPdf = async () => {
  if (!selectedNotification.value || !token.value || !activeCondominium.value?.id || !import.meta.client) return;
  const response = await fetch(`${apiBase.value}/api/v1/portal/notifications/${selectedNotification.value.id}/report.pdf`, {
    headers: {
      Authorization: `Bearer ${token.value}`,
      "X-Condominium": activeCondominium.value.id,
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response;
};

const loadPdfPreview = async () => {
  clearPdfPreview();
  if (!shouldShowPdfPreview.value) return;
  loadingPdfPreview.value = true;
  try {
    const response = await fetchNotificationPdf();
    if (!response) return;
    const blob = await response.blob();
    pdfPreviewUrl.value = URL.createObjectURL(blob);
  } catch (error) {
    pdfPreviewError.value = readableError(error);
  } finally {
    loadingPdfPreview.value = false;
  }
};

const downloadPdf = async () => {
  if (!selectedNotification.value || !import.meta.client) return;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const response = await fetchNotificationPdf();
    if (!response) return;
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/i);
    const filename = match?.[1] || `informe-${selectedNotification.value.id.slice(0, 8)}.pdf`;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    errorMessage.value = readableError(error);
  }
};

const dismissNotification = async (notification = selectedNotification.value) => {
  if (!notification) return;
  saving.value = true;
  actionNotificationId.value = notification.id;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const saved = await request<OperationalNotification>(`/api/v1/portal/notifications/${notification.id}/dismiss`, {
      method: "POST",
    });
    if (currentFilter.value.statuses.split(",").includes(saved.status)) {
      notifications.value = notifications.value.map((item) => item.id === saved.id ? saved : item);
      selectNotification(saved);
    } else {
      notifications.value = notifications.value.filter((item) => item.id !== saved.id);
      selectedId.value = notifications.value[0]?.id || "";
    }
    successMessage.value = "Autorizacion descartada.";
    await loadNotificationSummary();
    emit("changed");
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    actionNotificationId.value = "";
    saving.value = false;
  }
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudieron cargar las autorizaciones.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

const formatDateTime = (value: string | null | undefined) => {
  if (!value) return "Sin fecha";
  return new Intl.DateTimeFormat("es-CL", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
};

const statusLabel = (status: string) => {
  if (status === "pending_review") return "Pendiente";
  if (status === "in_review") return "En revision";
  if (status === "ready_to_send") return "Lista para enviar";
  if (status === "validated") return "Validada";
  if (status === "sent") return "Enviada";
  if (status === "dismissed") return "Descartada";
  return status;
};

const statusBadgeClass = (status: string) => {
  if (status === "pending_review") return "is-pending";
  if (status === "in_review") return "is-progress";
  if (["ready_to_send", "validated", "sent"].includes(status)) return "is-active";
  if (status === "dismissed") return "is-inactive";
  return "is-neutral";
};

const priorityLabel = (priority: string) => {
  if (priority === "urgent") return "Urgente";
  if (priority === "high") return "Alta";
  if (priority === "low") return "Baja";
  return "Media";
};

const renderInline = (value: string): PreviewInline[] => {
  const parts: PreviewInline[] = [];
  const pattern = /\*\*(.+?)\*\*/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(value)) !== null) {
    if (match.index > cursor) parts.push({ text: value.slice(cursor, match.index), bold: false });
    parts.push({ text: match[1], bold: true });
    cursor = match.index + match[0].length;
  }
  if (cursor < value.length) parts.push({ text: value.slice(cursor), bold: false });
  return parts.length ? parts : [{ text: value, bold: false }];
};

const cleanMarkdownText = (value: string) => value
  .replace(/^#+\s*/, "")
  .replace(/^\*\*(.+)\*\*:?$/, "$1")
  .trim();

const renderPreviewBlocks = (value: string): PreviewBlock[] => {
  const blocks: PreviewBlock[] = [];
  const lines = value.replace(/\r\n/g, "\n").split("\n");
  let paragraph: string[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flushParagraph = () => {
    const text = paragraph.join(" ").trim();
    if (text) blocks.push({ type: "paragraph", content: renderInline(text) });
    paragraph = [];
  };

  const flushList = () => {
    if (list && list.items.length) {
      blocks.push({ type: "list", ordered: list.ordered, items: list.items.map((item) => renderInline(cleanMarkdownText(item))) });
    }
    list = null;
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      blocks.push({ type: "heading", level: heading[1].length, content: renderInline(cleanMarkdownText(heading[2])) });
      continue;
    }

    if (/^\*\*.+\*\*:?$/.test(line)) {
      flushParagraph();
      flushList();
      blocks.push({ type: "heading", level: 3, content: renderInline(cleanMarkdownText(line)) });
      continue;
    }

    const unordered = line.match(/^[-*]\s+(.+)$/);
    const ordered = line.match(/^\d+[.)]\s+(.+)$/);
    if (unordered || ordered) {
      flushParagraph();
      const isOrdered = Boolean(ordered);
      const item = (ordered || unordered)?.[1] || "";
      if (!list || list.ordered !== isOrdered) flushList();
      if (!list) list = { ordered: isOrdered, items: [] };
      list.items.push(item);
      continue;
    }

    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();
  return blocks;
};

watch([filter, () => activeCondominium.value?.id, token], refreshNotifications);
watch(selectedNotification, (notification) => {
  finalText.value = notification?.final_body || notification?.draft_body || "";
  loadPdfPreview();
});

onMounted(refreshNotifications);
onBeforeUnmount(clearPdfPreview);
</script>

<template>
  <section class="panel notifications-panel">
    <div class="dashboard-hero notifications-hero">
      <div>
        <p class="eyebrow">Operacion diaria</p>
        <h2>Autorizaciones</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Sin condominio seleccionado" }}</p>
      </div>
      <div class="committee-summary operational-summary">
        <article>
          <span>En revision</span>
          <strong>{{ pendingCount }}</strong>
        </article>
        <article>
          <span>Listas</span>
          <strong>{{ readyCount }}</strong>
        </article>
        <article>
          <span>Validadas</span>
          <strong>{{ validatedCount }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>
    <p v-if="successMessage" class="form-success result-message">{{ successMessage }}</p>

    <div class="notifications-toolbar">
      <div class="segmented-control" role="tablist" aria-label="Filtro de autorizaciones">
        <button
          v-for="item in statusFilters"
          :key="item.id"
          class="button compact"
          :class="filter === item.id ? 'navy' : 'ghost'"
          type="button"
          @click="filter = item.id"
        >
          <span>{{ item.label }}</span>
          <span v-if="notificationFilterCount(item.id) !== null" class="filter-count">{{ notificationFilterCount(item.id) }}</span>
        </button>
      </div>
      <button class="button ghost" type="button" :disabled="loading" @click="refreshNotifications">
        <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
        <span>Actualizar</span>
      </button>
    </div>

    <div v-if="isHistoryFilter && notifications.length" class="notification-history-table-wrap">
      <table class="notification-history-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Informe</th>
            <th>Proveedor</th>
            <th>Evento</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="notification in notifications" :key="notification.id">
            <td>{{ formatDateTime(notification.validated_at || notification.updated_at || notification.created_at) }}</td>
            <td>
              <strong>{{ notification.title }}</strong>
              <small>{{ notification.summary || "Sin resumen" }}</small>
            </td>
            <td>
              <strong>{{ notification.provider_name || "Sin proveedor" }}</strong>
              <small>{{ notification.provider_email || notification.provider_phone || "Sin contacto" }}</small>
            </td>
            <td>{{ notification.event_title || "Entrega operativa" }}</td>
            <td>
              <span class="status-badge" :class="statusBadgeClass(notification.status)">
                <span aria-hidden="true"></span>
                {{ statusLabel(notification.status) }}
              </span>
            </td>
            <td>
              <div class="history-actions">
                <button
                  class="button ghost compact"
                  type="button"
                  :disabled="actionNotificationId === notification.id"
                  @click="moveNotificationStatus(notification, 'pending_review')"
                >
                  Pendientes
                </button>
                <button
                  class="button navy compact"
                  type="button"
                  :disabled="actionNotificationId === notification.id"
                  @click="moveNotificationStatus(notification, 'ready_to_send')"
                >
                  Informes para enviar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="selectedNotification" class="notifications-workspace">
      <aside class="notification-list">
        <button
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-list-item"
          :class="{ active: selectedNotification.id === notification.id }"
          type="button"
          @click="selectNotification(notification)"
        >
          <span class="status-badge" :class="statusBadgeClass(notification.status)">
            <span aria-hidden="true"></span>
            {{ statusLabel(notification.status) }}
          </span>
          <strong>{{ notification.title }}</strong>
          <small>{{ notification.summary || notification.event_title || "Sin resumen" }}</small>
          <small>{{ formatDateTime(notification.created_at) }}</small>
        </button>
      </aside>

      <article class="notification-detail">
        <header class="notification-detail-header">
          <div>
            <p class="eyebrow">Revision supervisor</p>
            <h2>{{ selectedNotification.title }}</h2>
            <p class="placeholder-copy">{{ selectedNotification.event_title || "Entrega operativa" }}</p>
          </div>
          <span class="priority-pill" :class="`is-${selectedNotification.priority}`">{{ priorityLabel(selectedNotification.priority) }}</span>
        </header>

        <div class="notification-meta-grid">
          <article>
            <span>Proveedor</span>
            <strong>{{ selectedNotification.provider_name || "Sin proveedor" }}</strong>
            <small>{{ selectedNotification.provider_email || selectedNotification.provider_phone || "Sin contacto" }}</small>
          </article>
          <article>
            <span>Estado</span>
            <strong>{{ statusLabel(selectedNotification.status) }}</strong>
            <small>{{ selectedNotification.send_status === "pending" ? "Envio movil preparado" : "Envio aun no preparado" }}</small>
          </article>
          <article>
            <span>Informe</span>
            <strong>{{ selectedNotification.report_id ? "Generado" : "No generado" }}</strong>
            <small>{{ selectedNotification.validated_at ? formatDateTime(selectedNotification.validated_at) : "Pendiente de validacion" }}</small>
          </article>
        </div>

        <section v-if="shouldShowPdfPreview" class="notification-pdf-preview">
          <header>
            <div>
              <h3>Informe PDF</h3>
              <p class="placeholder-copy">Vista final del documento que se enviara o descargara.</p>
            </div>
            <button class="button ghost compact" type="button" :disabled="loadingPdfPreview" @click="loadPdfPreview">
              <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
              <span>Actualizar PDF</span>
            </button>
          </header>
          <div v-if="loadingPdfPreview" class="pdf-preview-state">
            Cargando PDF...
          </div>
          <div v-else-if="pdfPreviewError" class="pdf-preview-state is-error">
            {{ pdfPreviewError }}
          </div>
          <iframe
            v-else-if="pdfPreviewUrl"
            class="pdf-preview-frame"
            :src="pdfPreviewUrl"
            title="Vista del informe PDF"
          ></iframe>
          <div v-else class="pdf-preview-state">
            PDF no disponible.
          </div>
        </section>

        <div v-else class="notification-editor-grid">
          <label class="wide-editor">
            Texto final para validar
            <textarea v-model="finalText" rows="14" :readonly="isLocked"></textarea>
          </label>
        </div>

        <details v-if="!shouldShowPdfPreview" class="notification-source">
          <summary>Ver respuesta original del proveedor</summary>
          <pre>{{ selectedNotification.body || "Sin detalle original." }}</pre>
        </details>

        <div class="modal-actions">
          <button v-if="canDismiss" class="button ghost" type="button" :disabled="saving || validating" @click="dismissNotification()">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
            <span>Descartar</span>
          </button>
          <button v-if="!isLocked" class="button ghost" type="button" :disabled="saving || validating" @click="saveDraft">
            <svg class="icon" aria-hidden="true"><use href="#icon-save" /></svg>
            <span>{{ saving ? "Guardando..." : "Guardar" }}</span>
          </button>
          <button v-if="!isLocked" class="button navy" type="button" :disabled="saving || validating" @click="openPreview">
            <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
            <span>Vista preliminar</span>
          </button>
          <button v-if="!isLocked" class="button orange" type="button" :disabled="saving || validating" @click="validateNotification">
            <svg class="icon" aria-hidden="true"><use href="#icon-checks" /></svg>
            <span>{{ validating ? "Validando..." : "Validar informe" }}</span>
          </button>
          <button v-if="selectedNotification.status === 'ready_to_send'" class="button orange" type="button" @click="prepareSend">
            <svg class="icon" aria-hidden="true"><use href="#icon-message" /></svg>
            <span>Enviar</span>
          </button>
          <button v-if="selectedNotification.status === 'ready_to_send'" class="button ghost" type="button" @click="downloadPdf">
            <svg class="icon" aria-hidden="true"><use href="#icon-download" /></svg>
            <span>Descargar PDF</span>
          </button>
          <button v-if="selectedNotification.status === 'ready_to_send'" class="button ghost" type="button" :disabled="saving" @click="changeNotificationStatus('pending_review')">
            <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
            <span>Volver a Pendientes</span>
          </button>
          <button v-if="selectedNotification.status === 'ready_to_send'" class="button ghost" type="button" :disabled="saving" @click="dismissNotification()">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
            <span>Descartar</span>
          </button>
          <button v-if="selectedNotification.status === 'dismissed'" class="button ghost" type="button" :disabled="saving" @click="changeNotificationStatus('pending_review')">
            <svg class="icon" aria-hidden="true"><use href="#icon-refresh" /></svg>
            <span>Mover a Pendientes</span>
          </button>
          <button v-if="selectedNotification.status === 'dismissed'" class="button navy" type="button" :disabled="saving" @click="changeNotificationStatus('ready_to_send')">
            <svg class="icon" aria-hidden="true"><use href="#icon-file-text" /></svg>
            <span>Mover a Informes para enviar</span>
          </button>
        </div>
      </article>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-message" /></svg>
      </span>
      <h2>Sin autorizaciones</h2>
      <p class="placeholder-copy">Cuando un proveedor envie un formulario desde su link, aparecera aqui para autorizacion del supervisor.</p>
    </div>

    <div v-if="showPreview && selectedNotification" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="notification-preview-title">
      <section class="confirm-modal notification-preview-modal">
        <header class="notification-preview-header">
          <div>
            <p class="eyebrow">Vista preliminar</p>
            <h2 id="notification-preview-title">{{ selectedNotification.title }}</h2>
            <p class="placeholder-copy">Revisa el informe final antes de validarlo y dejarlo listo para envio movil.</p>
          </div>
          <button class="button ghost icon-only" type="button" :disabled="validating" title="Cerrar" @click="showPreview = false">
            <svg class="icon" aria-hidden="true"><use href="#icon-x" /></svg>
          </button>
        </header>

        <article class="report-preview-sheet">
          <div class="report-preview-brand">
            <img src="/assets/komite-logo.png" alt="Komite" />
            <div>
              <span>Informe de servicio</span>
              <strong>{{ activeCondominium?.name || "Condominio" }}</strong>
            </div>
          </div>

          <div class="report-preview-title">
            <h3>{{ selectedNotification.title }}</h3>
            <span class="status-badge" :class="statusBadgeClass(selectedNotification.status)">
              <span aria-hidden="true"></span>
              {{ statusLabel(selectedNotification.status) }}
            </span>
          </div>

          <dl class="report-preview-meta">
            <div>
              <dt>Proveedor</dt>
              <dd>{{ selectedNotification.provider_name || "Sin proveedor" }}</dd>
            </div>
            <div>
              <dt>Contacto</dt>
              <dd>{{ selectedNotification.provider_email || selectedNotification.provider_phone || "Sin contacto" }}</dd>
            </div>
            <div>
              <dt>Evento</dt>
              <dd>{{ selectedNotification.event_title || "Entrega operativa" }}</dd>
            </div>
            <div>
              <dt>Fecha de recepcion</dt>
              <dd>{{ formatDateTime(selectedNotification.created_at) }}</dd>
            </div>
          </dl>

          <section class="report-preview-content">
            <template v-for="(block, blockIndex) in previewBlocks" :key="blockIndex">
              <h3 v-if="block.type === 'heading' && block.level <= 2">
                <span v-for="(part, partIndex) in block.content" :key="partIndex" :class="{ 'is-bold': part.bold }">{{ part.text }}</span>
              </h3>
              <h4 v-else-if="block.type === 'heading'">
                <span v-for="(part, partIndex) in block.content" :key="partIndex" :class="{ 'is-bold': part.bold }">{{ part.text }}</span>
              </h4>
              <ol v-else-if="block.type === 'list' && block.ordered">
                <li v-for="(item, itemIndex) in block.items" :key="itemIndex">
                  <span v-for="(part, partIndex) in item" :key="partIndex" :class="{ 'is-bold': part.bold }">{{ part.text }}</span>
                </li>
              </ol>
              <ul v-else-if="block.type === 'list'">
                <li v-for="(item, itemIndex) in block.items" :key="itemIndex">
                  <span v-for="(part, partIndex) in item" :key="partIndex" :class="{ 'is-bold': part.bold }">{{ part.text }}</span>
                </li>
              </ul>
              <p v-else>
                <span v-for="(part, partIndex) in block.content" :key="partIndex" :class="{ 'is-bold': part.bold }">{{ part.text }}</span>
              </p>
            </template>
            <p v-if="!previewBlocks.length">Sin texto final.</p>
          </section>
        </article>

        <div class="modal-actions">
          <button class="button ghost" type="button" :disabled="validating" @click="showPreview = false">
            <svg class="icon" aria-hidden="true"><use href="#icon-pencil" /></svg>
            <span>Volver a editar</span>
          </button>
          <button class="button navy" type="button" :disabled="validating" @click="validateNotification">
            <svg class="icon" aria-hidden="true"><use href="#icon-checks" /></svg>
            <span>{{ validating ? "Validando..." : "Validar informe" }}</span>
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.notifications-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 18px 0;
}

.segmented-control {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.segmented-control .button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.filter-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(15, 36, 55, 0.08);
  color: inherit;
  font-size: 0.75rem;
  font-weight: 800;
}

.segmented-control .button.navy .filter-count {
  background: rgba(255, 255, 255, 0.18);
}

.notification-history-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
}

.notification-history-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 980px;
}

.notification-history-table th,
.notification-history-table td {
  padding: 12px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: top;
}

.notification-history-table th {
  color: var(--muted);
  background: var(--surface-muted);
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
}

.notification-history-table tbody tr:hover {
  background: rgba(15, 36, 55, 0.025);
}

.notification-history-table tbody tr:last-child td {
  border-bottom: 0;
}

.notification-history-table td strong,
.notification-history-table td small {
  display: block;
  overflow-wrap: anywhere;
}

.notification-history-table td small {
  margin-top: 4px;
  color: var(--muted);
}

.history-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 260px;
}

.notifications-workspace {
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.notification-list {
  display: grid;
  gap: 10px;
}

.notification-list-item {
  display: grid;
  gap: 6px;
  width: 100%;
  min-height: 128px;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}

.notification-list-item:hover,
.notification-list-item.active {
  border-color: var(--orange);
  box-shadow: 0 12px 24px rgba(8, 24, 48, 0.08);
}

.notification-list-item strong,
.notification-list-item small {
  overflow-wrap: anywhere;
}

.notification-detail {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.notification-detail-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.notification-detail-header h2 {
  margin: 0;
  font-size: 1.35rem;
}

.notification-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.notification-meta-grid article {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-muted);
}

.notification-meta-grid span,
.notification-meta-grid small {
  color: var(--muted);
}

.notification-meta-grid strong,
.notification-meta-grid small {
  overflow-wrap: anywhere;
}

.notification-editor-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.notification-editor-grid label {
  display: grid;
  gap: 8px;
  font-weight: 700;
}

.notification-editor-grid textarea {
  width: 100%;
  min-height: 360px;
  resize: vertical;
  font-weight: 400;
  line-height: 1.45;
}

.notification-source {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  background: var(--surface);
}

.notification-source summary {
  cursor: pointer;
  font-weight: 700;
}

.notification-source pre {
  margin: 12px 0 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.notification-pdf-preview {
  display: grid;
  gap: 12px;
}

.notification-pdf-preview header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.notification-pdf-preview h3 {
  margin: 0;
  color: var(--ink);
  font-size: 1rem;
}

.pdf-preview-frame {
  width: 100%;
  min-height: 720px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
}

.pdf-preview-state {
  display: grid;
  min-height: 240px;
  place-items: center;
  border: 1px dashed var(--border);
  border-radius: 8px;
  background: var(--surface-muted);
  color: var(--muted);
  font-weight: 700;
}

.pdf-preview-state.is-error {
  border-color: rgba(180, 35, 24, 0.3);
  background: #fff1f0;
  color: #b42318;
}

.notification-preview-modal {
  width: min(980px, calc(100vw - 32px));
  max-height: calc(100vh - 36px);
  overflow: auto;
}

.notification-preview-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.notification-preview-header h2 {
  margin: 0;
}

.report-preview-sheet {
  display: grid;
  gap: 20px;
  padding: 28px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
  box-shadow: inset 0 0 0 1px rgba(15, 36, 55, 0.02);
}

.report-preview-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.report-preview-brand img {
  width: 118px;
  height: auto;
}

.report-preview-brand div {
  display: grid;
  gap: 4px;
  text-align: right;
}

.report-preview-brand span,
.report-preview-meta dt {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
}

.report-preview-title {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.report-preview-title h3 {
  margin: 0;
  font-size: 1.45rem;
}

.report-preview-meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.report-preview-meta div {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-muted);
}

.report-preview-meta dd {
  margin: 5px 0 0;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.report-preview-content {
  display: grid;
  gap: 10px;
  font-size: 0.98rem;
  line-height: 1.65;
}

.report-preview-content h3,
.report-preview-content h4,
.report-preview-content p,
.report-preview-content ul,
.report-preview-content ol {
  margin: 0;
  overflow-wrap: anywhere;
}

.report-preview-content h3 {
  margin-top: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
  color: var(--navy);
  font-size: 1.08rem;
}

.report-preview-content h4 {
  margin-top: 8px;
  color: var(--navy);
  font-size: 0.98rem;
}

.report-preview-content ul,
.report-preview-content ol {
  display: grid;
  gap: 6px;
  padding-left: 22px;
}

.report-preview-content .is-bold {
  font-weight: 800;
}

@media (max-width: 980px) {
  .notifications-workspace,
  .notification-editor-grid,
  .notification-meta-grid,
  .report-preview-meta {
    grid-template-columns: 1fr;
  }

  .report-preview-brand,
  .report-preview-title,
  .notification-preview-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .report-preview-brand div {
    text-align: left;
  }
}
</style>
