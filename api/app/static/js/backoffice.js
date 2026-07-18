const API_BASE = localStorage.getItem("komite_api_base") || window.location.origin;
const BACKOFFICE_PATH = "/backoffice";
const TOKEN_KEY = "komite_token";
const REFRESH_TOKEN_KEY = "komite_refresh_token";
const USER_KEY = "komite_user";
const SIDEBAR_KEY = "komite_sidebar_collapsed";
const NAV_GROUPS_KEY = "komite_nav_groups_collapsed";
const ACCESS_TOKEN_MAX_AGE_SECONDS = 1800;
const REFRESH_TOKEN_MAX_AGE_SECONDS = 604800;

const state = {
  token: readToken(),
  refreshToken: readRefreshToken(),
  user: readUser(),
  currentView: "dashboard",
  currentItems: [],
  tablePage: 1,
  tablePageSize: 10,
  tableMeta: { total: 0, page: 1, page_size: 10, pages: 1 },
  companies: [],
  condominiums: [],
  units: [],
  unitContacts: [],
  roles: [],
  usersLookup: [],
  operationalStaff: [],
  inspectionTemplates: [],
  inspectionTemplateSections: [],
  duplicateTemplateId: null,
  duplicateTemplateKind: "inspection",
  edifitoNeighborsPreview: null,
  comunidadFelizNeighborsPreview: null,
  companyReturnContext: null,
  confirmResolver: null,
};

let ticketsStatusChart = null;
let ticketsCompanyChart = null;
let searchDebounceTimer = null;
let pendingRequests = 0;

const outerStackBorderPlugin = {
  id: "outerStackBorder",
  afterDatasetsDraw(chart) {
    const { ctx, data } = chart;
    if (chart.config.type !== "bar" || !chart.options.plugins?.outerStackBorder?.enabled) return;

    ctx.save();
    ctx.strokeStyle = chart.options.plugins.outerStackBorder.color || "#93c5fd";
    ctx.lineWidth = chart.options.plugins.outerStackBorder.width || 1.5;
    data.labels.forEach((_, dataIndex) => {
      const visibleBars = data.datasets
        .map((__, datasetIndex) => chart.getDatasetMeta(datasetIndex).data[dataIndex])
        .filter(Boolean);
      if (!visibleBars.length) return;

      const left = Math.min(...visibleBars.map((bar) => bar.x - bar.width / 2));
      const right = Math.max(...visibleBars.map((bar) => bar.x + bar.width / 2));
      const top = Math.min(...visibleBars.map((bar) => bar.y));
      const bottom = Math.max(...visibleBars.map((bar) => bar.base));
      ctx.strokeRect(left, top, right - left, bottom - top);
    });
    ctx.restore();
  },
};

const stackPercentageLabelsPlugin = {
  id: "stackPercentageLabels",
  afterDatasetsDraw(chart) {
    if (chart.config.type !== "bar" || !chart.options.plugins?.stackPercentageLabels?.enabled) return;
    const { ctx, data } = chart;
    const color = chart.options.plugins.stackPercentageLabels.color || "#172536";
    const minHeight = chart.options.plugins.stackPercentageLabels.minHeight || 18;

    ctx.save();
    ctx.fillStyle = color;
    ctx.font = "700 11px Inter, Segoe UI, Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    data.labels.forEach((_, dataIndex) => {
      const total = data.datasets.reduce((sum, dataset) => sum + Number(dataset.data[dataIndex] || 0), 0);
      if (!total) return;

      data.datasets.forEach((dataset, datasetIndex) => {
        const value = Number(dataset.data[dataIndex] || 0);
        if (!value) return;

        const bar = chart.getDatasetMeta(datasetIndex).data[dataIndex];
        if (!bar) return;
        const height = Math.abs(bar.base - bar.y);
        if (height < minHeight) return;

        const percent = Math.round((value / total) * 100);
        ctx.fillText(`${percent}%`, bar.x, (bar.y + bar.base) / 2);
      });
    });
    ctx.restore();
  },
};

if (window.Chart) {
  Chart.register(outerStackBorderPlugin, stackPercentageLabelsPlugin);
}

const resources = {
  companies: {
    title: "Empresas",
    endpoint: "/api/v1/companies/",
    columns: ["name", "rut", "email", "status"],
  },
  banks: {
    title: "Bancos",
    endpoint: "/api/v1/banks/",
    columns: ["name", "code", "country", "website", "status"],
    createLabel: "Nuevo banco",
    singular: "banco",
    fields: [
      { name: "name", label: "Nombre", required: true, maxLength: 120 },
      { name: "code", label: "Código", maxLength: 40 },
      { name: "country", label: "País", defaultValue: "Chile", maxLength: 80 },
      { name: "website", label: "Web", maxLength: 255 },
      { name: "status", label: "Estado", type: "select", options: [["active", "Activo"], ["inactive", "Inactivo"], ["draft", "Borrador"]], defaultValue: "active" },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  condominiums: {
    title: "Condominios",
    endpoint: "/api/v1/condominiums/",
    columns: ["company_id", "name", "address", "status", "units_count"],
  },
  committeeMembers: {
    title: "Comité",
    endpoint: "/api/v1/committee-members/",
    columns: ["company_id", "condominium_id", "position", "full_name", "email", "phone", "status"],
    createLabel: "Nuevo miembro",
    singular: "miembro",
    fields: [
      { name: "company_id", label: "Empresa", type: "company", required: true },
      { name: "condominium_id", label: "Condominio", type: "condominium", required: true, emptyLabel: "Selecciona condominio" },
      { name: "unit_id", label: "Unidad", type: "unit" },
      { name: "unit_contact_id", label: "Contacto vecino", type: "unit_contact" },
      { name: "user_id", label: "Usuario asociado", type: "user" },
      { name: "position", label: "Cargo", type: "select", options: [["presidente", "Presidente"], ["tesorero", "Tesorero"], ["secretario", "Secretario"], ["vocal", "Vocal"], ["administrador", "Administrador"], ["otro", "Otro"]], defaultValue: "vocal", required: true },
      { name: "full_name", label: "Nombre completo", required: true, maxLength: 150 },
      { name: "email", label: "Email", type: "email", maxLength: 255 },
      { name: "phone", label: "Teléfono", maxLength: 40 },
      { name: "start_date", label: "Inicio periodo", type: "date" },
      { name: "end_date", label: "Fin periodo", type: "date" },
      { name: "status", label: "Estado", type: "select", options: [["active", "Activo"], ["inactive", "Inactivo"]], defaultValue: "active" },
      { name: "receives_notifications", label: "Recibe notificaciones", type: "checkbox", defaultValue: true },
      { name: "display_order", label: "Orden", type: "number", defaultValue: 0 },
      { name: "notes", label: "Notas", type: "textarea" },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  incidents: {
    title: "Incidencias",
    endpoint: "/api/v1/incidents/",
    columns: ["category", "priority", "status", "created_at"],
  },
  supportTickets: {
    title: "Tickets",
    endpoint: "/api/v1/support-tickets/",
    columns: ["company_id", "condominium_id", "subject", "priority", "status", "due_date"],
    createLabel: "Nuevo ticket",
    singular: "ticket",
    fields: [
      { name: "company_id", label: "Empresa", type: "company", required: true },
      { name: "condominium_id", label: "Condominio", type: "condominium" },
      { name: "subject", label: "Asunto", required: true, maxLength: 180 },
      { name: "description", label: "Descripción", type: "textarea" },
      { name: "requester_name", label: "Solicitante", maxLength: 150 },
      { name: "requester_email", label: "Email solicitante", type: "email", maxLength: 255 },
      { name: "category", label: "Categoría", defaultValue: "general", maxLength: 80 },
      { name: "priority", label: "Prioridad", type: "select", options: [["low", "Baja"], ["medium", "Media"], ["high", "Alta"], ["urgent", "Urgente"]], defaultValue: "medium" },
      { name: "status", label: "Estado", type: "select", options: [["open", "Abierto"], ["pending", "Pendiente"], ["in_progress", "En curso"], ["resolved", "Resuelto"], ["closed", "Cerrado"]], defaultValue: "open" },
      { name: "assigned_to_id", label: "Asignado a", type: "user" },
      { name: "due_date", label: "Vencimiento", type: "date" },
      { name: "resolved_at", label: "Resuelto el", type: "datetime" },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  tasks: {
    title: "Tareas",
    endpoint: "/api/v1/tasks/",
    columns: ["title", "priority", "status", "due_date"],
  },
  reports: {
    title: "Informes",
    endpoint: "/api/v1/reports/",
    columns: ["title", "report_type", "status", "published_at"],
  },
  communications: {
    title: "Comunicaciones",
    endpoint: "/api/v1/communications/",
    columns: ["title", "communication_type", "audience", "status"],
  },
  inspections: {
    title: "Inspecciones",
    endpoint: "/api/v1/inspections/",
    columns: ["inspection_type", "status", "started_at", "finished_at"],
  },
  inspectionTemplates: {
    title: "Plantillas",
    endpoint: "/api/v1/inspection-templates/",
    columns: ["name", "template_type", "inspection_type", "version", "status", "is_active"],
    createLabel: "Nueva plantilla",
    singular: "plantilla",
    fields: [
      { name: "company_id", label: "Empresa", type: "company" },
      { name: "condominium_id", label: "Condominio", type: "condominium", emptyLabel: "Plantilla base sin condominio" },
      { name: "name", label: "Nombre", required: true, maxLength: 150 },
      { name: "description", label: "Descripci\u00f3n", type: "textarea" },
      { name: "template_type", label: "Tipo de plantilla", type: "select", options: [["inspection", "Inspecci\u00f3n"], ["maintenance", "Mantenci\u00f3n"], ["mixed", "Mixta"]], defaultValue: "maintenance" },
      { name: "inspection_type", label: "Categor\u00eda", type: "select", options: [["preventive", "Preventiva"], ["security", "Seguridad"], ["cleaning", "Aseo"], ["infrastructure", "Infraestructura"], ["operations", "Operaci\u00f3n"], ["other", "Otra"]], defaultValue: "preventive", required: true },
      { name: "version", label: "Versi\u00f3n", type: "number", defaultValue: 1 },
      { name: "status", label: "Estado", type: "select", options: [["draft", "Borrador"], ["active", "Activo"], ["published", "Publicado"], ["inactive", "Inactivo"]], defaultValue: "draft" },
      { name: "source_file_name", label: "Archivo origen", maxLength: 255 },
      { name: "is_active", label: "Activa", type: "checkbox", defaultValue: true },
      { name: "checklist_schema", label: "Checklist base", type: "json", defaultValue: [] },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  inspectionTemplateSections: {
    title: "Secciones",
    endpoint: "/api/v1/inspection-template-sections/",
    columns: ["template_id", "name", "display_order", "status"],
    createLabel: "Nueva secci\u00f3n",
    singular: "secci\u00f3n",
    fields: [
      { name: "company_id", label: "Empresa", type: "company" },
      { name: "template_id", label: "Plantilla", type: "inspection_template", required: true },
      { name: "name", label: "Nombre", required: true, maxLength: 150 },
      { name: "description", label: "Descripci\u00f3n", type: "textarea" },
      { name: "display_order", label: "Orden", type: "number", defaultValue: 0 },
      { name: "status", label: "Estado", type: "select", options: [["active", "Activo"], ["inactive", "Inactivo"], ["draft", "Borrador"]], defaultValue: "active" },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  inspectionTemplateItems: {
    title: "\u00cdtems de plantilla",
    endpoint: "/api/v1/inspection-template-items/",
    columns: ["template_id", "section_id", "asset_name", "task_name", "event_type", "periodicity", "default_responsible_profile", "default_duration_minutes", "requires_evidence", "status"],
    createLabel: "Nuevo \u00edtem",
    singular: "\u00edtem",
    fields: [
      { name: "company_id", label: "Empresa", type: "company" },
      { name: "template_id", label: "Plantilla", type: "inspection_template", required: true },
      { name: "section_id", label: "Secci\u00f3n", type: "inspection_template_section" },
      { name: "asset_name", label: "Activo / zona", maxLength: 180 },
      { name: "task_name", label: "Tarea", required: true, maxLength: 255 },
      { name: "instructions", label: "Instrucciones", type: "textarea" },
      { name: "event_type", label: "Tipo de tarea", type: "select", options: [["maintenance", "Mantencion"], ["inspection", "Inspeccion"]], defaultValue: "maintenance" },
      { name: "periodicity", label: "Periodicidad", type: "select", options: [["daily", "Diaria"], ["weekly", "Semanal"], ["biweekly", "Quincenal"], ["monthly", "Mensual"], ["bimonthly", "Cada 2 meses"], ["quarterly", "Trimestral"], ["four_monthly", "Cada 4 meses"], ["semiannual", "Semestral"], ["annual", "Anual"], ["biennial", "Cada 2 a\u00f1os"], ["permanent", "Permanente"], ["on_demand", "Seg\u00fan necesidad"]], defaultValue: "monthly" },
      { name: "planned_months", label: "Meses planificados", type: "json", defaultValue: [] },
      { name: "requires_evidence", label: "Requiere evidencia", type: "checkbox", defaultValue: false },
      { name: "default_responsible_profile", label: "Responsable sugerido", type: "select", options: [["", "Sin responsable sugerido"], ["project_manager", "Project manager"], ["supervisor", "Supervisor"], ["ejecutivo", "Ejecutivo/a"], ["conserje", "Conserje"]], defaultValue: "" },
      { name: "default_duration_minutes", label: "Duraci\u00f3n estimada (min)", type: "number" },
      { name: "display_order", label: "Orden", type: "number", defaultValue: 0 },
      { name: "status", label: "Estado", type: "select", options: [["active", "Activo"], ["inactive", "Inactivo"], ["draft", "Borrador"]], defaultValue: "active" },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  users: {
    title: "Usuarios",
    endpoint: "/api/v1/users/",
    columns: ["company_id", "email", "full_name", "company_profile", "organization_position", "role_code", "status"],
  },
  roles: {
    title: "Roles",
    endpoint: "/api/v1/roles/",
    columns: ["code", "name", "is_system"],
  },
  attachments: {
    title: "Archivos",
    endpoint: "/api/v1/attachments/",
    columns: ["file_name", "file_type", "mime_type", "created_at"],
  },
  audit: {
    title: "Auditoría",
    endpoint: "/api/v1/audit-logs/",
    columns: ["action", "entity_type", "entity_id", "created_at"],
  },
  ai: {
    title: "IA",
    endpoint: "/api/v1/ai-requests/",
    columns: ["provider", "model", "purpose", "status"],
  },
  aiPromptTemplates: {
    title: "Prompts IA",
    endpoint: "/api/v1/ai-prompt-templates/",
    columns: ["key", "name", "module", "asset_type", "default_model", "default_max_tokens", "status", "is_active"],
    createLabel: "Nuevo prompt IA",
    singular: "prompt IA",
    fields: [
      { name: "company_id", label: "Empresa", type: "company" },
      { name: "condominium_id", label: "Condominio", type: "condominium", emptyLabel: "Global / disponible para todos" },
      { name: "key", label: "Clave", required: true, maxLength: 120 },
      { name: "name", label: "Nombre", required: true, maxLength: 180 },
      { name: "description", label: "Descripción", type: "textarea" },
      { name: "purpose", label: "Propósito", required: true, maxLength: 100 },
      { name: "module", label: "Módulo", type: "select", options: [["general", "General"], ["operations", "Operación"], ["maintenance", "Mantención"], ["accounting", "Contabilidad"], ["communications", "Comunicaciones"], ["incidents", "Incidencias"]], defaultValue: "operations" },
      { name: "asset_type", label: "Tipo de activo", type: "select", options: [["", "Sin tipo específico"], ["elevator", "Ascensor"], ["pump", "Bomba"], ["gate", "Portón"], ["boiler", "Caldera"], ["pool", "Piscina"], ["camera", "Cámara"], ["generator", "Generador"], ["other", "Otro"]], defaultValue: "" },
      { name: "system_template", label: "System prompt", type: "textarea", required: true },
      { name: "user_template", label: "User prompt template", type: "textarea", required: true },
      { name: "required_variables", label: "Variables requeridas", type: "json", defaultValue: [] },
      { name: "optional_variables", label: "Variables opcionales", type: "json", defaultValue: [] },
      { name: "default_model", label: "Modelo", type: "select", options: [["", "Modelo por defecto"], ["deepseek-v4-flash", "DeepSeek V4 Flash"], ["deepseek-v4-pro", "DeepSeek V4 Pro"]], defaultValue: "deepseek-v4-flash" },
      { name: "default_temperature", label: "Temperatura", type: "number", defaultValue: 0.2, step: "0.1" },
      { name: "default_max_tokens", label: "Max tokens", type: "number", defaultValue: 1200 },
      { name: "reasoning_enabled", label: "Razonamiento", type: "checkbox", defaultValue: false },
      { name: "expects_json", label: "Espera JSON", type: "checkbox", defaultValue: false },
      { name: "version", label: "Versión", type: "number", defaultValue: 1 },
      { name: "status", label: "Estado", type: "select", options: [["draft", "Borrador"], ["active", "Activo"], ["published", "Publicado"], ["inactive", "Inactivo"]], defaultValue: "draft" },
      { name: "is_active", label: "Activa", type: "checkbox", defaultValue: true },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
};

const columnLabels = {
  id: "ID",
  name: "Nombre",
  rut: "RUT",
  email: "Email",
  key: "Clave",
  purpose: "Propósito",
  module: "Módulo",
  asset_type: "Tipo activo",
  default_model: "Modelo",
  default_max_tokens: "Max tokens",
  default_temperature: "Temperatura",
  reasoning_enabled: "Razonamiento",
  expects_json: "JSON",
  status: "Estado",
  address: "Dirección",
  company_id: "Empresa",
  condominium_id: "Condominio",
  code: "Código",
  country: "País",
  website: "Web",
  units_count: "Unidades",
  category: "Categoría",
  priority: "Prioridad",
  created_at: "Creado",
  title: "Titulo",
  due_date: "Vencimiento",
  report_type: "Tipo de informe",
  published_at: "Publicado",
  communication_type: "Tipo de comunicación",
  audience: "Audiencia",
  inspection_type: "Tipo de inspección",
  template_type: "Tipo plantilla",
  template_id: "Plantilla",
  section_id: "Secci\u00f3n",
  version: "Versi\u00f3n",
  is_active: "Activa",
  source_file_name: "Archivo origen",
  asset_name: "Activo / zona",
  task_name: "Tarea",
  event_type: "Tipo de tarea",
  instructions: "Instrucciones",
  periodicity: "Periodicidad",
  planned_months: "Meses planificados",
  requires_evidence: "Evidencia",
  default_responsible_profile: "Responsable sugerido",
  default_duration_minutes: "Duraci\u00f3n min.",
  started_at: "Inicio",
  finished_at: "Fin",
  full_name: "Nombre completo",
  company_profile: "Perfil Portal Administrador",
  organization_position: "Puesto en la organizacion",
  role_code: "Rol",
  scope: "Ámbito",
  is_system: "Sistema",
  file_name: "Archivo",
  file_type: "Tipo",
  mime_type: "MIME",
  action: "Acción",
  entity_type: "Entidad",
  entity_id: "ID entidad",
  provider: "Proveedor",
  model: "Modelo",
  purpose: "Uso",
  subject: "Asunto",
  description: "Descripción",
  requester_name: "Solicitante",
  requester_email: "Email solicitante",
  assigned_to_id: "Asignado a",
  resolved_at: "Resuelto el",
  position: "Cargo",
  phone: "Teléfono",
  unit_id: "Unidad",
  unit_contact_id: "Contacto vecino",
  user_id: "Usuario",
  start_date: "Inicio",
  end_date: "Fin",
  receives_notifications: "Notifica",
  display_order: "Orden",
  notes: "Notas",
};

const statusLabels = {
  active: "Activo",
  inactive: "Inactivo",
  draft: "Borrador",
  pending: "Pendiente",
  in_progress: "En curso",
  resolved: "Resuelto",
  completed: "Completado",
  failed: "Fallido",
  partial: "Parcial",
  new: "Nuevo",
  open: "Abierto",
  closed: "Cerrado",
  published: "Publicado",
};

const ticketStatusPalette = {
  open: { fill: "#2563eb", background: "#e8f0ff", color: "#173b8f", accent: "#2563eb" },
  pending: { fill: "#f59e0b", background: "#fff4d6", color: "#8a4b00", accent: "#f59e0b" },
  in_progress: { fill: "#7c3aed", background: "#f0e8ff", color: "#4c1d95", accent: "#7c3aed" },
  resolved: { fill: "#10b981", background: "#ddfff3", color: "#047857", accent: "#10b981" },
  closed: { fill: "#64748b", background: "#edf2f7", color: "#334155", accent: "#64748b" },
};

const companyChartPalette = [
  { background: "#0ea5e9", border: "#0284c7" },
  { background: "#14b8a6", border: "#0f766e" },
  { background: "#6366f1", border: "#4f46e5" },
  { background: "#a855f7", border: "#7e22ce" },
  { background: "#f97316", border: "#ea580c" },
  { background: "#22c55e", border: "#16a34a" },
  { background: "#e11d48", border: "#be123c" },
  { background: "#0891b2", border: "#0e7490" },
];

const roleLabels = {
  project_manager: "Project manager",
  ejecutivo: "Ejecutivo/a",
  supervisor: "Supervisor",
  conserje: "Conserje",
  vecino: "Vecino",
  comite: "Comité",
};

const positionLabels = {
  presidente: "Presidente",
  tesorero: "Tesorero",
  secretario: "Secretario",
  vocal: "Vocal",
  administrador: "Administrador",
  otro: "Otro",
};

const templateTypeLabels = {
  inspection: "Inspecci\u00f3n",
  maintenance: "Mantenci\u00f3n",
  mixed: "Mixta",
};

const eventTypeLabels = {
  task: "Generica",
  administrative: "Administrativa",
  assembly: "Asamblea",
  meeting: "Reunion",
  inspection: "Inspeccion",
  maintenance: "Mantencion",
  incident: "Incidencia",
};

const inspectionTypeLabels = {
  preventive: "Preventiva",
  security: "Seguridad",
  cleaning: "Aseo",
  infrastructure: "Infraestructura",
  operations: "Operaci\u00f3n",
  other: "Otra",
};

const periodicityLabels = {
  daily: "Diaria",
  weekly: "Semanal",
  biweekly: "Quincenal",
  monthly: "Mensual",
  bimonthly: "Cada 2 meses",
  quarterly: "Trimestral",
  four_monthly: "Cada 4 meses",
  semiannual: "Semestral",
  annual: "Anual",
  biennial: "Cada 2 a\u00f1os",
  permanent: "Permanente",
  on_demand: "Seg\u00fan necesidad",
};

const placeholders = {
  committee: {
    title: "Comité",
    text: "Aquí quedará la gestión de miembros del comité, cargos, vigencias y relaciones con condominios.",
  },
  neighbors: {
    title: "Vecinos",
    text: "Aquí se preparará la administración de vecinos, unidades, datos de contacto y preferencias de comunicación.",
  },
  settings: {
    title: "Configuración",
    text: "Aquí se centralizarán parámetros del sistema, integraciones, proveedores de IA y reglas operativas.",
  },
  integrations: {
    title: "Integraciones",
    text: "Aquí se gestionarán conectores externos, credenciales por proveedor, sincronizaciones y estado de integraciones como Edifito, Comunidad Feliz, IA y servicios de mensajería.",
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function setLoading(loading) {
  pendingRequests = Math.max(0, pendingRequests + (loading ? 1 : -1));
  const overlay = $("#loadingOverlay");
  if (overlay) overlay.hidden = pendingRequests === 0;
}

async function apiFetch(path, options = {}) {
  setLoading(true);

  try {
    const headers = options.headers || {};
    if (state.token) {
      headers.Authorization = `Bearer ${state.token}`;
    }

    let response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && state.refreshToken && shouldAttemptRefresh(path)) {
      const refreshed = await refreshSession();
      if (refreshed) {
        headers.Authorization = `Bearer ${state.token}`;
        response = await fetch(`${API_BASE}${path}`, {
          ...options,
          headers,
        });
      }
    }

    if (response.status === 401) {
      handleExpiredSession();
    }

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }

    return response.json();
  } finally {
    setLoading(false);
  }
}

async function apiDownload(path, fallbackFilename) {
  setLoading(true);

  try {
    const headers = {};
    if (state.token) headers.Authorization = `Bearer ${state.token}`;

    let response = await fetch(`${API_BASE}${path}`, { headers });
    if (response.status === 401 && state.refreshToken && shouldAttemptRefresh(path)) {
      const refreshed = await refreshSession();
      if (refreshed) {
        headers.Authorization = `Bearer ${state.token}`;
        response = await fetch(`${API_BASE}${path}`, { headers });
      }
    }
    if (response.status === 401) handleExpiredSession();
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const filename = filenameFromDisposition(response.headers.get("Content-Disposition")) || fallbackFilename;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } finally {
    setLoading(false);
  }
}

function filenameFromDisposition(disposition) {
  if (!disposition) return "";
  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utfMatch?.[1]) return decodeURIComponent(utfMatch[1]);
  const plainMatch = disposition.match(/filename="?([^";]+)"?/i);
  return plainMatch?.[1] || "";
}

function setSession(data) {
  state.token = data.access_token;
  state.refreshToken = data.refresh_token || state.refreshToken;
  state.user = data.user;
  persistSession(state.token, state.refreshToken, state.user);
}

function shouldAttemptRefresh(path) {
  return ![
    "/api/v1/auth/login",
    "/api/v1/auth/backoffice-login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
  ].includes(path);
}

function clearSession() {
  state.token = null;
  state.refreshToken = null;
  state.user = null;
  purgeStoredSession();
}

function handleExpiredSession() {
  clearSession();
  showLogin();
  $("#loginError").textContent = "Tu sesion ha caducado. Vuelve a entrar para continuar.";
  $("#loginError").hidden = false;
}

function purgeStoredSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
  document.cookie = `${REFRESH_TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
  document.cookie = `${USER_KEY}=; path=/; max-age=0; SameSite=Lax`;
}

function persistSession(token, refreshToken, user) {
  const userPayload = JSON.stringify(user || null);
  localStorage.setItem(TOKEN_KEY, token);
  if (refreshToken) localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  localStorage.setItem(USER_KEY, userPayload);
  sessionStorage.setItem(TOKEN_KEY, token);
  if (refreshToken) sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  sessionStorage.setItem(USER_KEY, userPayload);
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${ACCESS_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
  if (refreshToken) {
    document.cookie = `${REFRESH_TOKEN_KEY}=${encodeURIComponent(refreshToken)}; path=/; max-age=${REFRESH_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
  }
  document.cookie = `${USER_KEY}=${encodeURIComponent(userPayload)}; path=/; max-age=${REFRESH_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
}

function readToken() {
  const token = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || readCookie(TOKEN_KEY);
  if (token && isJwtExpired(token)) {
    purgeStoredSession();
    return null;
  }
  return token;
}

function readRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY) || readCookie(REFRESH_TOKEN_KEY);
}

function readUser() {
  const value = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY) || readCookie(USER_KEY);
  if (!value) return null;

  try {
    return JSON.parse(value);
  } catch (error) {
    return null;
  }
}

function readCookie(name) {
  const prefix = `${name}=`;
  const match = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

function isJwtExpired(token) {
  try {
    const payload = JSON.parse(atob(base64UrlToBase64(token.split(".")[1] || "")));
    return typeof payload.exp === "number" && payload.exp <= Math.floor(Date.now() / 1000);
  } catch (error) {
    return true;
  }
}

function base64UrlToBase64(value) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  return base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
}

async function refreshSession() {
  if (!state.refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: state.refreshToken }),
    });
    if (!response.ok) {
      clearSession();
      return false;
    }

    setSession(await response.json());
    return true;
  } catch (error) {
    clearSession();
    return false;
  }
}

function showLogin() {
  $("#loginView").hidden = false;
  $("#officeView").hidden = true;
}

function showOffice() {
  $("#loginView").hidden = true;
  $("#officeView").hidden = false;
  applySidebarState();
  applyNavGroupState();
  $("#userName").textContent = state.user?.full_name || state.user?.email || "Usuario";
  openView("dashboard").catch(() => {
    $("#viewTitle").textContent = "Dashboard";
    showPanel("dashboard");
  });
}

function applySidebarState() {
  const collapsed = localStorage.getItem(SIDEBAR_KEY) === "true";
  $("#officeView").classList.toggle("sidebar-collapsed", collapsed);
  updateSidebarToggle(collapsed);
}

function toggleSidebar() {
  const collapsed = !$("#officeView").classList.contains("sidebar-collapsed");
  localStorage.setItem(SIDEBAR_KEY, String(collapsed));
  $("#officeView").classList.toggle("sidebar-collapsed", collapsed);
  updateSidebarToggle(collapsed);
}

function updateSidebarToggle(collapsed) {
  const button = $("#sidebarToggle");
  if (!button) return;
  const label = collapsed ? "Expandir menu" : "Contraer menu";
  button.setAttribute("aria-label", label);
  button.setAttribute("title", label);
}

function readCollapsedNavGroups() {
  try {
    return JSON.parse(localStorage.getItem(NAV_GROUPS_KEY) || "[]");
  } catch (error) {
    return [];
  }
}

function applyNavGroupState() {
  const collapsedGroups = readCollapsedNavGroups();
  $$("[data-nav-group-panel]").forEach((group) => {
    const key = group.dataset.navGroupPanel;
    const collapsed = collapsedGroups.includes(key);
    group.classList.toggle("collapsed", collapsed);
    const toggle = group.querySelector("[data-nav-group]");
    if (toggle) toggle.setAttribute("aria-expanded", String(!collapsed));
  });
}

function toggleNavGroup(groupKey) {
  const collapsedGroups = new Set(readCollapsedNavGroups());
  if (collapsedGroups.has(groupKey)) {
    collapsedGroups.delete(groupKey);
  } else {
    collapsedGroups.add(groupKey);
  }
  localStorage.setItem(NAV_GROUPS_KEY, JSON.stringify(Array.from(collapsedGroups)));
  applyNavGroupState();
}

async function login(event) {
  event.preventDefault();
  $("#loginError").hidden = true;

  try {
    const data = await apiFetch("/api/v1/auth/backoffice-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: $("#email").value,
        password: $("#password").value,
      }),
    });
    setSession(data);
    window.location.assign(BACKOFFICE_PATH);
  } catch (error) {
    $("#loginError").textContent = readableError(error);
    $("#loginError").hidden = false;
  }
}

async function loadDashboard() {
  const dashboardData = await fetchBackofficeDashboardData();
  const companies = dashboardData.companies || [];
  const condominiums = dashboardData.condominiums || [];
  const tickets = dashboardData.tickets || [];
  const clientCompanies = companies.filter((company) => !isInternalKomiteCompany(company));
  const clientCompanyIds = new Set(clientCompanies.map((company) => String(company.id)));
  const clientCondominiums = condominiums.filter((condominium) => clientCompanyIds.has(String(condominium.company_id)));

  const activeCompanies = countActive(clientCompanies);
  const openTickets = countByStatus(tickets, "open");
  const pendingTickets = countByStatus(tickets, "pending");
  const inProgressTickets = countByStatus(tickets, "in_progress");
  const urgentTickets = tickets.filter((ticket) => ["urgent", "high"].includes(String(ticket.priority || "").toLowerCase()) && !["resolved", "closed"].includes(String(ticket.status || "").toLowerCase())).length;
  const overdueTickets = tickets.filter((ticket) => ticketIsOverdue(ticket)).length;

  $("#metricCompanies").textContent = activeCompanies;
  $("#metricCompaniesTotal").textContent = clientCompanies.length;
  $("#metricTickets").textContent = openTickets;
  $("#metricTicketsBreakdown").textContent = `Pendientes: ${pendingTickets} | En curso: ${inProgressTickets}`;
  $("#metricUrgentTickets").textContent = urgentTickets;
  $("#metricOverdueTickets").textContent = overdueTickets;

  renderTicketsStatusChart(tickets);
  renderTicketsByCompanyChart(tickets, clientCompanies, clientCondominiums);
  renderPriorityTickets(tickets);
  renderRecentCompanies(clientCompanies, clientCondominiums);
  renderSupportSummary({
    tickets,
    activeCompanies,
    totalCompanies: clientCompanies.length,
    activeCondominiums: countActive(clientCondominiums),
    overdueTickets,
  });
}

async function fetchBackofficeDashboardData() {
  try {
    return await apiFetch("/api/v1/backoffice/dashboard");
  } catch (error) {
    const [companies, condominiums, tickets] = await Promise.all([
      fetchAllPages("/api/v1/companies/"),
      fetchAllPages("/api/v1/condominiums/"),
      fetchAllPages("/api/v1/support-tickets/"),
    ]);
    return { companies, condominiums, tickets };
  }
}

function countActive(items) {
  return (items || []).filter((item) => item.status === "active").length;
}

function countByStatus(items, status) {
  return (items || []).filter((item) => item.status === status).length;
}

function isInternalKomiteCompany(company) {
  return String(company?.name || "").trim().toLowerCase() === "komite";
}

function ticketIsOverdue(ticket) {
  if (!ticket.due_date || ["resolved", "closed"].includes(String(ticket.status || "").toLowerCase())) return false;
  const rawDueDate = String(ticket.due_date);
  const dueDate = new Date(rawDueDate.includes("T") ? rawDueDate : `${rawDueDate}T23:59:59`);
  return Number.isFinite(dueDate.getTime()) && dueDate < new Date();
}

function renderTicketsStatusChart(tickets) {
  const statuses = ["open", "pending", "in_progress", "resolved", "closed"];
  const labels = statuses.map((status) => statusLabels[status] || status);
  const values = statuses.map((status) => countByStatus(tickets, status));
  const statusColors = statuses.map((status) => ticketStatusPalette[status].fill);
  const statusBorders = statuses.map((status) => ticketStatusPalette[status].accent);

  const canvas = $("#ticketsStatusChart");
  const fallback = $("#ticketChartFallback");
  if (!window.Chart) {
    fallback.hidden = false;
    fallback.innerHTML = statuses
      .map((status, index) => `<div><strong>${escapeHtml(labels[index])}</strong><span>${values[index]}</span></div>`)
      .join("");
    return;
  }

  fallback.hidden = true;
  if (ticketsStatusChart) ticketsStatusChart.destroy();
  ticketsStatusChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: statusColors,
        borderColor: statusBorders,
        borderWidth: 3,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { boxWidth: 12, color: "#172536" } },
      },
      cutout: "62%",
    },
  });
}

function renderTicketsByCompanyChart(tickets, companies, condominiums) {
  const canvas = $("#ticketsCompanyChart");
  const fallback = $("#ticketCompanyChartFallback");
  const safeTickets = tickets || [];
  const condominiumLookup = new Map((condominiums || []).map((condominium) => [String(condominium.id), condominium.name]));
  const companiesWithTickets = companies
    .filter((company) => safeTickets.some((ticket) => sameId(ticket.company_id, company.id)))
    .slice(0, 8);
  const labels = companiesWithTickets.map((company) => company.name || "Empresa");
  const companyCondominiumBuckets = companiesWithTickets.map((company) => {
    const counts = new Map();
    safeTickets
      .filter((ticket) => sameId(ticket.company_id, company.id))
      .forEach((ticket) => {
        const condominiumName = ticketCondominiumName(ticket, condominiumLookup);
        counts.set(condominiumName, (counts.get(condominiumName) || 0) + 1);
      });
    return Array.from(counts.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((left, right) => right.count - left.count || left.name.localeCompare(right.name));
  });
  const maxCondominiums = Math.max(0, ...companyCondominiumBuckets.map((items) => items.length));

  if (!companiesWithTickets.length || !maxCondominiums) {
    if (ticketsCompanyChart) ticketsCompanyChart.destroy();
    fallback.hidden = false;
    fallback.innerHTML = `<div><strong>Sin datos</strong><span>Crea tickets con condominio asociado.</span></div>`;
    return;
  }

  const datasets = Array.from({ length: maxCondominiums }, (_, index) => ({
    label: `Condominio ${index + 1}`,
    data: companyCondominiumBuckets.map((items) => items[index]?.count || 0),
    condominiumNames: companyCondominiumBuckets.map((items) => items[index]?.name || ""),
    backgroundColor: companyChartPalette[index % companyChartPalette.length].background,
    borderColor: "transparent",
    borderWidth: 0,
    borderRadius: 4,
  }));

  if (!window.Chart) {
    fallback.hidden = false;
    fallback.innerHTML = companiesWithTickets.map((company) => {
      const total = safeTickets.filter((ticket) => sameId(ticket.company_id, company.id)).length;
      return `<div><strong>${escapeHtml(company.name)}</strong><span>${total}</span></div>`;
    }).join("");
    return;
  }

  fallback.hidden = true;
  if (ticketsCompanyChart) ticketsCompanyChart.destroy();
  ticketsCompanyChart = new Chart(canvas, {
    type: "bar",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true, ticks: { color: "#172536" }, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, ticks: { precision: 0, color: "#667789" } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: "index",
          intersect: false,
          itemSort(left, right) {
            return right.datasetIndex - left.datasetIndex;
          },
          callbacks: {
            label(context) {
              const condominiumName = context.dataset.condominiumNames?.[context.dataIndex] || context.dataset.label;
              return `${condominiumName}: ${context.parsed.y}`;
            },
          },
        },
        outerStackBorder: {
          enabled: false,
          color: "#0f172a",
          width: 1.25,
        },
        stackPercentageLabels: {
          enabled: true,
          color: "#ffffff",
          minHeight: 18,
        },
      },
    },
  });
}

function renderPriorityTickets(tickets) {
  const priorityTickets = [...tickets]
    .filter((ticket) => !["resolved", "closed"].includes(String(ticket.status || "").toLowerCase()))
    .sort((a, b) => priorityWeight(b.priority) - priorityWeight(a.priority))
    .slice(0, 5);

  const target = $("#priorityTickets");
  target.innerHTML = priorityTickets.length
    ? priorityTickets.map((ticket) => `<div class="list-item"><strong>${escapeHtml(ticket.subject || "Ticket")}</strong><span>${escapeHtml(priorityLabel(ticket.priority))} | ${escapeHtml(statusLabels[ticket.status] || ticket.status || "Sin estado")}</span></div>`).join("")
    : `<div class="list-item"><span>Sin tickets prioritarios.</span></div>`;
}

function renderRecentCompanies(companies, condominiums) {
  const recentCompanies = [...companies].slice(0, 5);
  const target = $("#recentCompanies");
  target.innerHTML = recentCompanies.length
    ? recentCompanies.map((company) => {
      const totalCondominiums = condominiums.filter((condominium) => sameId(condominium.company_id, company.id)).length;
      return `<div class="list-item"><strong>${escapeHtml(company.name || "Empresa")}</strong><span>${escapeHtml(statusLabels[company.status] || company.status || "Sin estado")} | Condominios: ${totalCondominiums}</span></div>`;
    }).join("")
    : `<div class="list-item"><span>Sin empresas registradas.</span></div>`;
}

function renderSupportSummary(summary) {
  const target = $("#supportSummary");
  target.innerHTML = [
    ["Modo de datos", "Tickets reales en BBDD"],
    ["Empresas activas", `${summary.activeCompanies} de ${summary.totalCompanies}`],
    ["Condominios activos", String(summary.activeCondominiums)],
    ["Tickets vencidos", String(summary.overdueTickets)],
  ].map(([label, value]) => `<div class="list-item"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`).join("");
}

function ticketCondominiumName(ticket, condominiumLookup = new Map()) {
  if (ticket?.condominium_id) {
    return condominiumLookup.get(String(ticket.condominium_id)) || formatCell(ticket.condominium_id);
  }
  return "Ticket general empresa";
}

function sameId(left, right) {
  return String(left || "") === String(right || "");
}

function priorityWeight(priority) {
  return { urgent: 4, high: 3, medium: 2, low: 1 }[String(priority || "").toLowerCase()] || 0;
}

function priorityLabel(priority) {
  return { urgent: "Urgente", high: "Alta", medium: "Media", low: "Baja" }[String(priority || "").toLowerCase()] || "Sin prioridad";
}

async function fetchAllPages(basePath, pageSize = 200) {
  const firstPage = await fetchPage(`${basePath}?page=1&page_size=${pageSize}`);
  const pages = firstPage.meta?.pages || 1;
  if (pages <= 1) return firstPage.items;

  const rest = await Promise.all(
    Array.from({ length: pages - 1 }, (_, index) => fetchPage(`${basePath}?page=${index + 2}&page_size=${pageSize}`)),
  );
  return [firstPage, ...rest].flatMap((page) => page.items || []);
}

async function fetchPage(path) {
  try {
    const data = await apiFetch(path);
    return {
      items: data.items || [],
      meta: data.meta || { total: data.items?.length || 0 },
    };
  } catch (error) {
    return { items: [], meta: { total: 0 } };
  }
}

function renderList(selector, items, titleKey, subtitleKey) {
  const target = $(selector);
  target.innerHTML = "";

  if (!items.length) {
    target.innerHTML = `<div class="list-item"><span>Sin registros.</span></div>`;
    return;
  }

  for (const item of items) {
    const element = document.createElement("div");
    element.className = "list-item";
    element.innerHTML = `<strong>${escapeHtml(item[titleKey] || "Registro")}</strong><span>${escapeHtml(item[subtitleKey] || "")}</span>`;
    target.appendChild(element);
  }
}

function showPanel(panel) {
  $("#dashboardPanel").hidden = panel !== "dashboard";
  $("#tablePanel").hidden = panel !== "table";
  $("#condominiumFormPanel").hidden = panel !== "condominiumForm";
  $("#companyFormPanel").hidden = panel !== "companyForm";
  $("#userFormPanel").hidden = panel !== "userForm";
  $("#genericFormPanel").hidden = panel !== "genericForm";
  $("#audioPanel").hidden = panel !== "audio";
  $("#toolsPanel").hidden = panel !== "tools";
  $("#placeholderPanel").hidden = panel !== "placeholder";
}

async function openView(view) {
  state.currentView = view;
  $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  scrollViewToTop();

  if (view === "dashboard") {
    $("#viewTitle").textContent = "Dashboard";
    showPanel("dashboard");
    await loadDashboard();
    return;
  }

  if (view === "audio") {
    $("#viewTitle").textContent = "Audio IA";
    showPanel("audio");
    return;
  }

  if (view === "tools") {
    $("#viewTitle").textContent = "Herramientas";
    showPanel("tools");
    showToolsCatalog();
    return;
  }

  if (placeholders[view]) {
    $("#viewTitle").textContent = placeholders[view].title;
    $("#placeholderTitle").textContent = placeholders[view].title;
    $("#placeholderText").textContent = placeholders[view].text;
    showPanel("placeholder");
    return;
  }

  if (!resources[view]) {
    $("#viewTitle").textContent = "Modulo";
    $("#placeholderTitle").textContent = "Modulo no disponible";
    $("#placeholderText").textContent = "Esta opción aún no tiene una ruta asociada en el backoffice.";
    showPanel("placeholder");
    return;
  }

  $("#viewTitle").textContent = resources[view].title;
  $("#searchInput").value = "";
  $("#companyFilter").value = "";
  $("#ticketCompanyFilter").value = "";
  $("#ticketCondominiumFilter").value = "";
  $("#ticketStatusFilter").value = "";
  state.tablePage = 1;
  $("#companyFilter").hidden = !["condominiums", "committeeMembers", "users", "inspectionTemplates", "inspectionTemplateSections", "inspectionTemplateItems", "aiPromptTemplates"].includes(view);
  $("#ticketCompanyFilter").hidden = view !== "supportTickets";
  $("#ticketCondominiumFilter").hidden = view !== "supportTickets";
  $("#ticketStatusFilter").hidden = view !== "supportTickets";
  $("#newCompanyButton").hidden = view !== "companies";
  $("#newCondominiumButton").hidden = view !== "condominiums";
  $("#newUserButton").hidden = view !== "users";
  $("#newGenericButton").hidden = !resources[view].fields;
  if (resources[view].fields) {
    $("#newGenericButtonLabel").textContent = resources[view].createLabel || "Nuevo";
  }
  if (["condominiums", "users"].includes(view)) {
    await ensureCompaniesLoaded();
    populateCompanyFilter();
  }
  if (view === "committeeMembers") {
    await ensureUserLookupsLoaded();
    populateCompanyFilter();
  }
  if (["inspectionTemplates", "inspectionTemplateSections", "inspectionTemplateItems", "aiPromptTemplates"].includes(view)) {
    await ensureUserLookupsLoaded();
    populateCompanyFilter();
  }
  if (view === "supportTickets") {
    await ensureUserLookupsLoaded();
    populateTicketFilters();
  }
  showPanel("table");
  await loadTable();
}

function scrollViewToTop() {
  requestAnimationFrame(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    const workspace = document.querySelector(".workspace");
    if (workspace) {
      workspace.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    }
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  });
}

async function loadTable() {
  const resource = resources[state.currentView];
  const query = buildTableQueryParams();
  const data = await apiFetch(`${resource.endpoint}?${query}`);
  state.currentItems = data.items || [];
  state.tableMeta = normalizeTableMeta(data.meta, state.currentItems.length);
  renderTable(resource.columns, filteredTableItems());
  renderPagination();
}

function buildTableQueryParams() {
  const params = new URLSearchParams({
    page: String(state.tablePage),
    page_size: String(state.tablePageSize),
  });
  const search = $("#searchInput").value.trim();
  if (search) params.set("q", search);

  if (state.currentView === "supportTickets") {
    const companyId = $("#ticketCompanyFilter").value;
    const condominiumId = $("#ticketCondominiumFilter").value;
    const status = $("#ticketStatusFilter").value;
    if (companyId) params.set("filter_company_id", companyId);
    if (condominiumId) params.set("filter_condominium_id", condominiumId);
    if (status) params.set("filter_status", status);
  }

  if (["condominiums", "committeeMembers", "users", "inspectionTemplates", "inspectionTemplateSections", "inspectionTemplateItems", "aiPromptTemplates"].includes(state.currentView)) {
    const companyId = $("#companyFilter").value;
    if (companyId) params.set("filter_company_id", companyId);
  }

  return params.toString();
}

function filteredTableItems() {
  let items = state.currentItems || [];
  if (["condominiums", "committeeMembers", "users", "inspectionTemplates", "inspectionTemplateSections", "inspectionTemplateItems", "aiPromptTemplates"].includes(state.currentView)) {
    const companyId = $("#companyFilter").value;
    if (companyId) {
      items = items.filter((item) => sameId(item.company_id, companyId));
    }
  }
  return items;
}

function renderTable(columns, items) {
  const actionColumn = ["condominiums", "companies", "users"].includes(state.currentView) || Boolean(resources[state.currentView]?.fields);
  $("#tableHead").innerHTML = `<tr>${columns.map((column) => `<th>${escapeHtml(labelForColumn(column))}</th>`).join("")}${actionColumn ? "<th>Acciones</th>" : ""}</tr>`;
  if (!items.length) {
    $("#tableBody").innerHTML = `<tr><td colspan="${columns.length + (actionColumn ? 1 : 0)}" class="empty-table">Sin registros para mostrar.</td></tr>`;
    return;
  }
  $("#tableBody").innerHTML = items
    .map((item) => {
      const cells = columns.map((column) => `<td>${formatTableCell(column, item[column])}</td>`).join("");
      if (!actionColumn) return `<tr>${cells}</tr>`;
      const actions = renderRowActions(state.currentView, item.id);
      return `<tr>${cells}<td>${actions}</td></tr>`;
    })
    .join("");
  bindCondominiumRowActions();
  bindCompanyRowActions();
  bindUserRowActions();
  bindGenericRowActions();
}

function normalizeTableMeta(meta, fallbackCount) {
  const pageSize = Number(meta?.page_size || state.tablePageSize);
  const total = Number(meta?.total ?? fallbackCount);
  const pages = Math.max(1, Number(meta?.pages || Math.ceil(total / pageSize) || 1));
  const page = Math.min(Math.max(1, Number(meta?.page || state.tablePage)), pages);
  state.tablePage = page;
  return { total, page, page_size: pageSize, pages };
}

function renderPagination() {
  const meta = state.tableMeta;
  const start = meta.total ? (meta.page - 1) * meta.page_size + 1 : 0;
  const end = Math.min(meta.page * meta.page_size, meta.total);
  $("#paginationSummary").textContent = meta.total ? `${start}-${end} de ${meta.total} registros` : "Sin registros";
  $("#pageIndicator").textContent = `Página ${meta.page} de ${meta.pages}`;
  $("#pageSizeSelect").value = String(state.tablePageSize);

  const isFirst = meta.page <= 1;
  const isLast = meta.page >= meta.pages;
  $("#firstPageButton").disabled = isFirst;
  $("#prevPageButton").disabled = isFirst;
  $("#nextPageButton").disabled = isLast;
  $("#lastPageButton").disabled = isLast;
}

async function goToTablePage(page) {
  const pages = state.tableMeta.pages || 1;
  state.tablePage = Math.min(Math.max(1, page), pages);
  await loadTable();
}

function labelForColumn(column) {
  return columnLabels[column] || column.replaceAll("_", " ");
}

function formatTableCell(column, value) {
  if (column === "status") return renderStatusBadge(value);
  if (["is_system", "receives_notifications", "is_active", "requires_evidence"].includes(column)) return renderBooleanBadge(value);
  if (column === "company_id") return escapeHtml(companyName(value));
  if (column === "condominium_id") return escapeHtml(condominiumName(value));
  if (column === "unit_id") return escapeHtml(unitName(value));
  if (column === "unit_contact_id") return escapeHtml(unitContactName(value));
  if (column === "user_id") return escapeHtml(userName(value));
  if (column === "template_id") return escapeHtml(inspectionTemplateName(value));
  if (column === "section_id") return escapeHtml(inspectionTemplateSectionName(value));
  if (column === "position") return escapeHtml(positionLabels[value] || formatCell(value));
  if (["company_profile", "role_code", "default_responsible_profile"].includes(column)) return escapeHtml(roleLabels[value] || formatCell(value));
  if (column === "template_type") return escapeHtml(templateTypeLabels[value] || formatCell(value));
  if (column === "event_type") return escapeHtml(eventTypeLabels[value] || formatCell(value));
  if (column === "inspection_type") return escapeHtml(inspectionTypeLabels[value] || formatCell(value));
  if (column === "periodicity") return escapeHtml(periodicityLabels[value] || formatCell(value));
  return escapeHtml(formatCell(value));
}

function companyName(companyId) {
  const company = state.companies.find((item) => sameId(item.id, companyId));
  return company?.name || formatCell(companyId);
}

function condominiumName(condominiumId) {
  if (!condominiumId) return "";
  const condominium = state.condominiums.find((item) => sameId(item.id, condominiumId));
  return condominium?.name || formatCell(condominiumId);
}

function unitName(unitId) {
  if (!unitId) return "";
  const unit = state.units.find((item) => sameId(item.id, unitId));
  return unit?.identifier || formatCell(unitId);
}

function unitContactName(contactId) {
  if (!contactId) return "";
  const contact = state.unitContacts.find((item) => sameId(item.id, contactId));
  return contact?.full_name || formatCell(contactId);
}

function userName(userId) {
  if (!userId) return "";
  const user = state.usersLookup.find((item) => sameId(item.id, userId));
  return user?.full_name || user?.email || formatCell(userId);
}

function inspectionTemplateName(templateId) {
  if (!templateId) return "";
  const template = state.inspectionTemplates.find((item) => sameId(item.id, templateId));
  return template?.name || formatCell(templateId);
}

function inspectionTemplateSectionName(sectionId) {
  if (!sectionId) return "";
  const section = state.inspectionTemplateSections.find((item) => sameId(item.id, sectionId));
  return section?.name || formatCell(sectionId);
}

function renderStatusBadge(status) {
  const normalized = String(status || "").toLowerCase();
  const label = statusLabels[normalized] || formatCell(status);
  if (ticketStatusPalette[normalized]) {
    const palette = ticketStatusPalette[normalized];
    return `<span class="status-badge is-ticket-status" style="--badge-bg: ${palette.background}; --badge-color: ${palette.color}; --badge-accent: ${palette.accent};"><span aria-hidden="true"></span>${escapeHtml(label)}</span>`;
  }
  const className = normalized === "active" ? "is-active" : normalized === "inactive" ? "is-inactive" : "is-neutral";
  return `<span class="status-badge ${className}"><span aria-hidden="true"></span>${escapeHtml(label)}</span>`;
}

function renderImportStatusBadge(status, preview) {
  const normalized = String(status || "").trim().toLowerCase();
  if (!preview) return renderStatusBadge(status);

  const previewLabels = {
    creado: "se va a crear",
    "se va a crear": "se va a crear",
    updated: "se va a actualizar",
    actualizado: "se va a actualizar",
    "se va a actualizar": "se va a actualizar",
    created: "se va a crear",
    skipped: "se va a omitir",
    omitido: "se va a omitir",
    "se va a omitir": "se va a omitir",
  };
  const label = previewLabels[normalized] || `se va a ${formatCell(status)}`;
  const className = ["creado", "created", "se va a crear"].includes(normalized)
    ? "is-active"
    : ["skipped", "omitido", "se va a omitir"].includes(normalized)
      ? "is-inactive"
      : "is-neutral";
  return `<span class="status-badge ${className}"><span aria-hidden="true"></span>${escapeHtml(label)}</span>`;
}

function renderBooleanBadge(value) {
  const active = Boolean(value);
  return `<span class="status-badge ${active ? "is-active" : "is-inactive"}"><span aria-hidden="true"></span>${active ? "Si" : "No"}</span>`;
}

function renderRowActions(view, id) {
  if (view === "companies") return renderCompanyActions(id);
  if (view === "users") return renderUserActions(id);
  if (resources[view]?.fields) return renderGenericActions(id);
  return renderCondominiumActions(id);
}

function renderGenericActions(id) {
  const safeId = escapeHtml(id);
  const canDuplicateAndExport = ["inspectionTemplates", "aiPromptTemplates"].includes(state.currentView);
  const duplicateKind = state.currentView === "aiPromptTemplates" ? "aiPrompt" : "inspection";
  const duplicateButton = canDuplicateAndExport
    ? `<button class="duplicate-row icon-button" type="button" data-duplicate-template="${safeId}" data-duplicate-kind="${duplicateKind}" aria-label="Duplicar para condominio" title="Duplicar para condominio">
        <svg aria-hidden="true"><use href="#icon-copy"></use></svg>
      </button>
      <button class="export-row icon-button" type="button" data-export-template="${safeId}" data-export-kind="${duplicateKind}" aria-label="Descargar" title="Descargar">
        <svg aria-hidden="true"><use href="#icon-download"></use></svg>
      </button>`
    : "";
  return `
    <div class="table-actions">
      ${duplicateButton}
      <button class="edit-row icon-button" type="button" data-edit-generic="${safeId}" aria-label="Editar" title="Editar">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-generic="${safeId}" aria-label="Borrar" title="Borrar">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
      </button>
    </div>
  `;
}

function bindGenericRowActions() {
  $$("[data-duplicate-template]").forEach((button) => {
    button.addEventListener("click", () => openDuplicateTemplateModal(button.dataset.duplicateTemplate, button.dataset.duplicateKind || "inspection"));
  });
  $$("[data-export-template]").forEach((button) => {
    button.addEventListener("click", () => exportTemplateResource(button.dataset.exportTemplate, button.dataset.exportKind || "inspection"));
  });
  $$("[data-edit-generic]").forEach((button) => {
    button.addEventListener("click", () => openGenericForm(button.dataset.editGeneric));
  });
  $$("[data-delete-generic]").forEach((button) => {
    button.addEventListener("click", () => deleteGenericEntity(button.dataset.deleteGeneric));
  });
}

function renderCondominiumActions(id) {
  const safeId = escapeHtml(id);
  return `
    <div class="table-actions">
      <button class="edit-row icon-button" type="button" data-edit-condominium="${safeId}" aria-label="Editar" title="Editar">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-condominium="${safeId}" aria-label="Borrar" title="Borrar">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
      </button>
    </div>
  `;
}

function bindCondominiumRowActions() {
  $$("[data-edit-condominium]").forEach((button) => {
    button.addEventListener("click", () => openCondominiumForm(button.dataset.editCondominium));
  });
  $$("[data-delete-condominium]").forEach((button) => {
    button.addEventListener("click", () => deleteCondominium(button.dataset.deleteCondominium));
  });
}

function renderCompanyActions(id) {
  const safeId = escapeHtml(id);
  return `
    <div class="table-actions">
      <button class="edit-row icon-button" type="button" data-edit-company="${safeId}" aria-label="Editar" title="Editar">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-company="${safeId}" aria-label="Borrar" title="Borrar">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
      </button>
    </div>
  `;
}

function bindCompanyRowActions() {
  $$("[data-edit-company]").forEach((button) => {
    button.addEventListener("click", () => openCompanyForm(button.dataset.editCompany));
  });
  $$("[data-delete-company]").forEach((button) => {
    button.addEventListener("click", () => deleteCompany(button.dataset.deleteCompany));
  });
}

function renderUserActions(id) {
  const safeId = escapeHtml(id);
  return `
    <div class="table-actions">
      <button class="edit-row icon-button" type="button" data-edit-user="${safeId}" aria-label="Editar" title="Editar">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-user="${safeId}" aria-label="Borrar" title="Borrar">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
      </button>
    </div>
  `;
}

function bindUserRowActions() {
  $$("[data-edit-user]").forEach((button) => {
    button.addEventListener("click", () => openUserForm(button.dataset.editUser));
  });
  $$("[data-delete-user]").forEach((button) => {
    button.addEventListener("click", () => deleteUser(button.dataset.deleteUser));
  });
}

function formatCell(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

async function ensureCompaniesLoaded() {
  const data = await apiFetch("/api/v1/companies/?page=1&page_size=200");
  state.companies = data.items || [];
}

function populateCompanyFilter() {
  const options = state.companies
    .filter((company) => !isInternalKomiteCompany(company))
    .map((company) => `<option value="${escapeHtml(company.id)}">${escapeHtml(company.name || "Empresa")}</option>`)
    .join("");
  $("#companyFilter").innerHTML = `<option value="">Todas las empresas</option>${options}`;
}

function populateTicketFilters() {
  const companies = state.companies.filter((company) => !isInternalKomiteCompany(company));
  $("#ticketCompanyFilter").innerHTML = `<option value="">Todas las empresas</option>${companies
    .map((company) => `<option value="${escapeHtml(company.id)}">${escapeHtml(company.name || "Empresa")}</option>`)
    .join("")}`;
  $("#ticketStatusFilter").innerHTML = `<option value="">Todos los estados</option>${resources.supportTickets.fields
    .find((field) => field.name === "status")
    .options.map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`)
    .join("")}`;
  populateTicketCondominiumFilter();
}

function populateTicketCondominiumFilter() {
  const companyId = $("#ticketCompanyFilter").value;
  const condominiums = state.condominiums
    .filter((condominium) => !companyId || sameId(condominium.company_id, companyId))
    .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")));
  $("#ticketCondominiumFilter").innerHTML = `<option value="">Todos los condominios</option>${condominiums
    .map((condominium) => `<option value="${escapeHtml(condominium.id)}">${escapeHtml(condominium.name || "Condominio")}</option>`)
    .join("")}`;
}

async function ensureUserLookupsLoaded() {
  const [companies, condominiums, roles, units, users, unitContacts, operationalStaff, inspectionTemplates, inspectionTemplateSections] = await Promise.all([
    fetchAllPages("/api/v1/companies/"),
    fetchAllPages("/api/v1/condominiums/"),
    apiFetch("/api/v1/roles/?page=1&page_size=200"),
    fetchAllPages("/api/v1/units/"),
    fetchAllPages("/api/v1/users/"),
    fetchAllPages("/api/v1/unit-contacts/"),
    fetchAllPages("/api/v1/condominium-operational-staff/"),
    fetchAllPages("/api/v1/inspection-templates/"),
    fetchAllPages("/api/v1/inspection-template-sections/"),
  ]);
  state.companies = Array.isArray(companies) ? companies : companies.items || [];
  state.condominiums = Array.isArray(condominiums) ? condominiums : condominiums.items || [];
  state.roles = (roles.items || []).filter((role) => ["vecino", "comite", "supervisor", "conserje"].includes(role.code));
  state.units = Array.isArray(units) ? units : units.items || [];
  state.usersLookup = Array.isArray(users) ? users : users.items || [];
  state.unitContacts = Array.isArray(unitContacts) ? unitContacts : unitContacts.items || [];
  state.operationalStaff = Array.isArray(operationalStaff) ? operationalStaff : operationalStaff.items || [];
  state.inspectionTemplates = Array.isArray(inspectionTemplates) ? inspectionTemplates : inspectionTemplates.items || [];
  state.inspectionTemplateSections = Array.isArray(inspectionTemplateSections) ? inspectionTemplateSections : inspectionTemplateSections.items || [];
}

async function exportTemplateResource(templateId, kind = "inspection") {
  try {
    const template = state.currentItems.find((entry) => sameId(entry.id, templateId))
      || (kind === "inspection" ? state.inspectionTemplates.find((entry) => sameId(entry.id, templateId)) : null);
    const isAiPrompt = kind === "aiPrompt";
    const baseName = normalizeSearch(template?.key || template?.name || "komite").replaceAll(" ", "_");
    const fallbackName = isAiPrompt ? `prompt_ia_${baseName}.json` : `plantilla_${baseName}.xlsx`;
    const endpoint = isAiPrompt
      ? `/api/v1/ai-prompt-templates/${templateId}/export`
      : `/api/v1/inspection-templates/${templateId}/export`;
    await apiDownload(endpoint, fallbackName);
    showToast({
      title: isAiPrompt ? "Prompt descargado" : "Plantilla exportada",
      message: isAiPrompt ? "Se descargo el JSON del prompt IA." : "Se descargo el Excel de la plantilla.",
    });
  } catch (error) {
    window.alert(readableError(error));
  }
}

async function openGenericForm(id = null) {
  const resource = resources[state.currentView];
  if (!resource?.fields) return;

  $("#genericFormError").hidden = true;
  if (resource.fields.some((field) => ["company", "condominium", "user", "unit", "unit_contact", "inspection_template", "inspection_template_section"].includes(field.type))) {
    await ensureUserLookupsLoaded();
  }

  const item = id ? state.currentItems.find((entry) => entry.id === id) || (await apiFetch(`${resource.endpoint}${id}`)) : null;
  $("#genericId").value = item?.id || "";
  $("#viewTitle").textContent = item ? `Editar ${resource.singular}` : resource.createLabel;
  $("#genericFormEyebrow").textContent = resource.title;
  $("#genericFormTitle").textContent = item ? `Editar ${resource.singular}` : resource.createLabel;
  setRecordId("#genericRecordId", item?.id);
  $("#saveGenericButton span").textContent = `Guardar ${resource.singular}`;
  $("#deleteGenericButton").hidden = !item;
  renderGenericFormFields(resource, item);
  showPanel("genericForm");
}

function setRecordId(selector, id) {
  const element = $(selector);
  if (!element) return;
  element.hidden = !id;
  element.textContent = id ? `ID: ${id}` : "";
}

function renderGenericFormFields(resource, item) {
  $("#genericFormFields").innerHTML = resource.fields.map((field) => renderGenericField(field, item)).join("");
  bindSearchableSelects();
  bindGenericFieldDependencies();
}

function renderGenericField(field, item) {
  const value = item?.[field.name] ?? field.defaultValue ?? "";
  const required = field.required ? " required" : "";
  const maxlength = field.maxLength ? ` maxlength="${field.maxLength}"` : "";
  const label = escapeHtml(field.label);
  const name = escapeHtml(field.name);

  if (field.type === "select") {
    return `<label>${label}<select data-generic-field="${name}"${required}>${field.options
      .map(([optionValue, optionLabel]) => `<option value="${escapeHtml(optionValue)}"${value === optionValue ? " selected" : ""}>${escapeHtml(optionLabel)}</option>`)
      .join("")}</select></label>`;
  }

  if (field.type === "company") {
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"${required}><option value="">Selecciona empresa</option>${state.companies
      .map((company) => `<option value="${escapeHtml(company.id)}"${value === company.id ? " selected" : ""}>${escapeHtml(company.name)}</option>`)
      .join("")}</select>`, "Buscar empresa");
  }

  if (field.type === "condominium") {
    const emptyLabel = field.emptyLabel || "Sin condominio";
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"${required}><option value="">${escapeHtml(emptyLabel)}</option>${state.condominiums
      .map((condominium) => `<option value="${escapeHtml(condominium.id)}" data-company-id="${escapeHtml(condominium.company_id || "")}"${value === condominium.id ? " selected" : ""}>${escapeHtml(condominium.name)}</option>`)
      .join("")}</select>`, "Buscar condominio");
  }

  if (field.type === "unit") {
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"><option value="">Sin unidad</option>${state.units
      .map((unit) => `<option value="${escapeHtml(unit.id)}" data-condominium-id="${escapeHtml(unit.condominium_id || "")}"${value === unit.id ? " selected" : ""}>${escapeHtml(unit.identifier || unit.id)}</option>`)
      .join("")}</select>`, "Buscar unidad");
  }

  if (field.type === "unit_contact") {
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"><option value="">Sin contacto asociado</option>${state.unitContacts
      .map((contact) => `<option value="${escapeHtml(contact.id)}" data-condominium-id="${escapeHtml(contact.condominium_id || "")}" data-unit-id="${escapeHtml(contact.unit_id || "")}" data-full-name="${escapeHtml(contact.full_name || "")}" data-email="${escapeHtml(contact.email || "")}" data-phone="${escapeHtml(contact.phone || "")}"${value === contact.id ? " selected" : ""}>${escapeHtml(contact.full_name || contact.email || contact.id)}</option>`)
      .join("")}</select>`, "Buscar vecino");
  }

  if (field.type === "user") {
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"><option value="">Sin asignar</option>${state.usersLookup
      .map((user) => `<option value="${escapeHtml(user.id)}"${value === user.id ? " selected" : ""}>${escapeHtml(user.full_name || user.email)}</option>`)
      .join("")}</select>`, "Buscar usuario");
  }

  if (field.type === "inspection_template") {
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"${required}><option value="">Selecciona plantilla</option>${state.inspectionTemplates
      .map((template) => `<option value="${escapeHtml(template.id)}" data-company-id="${escapeHtml(template.company_id || "")}"${value === template.id ? " selected" : ""}>${escapeHtml(template.name || template.id)}</option>`)
      .join("")}</select>`, "Buscar plantilla");
  }

  if (field.type === "inspection_template_section") {
    return renderSearchableSelect(label, name, `<select data-generic-field="${name}"><option value="">Sin secci\u00f3n</option>${state.inspectionTemplateSections
      .map((section) => `<option value="${escapeHtml(section.id)}" data-template-id="${escapeHtml(section.template_id || "")}" data-company-id="${escapeHtml(section.company_id || "")}"${value === section.id ? " selected" : ""}>${escapeHtml(section.name || section.id)}</option>`)
      .join("")}</select>`, "Buscar secci\u00f3n");
  }

  if (field.type === "textarea" || field.type === "json") {
    const textareaValue = field.type === "json" ? JSON.stringify(value ?? field.defaultValue ?? {}, null, 2) : value || "";
    return `<label class="span-2">${label}<textarea data-generic-field="${name}" data-field-type="${field.type}" rows="4"${required}>${escapeHtml(textareaValue)}</textarea></label>`;
  }

  if (field.type === "checkbox") {
    const checked = value === true || value === "true" ? " checked" : "";
    return `<label class="switch-row"><input data-generic-field="${name}" type="checkbox"${checked} /><span class="switch-slider" aria-hidden="true"></span><span>${label}</span></label>`;
  }

  const inputType = field.type === "datetime" ? "datetime-local" : field.type || "text";
  const inputValue = field.type === "datetime" && value ? String(value).slice(0, 16) : value;
  return `<label>${label}<input data-generic-field="${name}" type="${inputType}" value="${escapeHtml(inputValue ?? "")}"${required}${maxlength} /></label>`;
}

function renderSearchableSelect(label, name, selectHtml, placeholder) {
  return `<label class="searchable-select-field">${label}<input class="select-search-input" data-select-search="${name}" type="search" placeholder="${escapeHtml(placeholder)}" autocomplete="off" />${selectHtml}</label>`;
}

function bindSearchableSelects() {
  $$("[data-select-search]").forEach((input) => {
    const fieldName = input.dataset.selectSearch;
    const select = $(`[data-generic-field="${fieldName}"]`);
    if (!select) return;
    const applySearch = () => filterSelectOptions(select, input.value);
    input.addEventListener("input", applySearch);
    select.addEventListener("change", () => {
      input.value = "";
      filterSelectOptions(select, "");
    });
    applySearch();
  });
}

function filterSelectOptions(select, searchText) {
  const normalizedSearch = normalizeSearch(searchText);
  Array.from(select.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      option.dataset.searchHidden = "false";
      return;
    }
    const hiddenBySearch = Boolean(normalizedSearch && !normalizeSearch(option.textContent).includes(normalizedSearch));
    option.dataset.searchHidden = hiddenBySearch ? "true" : "false";
    option.hidden = hiddenBySearch || option.dataset.dependencyHidden === "true";
  });
}

function setOptionDependencyHidden(option, hidden) {
  option.dataset.dependencyHidden = hidden ? "true" : "false";
  option.hidden = hidden || option.dataset.searchHidden === "true";
}

function normalizeSearch(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function buildGenericPayload(resource) {
  const payload = {};
  resource.fields.forEach((field) => {
    const element = $(`[data-generic-field="${field.name}"]`);
    if (!element) return;
    if (field.type === "json") {
      payload[field.name] = parseJsonText(element.value, field.defaultValue ?? {});
      return;
    }
    if (field.type === "checkbox") {
      payload[field.name] = element.checked;
      return;
    }
    if (field.type === "number") {
      payload[field.name] = element.value === "" ? field.defaultValue ?? null : Number(element.value);
      return;
    }
    payload[field.name] = emptyToNull(element.value);
  });
  return payload;
}

function parseJsonText(value, fallback) {
  const clean = value.trim();
  if (!clean) return fallback;
  return JSON.parse(clean);
}

async function saveGenericEntity(event) {
  event.preventDefault();
  const resource = resources[state.currentView];
  if (!resource?.fields) return;
  $("#genericFormError").hidden = true;

  try {
    const id = $("#genericId").value;
    const payload = buildGenericPayload(resource);
    if (state.currentView === "committeeMembers" && payload.status !== "inactive") {
      const confirmed = await confirmAction({
        title: "Asignar rol Comité",
        message: "Al guardar este miembro, si la persona tiene usuario asociado o coincide por email, adquirirá automáticamente el rol Comité para el condominio seleccionado.",
        acceptLabel: "Guardar y asignar rol",
      });
      if (!confirmed) return;
    }
    await apiFetch(id ? `${resource.endpoint}${id}` : resource.endpoint, {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await returnToGenericList();
    showToast({
      title: id ? `${capitalize(resource.singular)} actualizado` : `${capitalize(resource.singular)} creado`,
      message: "Los cambios se guardaron correctamente.",
    });
  } catch (error) {
    $("#genericFormError").textContent = readableError(error);
    $("#genericFormError").hidden = false;
  }
}

async function deleteGenericEntity(id = $("#genericId").value) {
  const resource = resources[state.currentView];
  if (!resource?.fields || !id) return;
  const confirmed = await confirmAction({
    title: `Borrar ${resource.singular}`,
    message: `Esta acción eliminará el ${resource.singular} seleccionado.`,
    acceptLabel: `Borrar ${resource.singular}`,
  });
  if (!confirmed) return;

  try {
    await apiFetch(`${resource.endpoint}${id}`, { method: "DELETE" });
    await returnToGenericList();
    showToast({
      title: `${capitalize(resource.singular)} borrado`,
      message: "El registro se elimino correctamente.",
    });
  } catch (error) {
    window.alert(readableError(error));
  }
}

async function openDuplicateTemplateModal(templateId, kind = "inspection") {
  try {
    await ensureUserLookupsLoaded();
    state.duplicateTemplateId = templateId;
    state.duplicateTemplateKind = kind;
    const isAiPrompt = kind === "aiPrompt";
    const template = state.currentItems.find((entry) => sameId(entry.id, templateId))
      || (!isAiPrompt ? state.inspectionTemplates.find((entry) => sameId(entry.id, templateId)) : null)
      || await apiFetch(isAiPrompt ? `/api/v1/ai-prompt-templates/${templateId}` : `/api/v1/inspection-templates/${templateId}`);
    const selectedCompanyId = $("#companyFilter")?.value || template.company_id || "";
    $("#duplicateTemplateError").hidden = true;
    $("#duplicateTemplateMessage").textContent = `Se creara una version editable de "${template.name}" para el condominio seleccionado.`;
    $("#duplicateTemplateName").value = "";
    populateDuplicateTemplateCompanies(selectedCompanyId);
    populateDuplicateTemplateCondominiums();
    suggestDuplicateTemplateName(template);
    $("#duplicateTemplateModal").hidden = false;
    $("#duplicateTemplateCompany").focus();
  } catch (error) {
    window.alert(readableError(error));
  }
}

function closeDuplicateTemplateModal() {
  state.duplicateTemplateId = null;
  state.duplicateTemplateKind = "inspection";
  $("#duplicateTemplateModal").hidden = true;
}

function populateDuplicateTemplateCompanies(selectedCompanyId = "") {
  const companies = state.companies.filter((company) => !isInternalKomiteCompany(company));
  $("#duplicateTemplateCompany").innerHTML = companies
    .map((company, index) => {
      const selected = selectedCompanyId
        ? sameId(company.id, selectedCompanyId)
        : index === 0;
      return `<option value="${escapeHtml(company.id)}"${selected ? " selected" : ""}>${escapeHtml(company.name || "Empresa")}</option>`;
    })
    .join("");
}

function populateDuplicateTemplateCondominiums() {
  const companyId = $("#duplicateTemplateCompany").value;
  const condominiums = state.condominiums.filter((condominium) => sameId(condominium.company_id, companyId));
  $("#duplicateTemplateCondominium").innerHTML = condominiums.length
    ? condominiums
      .map((condominium) => `<option value="${escapeHtml(condominium.id)}">${escapeHtml(condominium.name || "Condominio")}</option>`)
      .join("")
    : `<option value="">Sin condominios disponibles</option>`;
}

function suggestDuplicateTemplateName(template) {
  const condominiumId = $("#duplicateTemplateCondominium").value;
  const condominium = state.condominiums.find((item) => sameId(item.id, condominiumId));
  $("#duplicateTemplateName").placeholder = condominium
    ? `${template.name} - ${condominium.name}`
    : template.name;
}

function currentDuplicateTemplateCandidate() {
  return state.currentItems.find((entry) => sameId(entry.id, state.duplicateTemplateId))
    || state.inspectionTemplates.find((entry) => sameId(entry.id, state.duplicateTemplateId));
}

async function duplicateTemplateToCondominium(event) {
  event.preventDefault();
  const templateId = state.duplicateTemplateId;
  if (!templateId) return;
  const isAiPrompt = state.duplicateTemplateKind === "aiPrompt";
  const condominiumId = $("#duplicateTemplateCondominium").value;
  if (!condominiumId) {
    $("#duplicateTemplateError").textContent = "Selecciona un condominio para crear la copia.";
    $("#duplicateTemplateError").hidden = false;
    return;
  }

  try {
    $("#duplicateTemplateError").hidden = true;
    const payload = {
      condominium_id: condominiumId,
      name: emptyToNull($("#duplicateTemplateName").value),
      status: "draft",
    };
    const endpoint = isAiPrompt
      ? `/api/v1/ai-prompt-templates/${templateId}/duplicate-to-condominium`
      : `/api/v1/inspection-templates/${templateId}/duplicate-to-condominium`;
    const result = await apiFetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    closeDuplicateTemplateModal();
    showToast({
      title: isAiPrompt ? "Prompt duplicado" : "Plantilla duplicada",
      message: isAiPrompt ? "Se creo una copia editable del prompt IA." : `Se creo la version para el condominio con ${result.items_created} items.`,
    });
    await loadTable();
  } catch (error) {
    $("#duplicateTemplateError").textContent = readableError(error);
    $("#duplicateTemplateError").hidden = false;
  }
}

async function returnToGenericList() {
  const resource = resources[state.currentView];
  $("#viewTitle").textContent = resource.title;
  showPanel("table");
  await loadTable();
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

async function openCondominiumForm(id = null) {
  try {
    $("#condominiumFormError").hidden = true;
    await ensureUserLookupsLoaded();
    if (!state.companies.length) {
      throw new Error("Antes de crear un condominio debes crear al menos una empresa.");
    }
    fillCompanySelect();

    const item = id ? state.currentItems.find((entry) => entry.id === id) || (await apiFetch(`/api/v1/condominiums/${id}`)) : null;
    $("#viewTitle").textContent = item ? "Editar condominio" : "Nuevo condominio";
    $("#condominiumFormTitle").textContent = item ? "Editar condominio" : "Nuevo condominio";
    setRecordId("#condominiumRecordId", item?.id);
    $("#deleteCondominiumButton").hidden = !item;
    fillCondominiumForm(item);
    showPanel("condominiumForm");
  } catch (error) {
    window.alert(readableError(error));
  }
}

async function openCompanyForm(id = null, returnContext = null) {
  $("#companyFormError").hidden = true;
  state.companyReturnContext = returnContext;
  $("#companyReturnView").value = returnContext || "";
  await ensureUserLookupsLoaded();

  const item = id ? state.currentItems.find((entry) => entry.id === id) || (await apiFetch(`/api/v1/companies/${id}`)) : null;
  $("#viewTitle").textContent = item ? "Editar empresa" : "Nueva empresa";
  $("#companyFormTitle").textContent = item ? "Editar empresa" : "Nueva empresa";
  setRecordId("#companyRecordId", item?.id);
  $("#deleteCompanyButton").hidden = !item;
  fillCompanyForm(item);
  showPanel("companyForm");
}

function fillCompanyForm(item) {
  $("#companyId").value = item?.id || "";
  $("#companyName").value = item?.name || "";
  $("#companyRut").value = item?.rut || "";
  $("#companyLegalName").value = item?.legal_name || "";
  $("#companyEmail").value = item?.email || "";
  $("#companyPhone").value = item?.phone || "";
  $("#companyStatus").value = item?.status || "active";
  $("#companyMetadata").value = JSON.stringify(item?.metadata || {}, null, 2);
  renderCompanyOperationalStaffRows(item);
}

function renderCompanyOperationalStaffRows(company) {
  const list = $("#companyOperationalStaffRows");
  list.innerHTML = "";

  if (!company?.id) {
    addOperationalStaffRow({}, "company");
    return;
  }

  const rows = state.operationalStaff.filter((item) => sameId(item.company_id, company.id) && !item.condominium_id);
  if (!rows.length) {
    addOperationalStaffRow({}, "company");
    return;
  }

  rows.forEach((item) => addOperationalStaffRow(item, "company"));
}

async function saveCompany(event) {
  event.preventDefault();
  $("#companyFormError").hidden = true;

  try {
    const id = $("#companyId").value;
    const payload = buildCompanyPayload();
    const saved = await apiFetch(id ? `/api/v1/companies/${id}` : "/api/v1/companies/", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await syncCompanyOperationalStaff(saved.id || id);
    state.companies = [];
    await returnFromCompanyForm(saved);
    showToast({
      title: id ? "Empresa actualizada" : "Empresa creada",
      message: "Los cambios se guardaron correctamente.",
    });
  } catch (error) {
    $("#companyFormError").textContent = readableError(error);
    $("#companyFormError").hidden = false;
  }
}

function buildCompanyPayload() {
  return {
    name: $("#companyName").value.trim(),
    rut: emptyToNull($("#companyRut").value),
    legal_name: emptyToNull($("#companyLegalName").value),
    email: emptyToNull($("#companyEmail").value),
    phone: emptyToNull($("#companyPhone").value),
    status: $("#companyStatus").value,
    metadata: parseJsonField("#companyMetadata", {}),
  };
}

async function deleteCurrentCompany() {
  const id = $("#companyId").value;
  if (!id) return;
  await deleteCompany(id);
}

async function deleteCompany(id) {
  const confirmed = await confirmAction({
    title: "Borrar empresa",
    message: "Esta acción eliminará la empresa seleccionada. Si tiene datos relacionados, la API puede impedir el borrado.",
    acceptLabel: "Borrar empresa",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/v1/companies/${id}`, { method: "DELETE" });
    state.companies = [];
    await returnToCompanyList();
    showToast({
      title: "Empresa borrada",
      message: "La empresa se elimino correctamente.",
    });
  } catch (error) {
    window.alert(readableError(error));
  }
}

async function returnFromCompanyForm(savedCompany = null) {
  if ($("#companyReturnView").value === "condominiumForm") {
    await ensureCompaniesLoaded();
    fillCompanySelect();
    if (savedCompany?.id) {
      $("#condominiumCompany").value = savedCompany.id;
    }
    $("#viewTitle").textContent = $("#condominiumId").value ? "Editar condominio" : "Nuevo condominio";
    showPanel("condominiumForm");
    return;
  }

  await returnToCompanyList();
}

async function returnToCompanyList() {
  state.currentView = "companies";
  $("#viewTitle").textContent = resources.companies.title;
  $("#newCompanyButton").hidden = false;
  $("#newCondominiumButton").hidden = true;
  $("#newUserButton").hidden = true;
  showPanel("table");
  await loadTable();
}

async function openUserForm(id = null) {
  $("#userFormError").hidden = true;
  await ensureUserLookupsLoaded();
  fillUserSelects();

  const item = id ? state.currentItems.find((entry) => entry.id === id) || (await apiFetch(`/api/v1/users/${id}`)) : null;
  $("#viewTitle").textContent = item ? "Editar usuario" : "Nuevo usuario";
  $("#userFormTitle").textContent = item ? "Editar usuario" : "Nuevo usuario";
  setRecordId("#userRecordId", item?.id);
  $("#deleteUserButton").hidden = !item;
  $("#userPassword").required = !item;
  fillUserForm(item);
  showPanel("userForm");
}

function fillUserSelects() {
  $("#userCompany").innerHTML = `<option value="">Sin empresa</option>${state.companies
    .map((company) => `<option value="${escapeHtml(company.id)}">${escapeHtml(company.name)}</option>`)
    .join("")}`;
}

function fillUserForm(item) {
  $("#userId").value = item?.id || "";
  $("#userCompany").value = item?.company_id || "";
  $("#userFullName").value = item?.full_name || "";
  $("#userEmail").value = item?.email || "";
  $("#userPhone").value = item?.phone || "";
  $("#userPassword").value = "";
  $("#userStatus").value = item?.status || "active";
  $("#userCompanyProfile").value = item?.company_profile || "";
  $("#userOrganizationPosition").value = item?.organization_position || "";
  renderMembershipRows(item);
}

function renderMembershipRows(item) {
  const list = $("#userMembershipRows");
  list.innerHTML = "";

  const memberships = item?.memberships?.length
    ? item.memberships
    : item?.condominium_id
      ? [{ condominium_id: item.condominium_id, role_code: item.role_code || "vecino", unit_id: item.unit_id || "" }]
      : [];

  if (!memberships.length) {
    addMembershipRow();
    return;
  }

  memberships.forEach((membership) => addMembershipRow(membership));
}

function addMembershipRow(membership = {}) {
  const row = document.createElement("div");
  row.className = "membership-row";
  row.innerHTML = `
    <label>
      Condominio
      <select class="membership-condominium" required>
        <option value="">Selecciona condominio</option>
        <option value="__all__">Todos</option>
        ${state.condominiums.map((condominium) => `<option value="${escapeHtml(condominium.id)}">${escapeHtml(condominium.name)}</option>`).join("")}
      </select>
    </label>
    <label>
      Rol
      <select class="membership-role" required>
        <option value="">Selecciona rol</option>
        ${state.roles.map((role) => `<option value="${escapeHtml(role.code)}">${escapeHtml(role.name || role.code)}</option>`).join("")}
      </select>
    </label>
    <label>
      Unidad
      <select class="membership-unit"></select>
    </label>
    <button class="membership-remove icon-button" type="button">
      <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
      <span>Quitar</span>
    </button>
  `;

  const condominiumSelect = row.querySelector(".membership-condominium");
  const roleSelect = row.querySelector(".membership-role");
  const unitSelect = row.querySelector(".membership-unit");

  condominiumSelect.value = membership.condominium_id === null ? "__all__" : membership.condominium_id || "";
  roleSelect.value = membership.role_code || membership.role || "";
  updateMembershipUnitOptions(unitSelect, condominiumSelect.value, membership.unit_id || "");

  condominiumSelect.addEventListener("change", () => {
    updateMembershipUnitOptions(unitSelect, condominiumSelect.value, "");
  });

  row.querySelector(".membership-remove").addEventListener("click", () => {
    row.remove();
    if (!$$("#userMembershipRows .membership-row").length) {
      addMembershipRow();
    }
  });

  $("#userMembershipRows").appendChild(row);
}

function updateMembershipUnitOptions(select, condominiumId, selectedUnitId) {
  if (condominiumId === "__all__" || !condominiumId) {
    select.innerHTML = `<option value="">Sin unidad</option>`;
    select.value = "";
    select.disabled = condominiumId === "__all__";
    return;
  }

  select.disabled = false;
  const units = condominiumId
    ? state.units.filter((unit) => unit.condominium_id === condominiumId)
    : [];

  select.innerHTML = `<option value="">Sin unidad</option>${units
    .map((unit) => `<option value="${escapeHtml(unit.id)}">${escapeHtml(unit.identifier)}</option>`)
    .join("")}`;
  select.value = selectedUnitId || "";
}

async function saveUser(event) {
  event.preventDefault();
  $("#userFormError").hidden = true;

  try {
    const id = $("#userId").value;
    const payload = buildUserPayload(Boolean(id));
    await apiFetch(id ? `/api/v1/users/${id}` : "/api/v1/users/", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await returnToUserList();
    showToast({
      title: id ? "Usuario actualizado" : "Usuario creado",
      message: "Los cambios se guardaron correctamente.",
    });
  } catch (error) {
    $("#userFormError").textContent = readableError(error);
    $("#userFormError").hidden = false;
  }
}

function buildUserPayload(isUpdate) {
  const payload = {
    email: $("#userEmail").value.trim(),
    full_name: $("#userFullName").value.trim(),
    phone: emptyToNull($("#userPhone").value),
    company_id: emptyToNull($("#userCompany").value),
    company_profile: emptyToNull($("#userCompanyProfile").value),
    organization_position: emptyToNull($("#userOrganizationPosition").value),
    status: $("#userStatus").value,
  };

  const password = $("#userPassword").value;
  if (password) {
    payload.password = password;
  } else if (!isUpdate) {
    payload.password = "";
  }

  payload.memberships = buildUserMembershipPayload();

  return payload;
}

function buildUserMembershipPayload() {
  return $$("#userMembershipRows .membership-row")
    .map((row) => {
      const condominiumValue = row.querySelector(".membership-condominium").value;
      const isAllCondominiums = condominiumValue === "__all__";
      return {
        isValidSelection: Boolean(condominiumValue),
        condominium_id: isAllCondominiums ? null : emptyToNull(condominiumValue),
        role_code: emptyToNull(row.querySelector(".membership-role").value),
        unit_id: isAllCondominiums ? null : emptyToNull(row.querySelector(".membership-unit").value),
        status: "active",
        receives_notifications: true,
      };
    })
    .filter((membership) => membership.isValidSelection && membership.role_code)
    .map(({ isValidSelection, ...membership }) => membership);
}

async function deleteCurrentUser() {
  const id = $("#userId").value;
  if (!id) return;
  await deleteUser(id);
}

async function deleteUser(id) {
  const confirmed = await confirmAction({
    title: "Borrar usuario",
    message: "Esta acción eliminará el usuario seleccionado. No se puede deshacer desde el backoffice.",
    acceptLabel: "Borrar usuario",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/v1/users/${id}`, { method: "DELETE" });
    await returnToUserList();
    showToast({
      title: "Usuario borrado",
      message: "El usuario se elimino correctamente.",
    });
  } catch (error) {
    window.alert(readableError(error));
  }
}

async function returnToUserList() {
  state.currentView = "users";
  $("#viewTitle").textContent = resources.users.title;
  $("#newCompanyButton").hidden = true;
  $("#newCondominiumButton").hidden = true;
  $("#newUserButton").hidden = false;
  showPanel("table");
  await loadTable();
}

function fillCompanySelect() {
  const select = $("#condominiumCompany");
  select.innerHTML = state.companies
    .map((company) => `<option value="${escapeHtml(company.id)}">${escapeHtml(company.name)}</option>`)
    .join("");
}

function fillCondominiumForm(item) {
  const customRows = item?.id ? state.operationalStaff.filter((entry) => sameId(entry.condominium_id, item.id)) : [];
  const metadata = item?.metadata || {};
  $("#condominiumId").value = item?.id || "";
  $("#condominiumCompany").value = item?.company_id || state.companies[0]?.id || "";
  $("#condominiumName").value = item?.name || "";
  $("#condominiumAddress").value = item?.address || "";
  $("#condominiumCommune").value = item?.commune || "";
  $("#condominiumCity").value = item?.city || "";
  $("#condominiumRegion").value = item?.region || "";
  $("#condominiumStatus").value = item?.status || "active";
  $("#condominiumTowers").value = item?.towers_count ?? 0;
  $("#condominiumUnits").value = item?.units_count ?? 0;
  $("#condominiumIncidentCategories").value = JSON.stringify(item?.incident_categories || [], null, 2);
  $("#condominiumCommunicationRules").value = JSON.stringify(item?.communication_rules || {}, null, 2);
  $("#condominiumMetadata").value = JSON.stringify(metadata, null, 2);
  $("#condominiumOperationalStaffMode").value = metadata.operational_staff_mode || (customRows.length ? "custom" : "company");
  renderOperationalStaffRows(item);
}

function renderOperationalStaffRows(condominium) {
  const list = $("#condominiumOperationalStaffRows");
  list.innerHTML = "";
  const mode = $("#condominiumOperationalStaffMode").value || "company";
  const companyId = $("#condominiumCompany").value;
  const baseRows = state.operationalStaff.filter((item) => sameId(item.company_id, companyId) && !item.condominium_id);

  if (mode === "company") {
    $("#addOperationalStaffButton").hidden = true;
    if (!baseRows.length) {
      list.innerHTML = `<div class="empty-table">Esta empresa aun no tiene equipo operativo base.</div>`;
      return;
    }
    baseRows.forEach((item) => addOperationalStaffRow({ ...item, id: "" }, "condominium", true));
    return;
  }

  $("#addOperationalStaffButton").hidden = false;
  const rows = condominium?.id
    ? state.operationalStaff.filter((item) => sameId(item.condominium_id, condominium.id))
    : [];

  if (!rows.length) {
    if (baseRows.length) {
      baseRows.forEach((item) => addOperationalStaffRow({ ...item, id: "" }, "condominium"));
    } else {
      addOperationalStaffRow({}, "condominium");
    }
    return;
  }

  rows.forEach((item) => addOperationalStaffRow(item, "condominium"));
}

function operationalStaffUsersForCompany(companyId) {
  return state.usersLookup
    .filter((user) => sameId(user.company_id, companyId) && user.company_profile)
    .sort((left, right) => String(left.full_name || "").localeCompare(String(right.full_name || "")));
}

function selectedOperationalStaffUser(row) {
  const userId = row.querySelector(".staff-user")?.value;
  return state.usersLookup.find((user) => sameId(user.id, userId)) || null;
}

function updateOperationalStaffProfile(row) {
  const user = selectedOperationalStaffUser(row);
  const profile = user?.company_profile || "";
  row.querySelector(".staff-profile").value = profile;
  row.querySelector(".staff-profile-display").textContent = roleLabels[profile] || "Sin perfil";
  row.querySelector(".staff-profile-display").classList.toggle("muted-badge", !profile);
  if (row.dataset.staffTarget === "company" || row.dataset.staffReadOnly === "true") {
    const fallbackResponsibility = row.querySelector(".staff-responsibility")?.value || "";
    const position = user?.organization_position || fallbackResponsibility;
    row.querySelector(".staff-responsibility").value = position;
    row.querySelector(".staff-responsibility-display").textContent = position || (row.dataset.staffTarget === "company" ? "Sin puesto" : "Sin responsabilidad");
    row.querySelector(".staff-responsibility-display").classList.toggle("muted-badge", !position);
  }
}

function addOperationalStaffRow(item = {}, target = "condominium", readOnly = false) {
  const companyId = target === "company" ? $("#companyId").value : $("#condominiumCompany").value;
  const containerSelector = target === "company" ? "#companyOperationalStaffRows" : "#condominiumOperationalStaffRows";
  const users = operationalStaffUsersForCompany(companyId);
  const row = document.createElement("div");
  row.className = "membership-row operational-staff-row";
  row.dataset.staffId = item.id || "";
  row.dataset.staffTarget = target;
  row.dataset.staffReadOnly = readOnly ? "true" : "false";
  row.innerHTML = `
    <label>
      Usuario
      <select class="staff-user" required ${readOnly ? "disabled" : ""}>
        <option value="">Selecciona usuario</option>
        ${users.map((user) => `<option value="${escapeHtml(user.id)}" data-profile="${escapeHtml(user.company_profile || "")}">${escapeHtml(user.full_name || user.email)}</option>`).join("")}
      </select>
    </label>
    <label>
      Perfil
      <input class="staff-profile" type="hidden" />
      <span class="readonly-value staff-profile-display">Sin perfil</span>
    </label>
    <label>
      ${target === "company" ? "Puesto" : "Responsabilidad"}
      ${target === "company" || readOnly
        ? `<input class="staff-responsibility" type="hidden" /><span class="readonly-value staff-responsibility-display">${target === "company" ? "Sin puesto" : "Sin responsabilidad"}</span>`
        : `<input class="staff-responsibility" maxlength="120" placeholder="Ej. Zona norte" ${readOnly ? "disabled" : ""} />`}
    </label>
    <label>
      Estado
      <select class="staff-status" ${readOnly ? "disabled" : ""}>
        <option value="active">Activo</option>
        <option value="inactive">Inactivo</option>
      </select>
    </label>
    <label class="switch-line">
      <input class="staff-primary" type="checkbox" ${readOnly ? "disabled" : ""} />
      <span class="switch-slider" aria-hidden="true"></span>
      <span>Principal</span>
    </label>
    <button class="staff-remove icon-button danger-action" type="button" ${readOnly ? "hidden" : ""}>
      <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
      <span>Quitar</span>
    </button>
  `;

  const userSelect = row.querySelector(".staff-user");
  const profileSelect = row.querySelector(".staff-profile");
  userSelect.value = item.user_id || "";
  row.querySelector(".staff-responsibility").value = item.responsibility || "";
  const responsibilityDisplay = row.querySelector(".staff-responsibility-display");
  if (responsibilityDisplay && row.dataset.staffTarget !== "company") {
    const responsibility = item.responsibility || "";
    responsibilityDisplay.textContent = responsibility || "Sin responsabilidad";
    responsibilityDisplay.classList.toggle("muted-badge", !responsibility);
  }
  row.querySelector(".staff-status").value = item.status || "active";
  row.querySelector(".staff-primary").checked = Boolean(item.is_primary);
  updateOperationalStaffProfile(row);

  userSelect.addEventListener("change", () => {
    updateOperationalStaffProfile(row);
  });

  row.querySelector(".staff-remove").addEventListener("click", () => {
    row.remove();
    if (!$$(`${containerSelector} .operational-staff-row`).length) {
      addOperationalStaffRow({}, target);
    }
  });

  $(containerSelector).appendChild(row);
}

function refreshOperationalStaffUserOptions(target = "condominium") {
  const containerSelector = target === "company" ? "#companyOperationalStaffRows" : "#condominiumOperationalStaffRows";
  const currentRows = $$(`${containerSelector} .operational-staff-row`).map((row) => ({
    id: row.dataset.staffId || "",
    user_id: row.querySelector(".staff-user").value,
    responsibility: row.querySelector(".staff-responsibility").value,
    status: row.querySelector(".staff-status").value,
    is_primary: row.querySelector(".staff-primary").checked,
  }));
  $(containerSelector).innerHTML = "";
  if (!currentRows.length) {
    addOperationalStaffRow({}, target);
    return;
  }
  currentRows.forEach((row) => addOperationalStaffRow(row, target));
}

async function saveCondominium(event) {
  event.preventDefault();
  $("#condominiumFormError").hidden = true;

  try {
    const id = $("#condominiumId").value;
    const payload = buildCondominiumPayload();
    const savedCondominium = await apiFetch(id ? `/api/v1/condominiums/${id}` : "/api/v1/condominiums/", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await syncOperationalStaff(savedCondominium.id || id, savedCondominium.company_id || payload.company_id);
    await returnToCondominiumList();
    showToast({
      title: id ? "Condominio actualizado" : "Condominio creado",
      message: "Los cambios se guardaron correctamente.",
    });
  } catch (error) {
    $("#condominiumFormError").textContent = readableError(error);
    $("#condominiumFormError").hidden = false;
  }
}

function buildCondominiumPayload() {
  const metadata = parseJsonField("#condominiumMetadata", {});
  metadata.operational_staff_mode = $("#condominiumOperationalStaffMode").value || "company";
  return {
    company_id: $("#condominiumCompany").value,
    name: $("#condominiumName").value.trim(),
    address: emptyToNull($("#condominiumAddress").value),
    commune: emptyToNull($("#condominiumCommune").value),
    city: emptyToNull($("#condominiumCity").value),
    region: emptyToNull($("#condominiumRegion").value),
    towers_count: Number($("#condominiumTowers").value || 0),
    units_count: Number($("#condominiumUnits").value || 0),
    status: $("#condominiumStatus").value,
    incident_categories: parseJsonField("#condominiumIncidentCategories", []),
    communication_rules: parseJsonField("#condominiumCommunicationRules", {}),
    metadata,
  };
}

function buildOperationalStaffPayloads({ companyId, condominiumId = null, target = "condominium" }) {
  const containerSelector = target === "company" ? "#companyOperationalStaffRows" : "#condominiumOperationalStaffRows";
  return $$(`${containerSelector} .operational-staff-row`)
    .map((row) => ({
      id: row.dataset.staffId || "",
      company_id: companyId,
      condominium_id: condominiumId,
      user_id: emptyToNull(row.querySelector(".staff-user").value),
      portal_profile: selectedOperationalStaffUser(row)?.company_profile || null,
      responsibility: target === "company"
        ? emptyToNull(selectedOperationalStaffUser(row)?.organization_position || "")
        : emptyToNull(row.querySelector(".staff-responsibility").value),
      is_primary: row.querySelector(".staff-primary").checked,
      status: row.querySelector(".staff-status").value || "active",
      metadata: {},
    }))
    .filter((item) => item.user_id && item.portal_profile);
}

async function syncOperationalStaff(condominiumId, companyId) {
  const mode = $("#condominiumOperationalStaffMode").value || "company";
  const existing = state.operationalStaff.filter((item) => sameId(item.condominium_id, condominiumId));
  if (mode === "company") {
    for (const item of existing) {
      await apiFetch(`/api/v1/condominium-operational-staff/${item.id}`, { method: "DELETE" });
    }
    return;
  }

  const desired = buildOperationalStaffPayloads({ companyId, condominiumId, target: "condominium" });
  const desiredIds = new Set(desired.map((item) => item.id).filter(Boolean));

  for (const item of existing) {
    if (!desiredIds.has(String(item.id))) {
      await apiFetch(`/api/v1/condominium-operational-staff/${item.id}`, { method: "DELETE" });
    }
  }

  for (const item of desired) {
    const id = item.id;
    const payload = { ...item };
    delete payload.id;
    await apiFetch(id ? `/api/v1/condominium-operational-staff/${id}` : "/api/v1/condominium-operational-staff/", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }
}

async function syncCompanyOperationalStaff(companyId) {
  if (!companyId) return;
  const desired = buildOperationalStaffPayloads({ companyId, condominiumId: null, target: "company" });
  const existing = state.operationalStaff.filter((item) => sameId(item.company_id, companyId) && !item.condominium_id);
  const desiredIds = new Set(desired.map((item) => item.id).filter(Boolean));

  for (const item of existing) {
    if (!desiredIds.has(String(item.id))) {
      await apiFetch(`/api/v1/condominium-operational-staff/${item.id}`, { method: "DELETE" });
    }
  }

  for (const item of desired) {
    const id = item.id;
    const payload = { ...item };
    delete payload.id;
    await apiFetch(id ? `/api/v1/condominium-operational-staff/${id}` : "/api/v1/condominium-operational-staff/", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }
}

function parseJsonField(selector, fallback) {
  const value = $(selector).value.trim();
  if (!value) return fallback;
  return JSON.parse(value);
}

function emptyToNull(value) {
  const normalized = value.trim();
  return normalized || null;
}

async function deleteCurrentCondominium() {
  const id = $("#condominiumId").value;
  if (!id) return;
  await deleteCondominium(id);
}

async function deleteCondominium(id) {
  const confirmed = await confirmAction({
    title: "Borrar condominio",
    message: "Esta acción eliminará el condominio seleccionado. No se puede deshacer desde el backoffice.",
    acceptLabel: "Borrar condominio",
  });
  if (!confirmed) return;

  try {
    await apiFetch(`/api/v1/condominiums/${id}`, { method: "DELETE" });
    await returnToCondominiumList();
    showToast({
      title: "Condominio borrado",
      message: "El condominio se elimino correctamente.",
    });
  } catch (error) {
    window.alert(readableError(error));
  }
}

async function returnToCondominiumList() {
  state.currentView = "condominiums";
  $("#viewTitle").textContent = resources.condominiums.title;
  $("#newCompanyButton").hidden = true;
  $("#newCondominiumButton").hidden = false;
  $("#newUserButton").hidden = true;
  showPanel("table");
  await loadTable();
}

function readableError(error) {
  try {
    const parsed = JSON.parse(error.message);
    if (typeof parsed.detail === "string") return parsed.detail;
    return JSON.stringify(parsed.detail || parsed);
  } catch (parseError) {
    return error.message || "No se pudo completar la operacion.";
  }
}

function confirmAction({ title, message, acceptLabel = "Aceptar" }) {
  $("#confirmTitle").textContent = title;
  $("#confirmMessage").textContent = message;
  $("#confirmAcceptButton").textContent = acceptLabel;
  $("#confirmModal").hidden = false;
  $("#confirmCancelButton").focus();

  return new Promise((resolve) => {
    state.confirmResolver = resolve;
  });
}

function closeConfirmModal(confirmed) {
  $("#confirmModal").hidden = true;
  if (state.confirmResolver) {
    state.confirmResolver(confirmed);
    state.confirmResolver = null;
  }
}

let toastTimer = null;

function showToast({ title, message }) {
  $("#toastTitle").textContent = title;
  $("#toastMessage").textContent = message;
  $("#toast").hidden = false;

  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    $("#toast").hidden = true;
  }, 3200);
}

function showToolsCatalog() {
  $("#toolsCatalog").hidden = false;
  $("#edifitoNeighborsTool").hidden = true;
  $("#comunidadFelizNeighborsTool").hidden = true;
  $("#aiPromptTool").hidden = true;
  resetEdifitoNeighborsTool(false);
  resetComunidadFelizNeighborsTool(false);
  resetAiPromptTool(false);
}

async function openEdifitoNeighborsTool() {
  $("#toolsCatalog").hidden = true;
  $("#edifitoNeighborsTool").hidden = false;
  $("#comunidadFelizNeighborsTool").hidden = true;
  $("#aiPromptTool").hidden = true;
  $("#viewTitle").textContent = "Carga vecinos Edifito";
  $("#edifitoNeighborsError").hidden = true;
  $("#edifitoNeighborsPreview").hidden = true;
  state.edifitoNeighborsPreview = null;

  try {
    await ensureBackofficeToolLookupsLoaded();
    populateToolCompanySelect();
    populateToolCondominiumSelect();
  } catch (error) {
    $("#edifitoNeighborsError").textContent = readableError(error);
    $("#edifitoNeighborsError").hidden = false;
  }
}

async function openComunidadFelizNeighborsTool() {
  $("#toolsCatalog").hidden = true;
  $("#edifitoNeighborsTool").hidden = true;
  $("#comunidadFelizNeighborsTool").hidden = false;
  $("#aiPromptTool").hidden = true;
  $("#viewTitle").textContent = "Carga vecinos Comunidad Feliz";
  $("#comunidadFelizNeighborsError").hidden = true;
  $("#comunidadFelizNeighborsPreview").hidden = true;
  state.comunidadFelizNeighborsPreview = null;

  try {
    await ensureBackofficeToolLookupsLoaded();
    populateCfToolCompanySelect();
    populateCfToolCondominiumSelect();
  } catch (error) {
    $("#comunidadFelizNeighborsError").textContent = readableError(error);
    $("#comunidadFelizNeighborsError").hidden = false;
  }
}

async function ensureBackofficeToolLookupsLoaded() {
  const data = await apiFetch("/api/v1/backoffice/dashboard");
  state.companies = data.companies || [];
  state.condominiums = data.condominiums || [];
}

function populateToolCompanySelect() {
  const select = $("#toolCompanySelect");
  const companies = state.companies
    .filter((company) => !isInternalKomiteCompany(company))
    .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")));

  select.innerHTML = companies.length
    ? companies
    .map((company) => `<option value="${escapeHtml(company.id)}">${escapeHtml(company.name || "Empresa")}</option>`)
      .join("")
    : `<option value="">No hay empresas cliente</option>`;
}

function populateCfToolCompanySelect() {
  const select = $("#cfToolCompanySelect");
  const companies = state.companies
    .filter((company) => !isInternalKomiteCompany(company))
    .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")));

  select.innerHTML = companies.length
    ? companies
      .map((company) => `<option value="${escapeHtml(company.id)}">${escapeHtml(company.name || "Empresa")}</option>`)
      .join("")
    : `<option value="">No hay empresas cliente</option>`;
}

function populateToolCondominiumSelect(selectedId = "") {
  const companyId = $("#toolCompanySelect").value;
  const condominiums = state.condominiums
    .filter((condominium) => companyId && sameId(condominium.company_id, companyId))
    .filter((condominium) => !condominium.status || condominium.status === "active")
    .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")));
  $("#toolCondominiumSelect").innerHTML = condominiums.length
    ? condominiums
      .map((condominium) => `<option value="${escapeHtml(condominium.id)}"${sameId(condominium.id, selectedId) ? " selected" : ""}>${escapeHtml(condominium.name || "Condominio")}</option>`)
      .join("")
    : `<option value="">Sin condominios para esta empresa</option>`;
}

function populateCfToolCondominiumSelect(selectedId = "") {
  const companyId = $("#cfToolCompanySelect").value;
  const condominiums = state.condominiums
    .filter((condominium) => companyId && sameId(condominium.company_id, companyId))
    .filter((condominium) => !condominium.status || condominium.status === "active")
    .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")));
  $("#cfToolCondominiumSelect").innerHTML = condominiums.length
    ? condominiums
      .map((condominium) => `<option value="${escapeHtml(condominium.id)}"${sameId(condominium.id, selectedId) ? " selected" : ""}>${escapeHtml(condominium.name || "Condominio")}</option>`)
      .join("")
    : `<option value="">Sin condominios para esta empresa</option>`;
}

function resetEdifitoNeighborsTool(clearFile = true) {
  $("#edifitoNeighborsError").hidden = true;
  $("#edifitoNeighborsPreview").hidden = true;
  $("#edifitoNeighborsSummary").innerHTML = "";
  $("#edifitoNeighborsItems").innerHTML = "";
  state.edifitoNeighborsPreview = null;
  if (clearFile) $("#toolAssignmentsFile").value = "";
}

function resetComunidadFelizNeighborsTool(clearFile = true) {
  $("#comunidadFelizNeighborsError").hidden = true;
  $("#comunidadFelizNeighborsPreview").hidden = true;
  $("#comunidadFelizNeighborsSummary").innerHTML = "";
  $("#comunidadFelizNeighborsItems").innerHTML = "";
  state.comunidadFelizNeighborsPreview = null;
  if (clearFile) $("#cfToolChargesFile").value = "";
}

function resetAiPromptTool(clearInput = true) {
  $("#aiPromptError").hidden = true;
  $("#aiPromptOutput").value = "Sin respuesta.";
  $("#aiPromptTextResult").textContent = "Sin texto generado.";
  if (clearInput) $("#aiPromptInput").value = "";
}

function loadAiPromptSample() {
  const mode = $("#aiPromptMode").value;
  const sample = mode === "chat" ? {
    purpose: "backoffice_prompt_test",
    messages: [
      {
        role: "system",
        content: "Eres Komite, un asistente operativo para administracion de condominios en Chile. Responde de forma profesional, concreta y verificable.",
      },
      {
        role: "user",
        content: "Redacta un resumen ejecutivo para una mantencion preventiva de sala de bombas. Datos: Edificio Los Olivos, bomba de agua N. 2, ajuste de presion, revision de valvulas, sin fugas visibles, 3 fotografias adjuntas.",
      },
    ],
    temperature: 0.2,
    max_tokens: 1200,
  } : {
    prompt_key: "operational_report_draft",
    variables: {
      condominium_name: "Edificio Los Olivos",
      event_title: "Mantencion preventiva sala de bombas",
      asset_name: "Bomba de agua N. 2",
      event_description: "Revision programada del sistema de impulsion de agua potable, tablero electrico asociado y alternancia de bombas.",
      execution_comments: "Se reviso funcionamiento general de la bomba N. 2. Se ajusto presion de trabajo, se verifico alternancia con bomba N. 1 y se inspeccionaron valvulas de corte. No se detectaron fugas visibles. Se recomienda limpiar el sector de tablero porque presenta acumulacion de polvo.",
      evidence_summary: "3 fotografias: tablero electrico, manometro posterior al ajuste y vista general de sala de bombas.",
      asset_history: "05/05/2026: mantencion preventiva sin observaciones. 12/06/2026: cambio de valvula de retencion. 18/07/2026: ajuste de presion y revision de alternancia.",
    },
    temperature: 0.2,
    max_tokens: 1600,
  };
  $("#aiPromptInput").value = JSON.stringify(sample, null, 2);
}

async function submitAiPromptTool(event) {
  event.preventDefault();
  resetAiPromptTool(false);

  let payload;
  try {
    payload = JSON.parse($("#aiPromptInput").value || "{}");
  } catch (error) {
    $("#aiPromptError").textContent = "El JSON de entrada no es valido.";
    $("#aiPromptError").hidden = false;
    return;
  }

  const endpoint = $("#aiPromptMode").value === "chat" ? "/api/v1/ai/chat" : "/api/v1/ai/prompts/run";

  try {
    $("#aiPromptOutput").value = "Esperando respuesta de IA...";
    $("#aiPromptTextResult").textContent = "Generando...";
    const data = await apiFetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("#aiPromptOutput").value = JSON.stringify(data, null, 2);
    $("#aiPromptTextResult").textContent = data.text || "La respuesta no incluyo texto.";
    showToast({
      title: "Respuesta IA recibida",
      message: data.ai_request_id ? `Registro AI ${data.ai_request_id}` : "Prompt procesado correctamente.",
    });
  } catch (error) {
    $("#aiPromptOutput").value = "Sin respuesta.";
    $("#aiPromptTextResult").textContent = "Sin texto generado.";
    $("#aiPromptError").textContent = readableError(error);
    $("#aiPromptError").hidden = false;
  }
}

function edifitoImportFormData() {
  const file = $("#toolAssignmentsFile").files[0];
  const condominiumId = $("#toolCondominiumSelect").value;
  if (!condominiumId) throw new Error("Selecciona un condominio.");
  if (!file) throw new Error("Selecciona el informe XLSX de asignaciones.");

  const form = new FormData();
  form.append("condominium_id", condominiumId);
  form.append("assignments_file", file);
  return form;
}

function comunidadFelizImportFormData() {
  const file = $("#cfToolChargesFile").files[0];
  const condominiumId = $("#cfToolCondominiumSelect").value;
  if (!condominiumId) throw new Error("Selecciona un condominio.");
  if (!file) throw new Error("Selecciona el informe XLSX de Comunidad Feliz.");

  const form = new FormData();
  form.append("condominium_id", condominiumId);
  form.append("charges_file", file);
  return form;
}

async function previewEdifitoNeighborsTool(event) {
  event.preventDefault();
  resetEdifitoNeighborsTool(false);

  try {
    const data = await apiFetch("/api/v1/edifito/import-neighbors/preview", {
      method: "POST",
      body: edifitoImportFormData(),
    });
    state.edifitoNeighborsPreview = data;
    renderEdifitoNeighborsResult(data, true);
  } catch (error) {
    $("#edifitoNeighborsError").textContent = readableError(error);
    $("#edifitoNeighborsError").hidden = false;
  }
}

async function applyEdifitoNeighborsTool() {
  try {
    const data = await apiFetch("/api/v1/edifito/import-neighbors", {
      method: "POST",
      body: edifitoImportFormData(),
    });
    state.edifitoNeighborsPreview = null;
    renderEdifitoNeighborsResult(data, false);
    showToast({
      title: "Carga aplicada",
      message: `Vecinos cargados en ${data.condominium_name || "el condominio"}.`,
    });
  } catch (error) {
    $("#edifitoNeighborsError").textContent = readableError(error);
    $("#edifitoNeighborsError").hidden = false;
  }
}

async function previewComunidadFelizNeighborsTool(event) {
  event.preventDefault();
  resetComunidadFelizNeighborsTool(false);

  try {
    const data = await apiFetch("/api/v1/comunidad-feliz/import-neighbors/preview", {
      method: "POST",
      body: comunidadFelizImportFormData(),
    });
    state.comunidadFelizNeighborsPreview = data;
    renderComunidadFelizNeighborsResult(data, true);
  } catch (error) {
    $("#comunidadFelizNeighborsError").textContent = readableError(error);
    $("#comunidadFelizNeighborsError").hidden = false;
  }
}

async function applyComunidadFelizNeighborsTool() {
  try {
    const data = await apiFetch("/api/v1/comunidad-feliz/import-neighbors", {
      method: "POST",
      body: comunidadFelizImportFormData(),
    });
    state.comunidadFelizNeighborsPreview = null;
    renderComunidadFelizNeighborsResult(data, false);
    showToast({
      title: "Carga aplicada",
      message: `Vecinos cargados en ${data.condominium_name || "el condominio"}.`,
    });
  } catch (error) {
    $("#comunidadFelizNeighborsError").textContent = readableError(error);
    $("#comunidadFelizNeighborsError").hidden = false;
  }
}

function renderEdifitoNeighborsResult(data, preview) {
  const summary = data.summary || {};
  $("#edifitoNeighborsPreviewTitle").textContent = preview
    ? `Resumen previo en ${data.condominium_name || "condominio"}`
    : `Carga aplicada en ${data.condominium_name || "condominio"}`;
  $("#applyEdifitoNeighborsImport").hidden = !preview;
  $("#edifitoNeighborsSummary").innerHTML = [
    ["Unidades leídas", summary.rows],
    ["Unidades nuevas", summary.units_created],
    ["Unidades existentes", summary.units_updated],
    ["Contactos nuevos", summary.contacts_created],
    ["Contactos actualizados", summary.contacts_updated],
    ["Usuarios nuevos", summary.users_created],
    ["Usuarios actualizados", summary.users_updated],
    ["Sin usuario", summary.users_skipped],
  ].map(([label, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? 0)}</strong></article>`).join("");
  $("#edifitoNeighborsSummaryNote").textContent = "Las unidades se cuentan una vez por fila del informe. Los contactos y usuarios se calculan por copropietario y residente, por eso pueden ser mayores que las unidades.";

  const items = data.items || [];
  $("#edifitoNeighborsItems").innerHTML = items.length
    ? items.map((item) => `
      <tr>
        <td>${escapeHtml(item.unit || "")}</td>
        <td>${escapeHtml(item.relationship_type || "")}</td>
        <td>${escapeHtml(item.full_name || "")}</td>
        <td>${renderImportStatusBadge(item.status, preview)}</td>
      </tr>
    `).join("")
    : `<tr><td colspan="4" class="empty-table">Sin detalle para mostrar.</td></tr>`;
  $("#edifitoNeighborsPreview").hidden = false;
}

function renderComunidadFelizNeighborsResult(data, preview) {
  const summary = data.summary || {};
  $("#comunidadFelizNeighborsPreviewTitle").textContent = preview
    ? `Resumen previo en ${data.condominium_name || "condominio"}`
    : `Carga aplicada en ${data.condominium_name || "condominio"}`;
  $("#applyComunidadFelizNeighborsImport").hidden = !preview;
  $("#comunidadFelizNeighborsSummary").innerHTML = [
    [summary.format_residents ? "Personas leidas" : "Unidades leidas", summary.rows],
    ["Unidades nuevas", summary.units_created],
    ["Unidades existentes", summary.units_updated],
    ["Contactos nuevos", summary.contacts_created],
    ["Contactos actualizados", summary.contacts_updated],
    ["Usuarios nuevos", summary.users_created],
    ["Usuarios actualizados", summary.users_updated],
    ["Sin usuario", summary.users_skipped],
  ].map(([label, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? 0)}</strong></article>`).join("");
  $("#comunidadFelizNeighborsSummaryNote").textContent = summary.format_residents
    ? "Formato residentes detectado. Se crean o actualizan unidades, contactos y usuarios cuando el registro incluye correo."
    : "Formato gastos comunes detectado. Se cargan unidades y residentes; solo se crean usuarios si el informe incluye correo.";

  const items = data.items || [];
  $("#comunidadFelizNeighborsItems").innerHTML = items.length
    ? items.map((item) => `
      <tr>
        <td>${escapeHtml(item.unit || "")}</td>
        <td>${escapeHtml(item.relationship_type || "")}</td>
        <td>${escapeHtml(item.full_name || "")}</td>
        <td>${renderImportStatusBadge(item.status, preview)}</td>
      </tr>
    `).join("")
    : `<tr><td colspan="4" class="empty-table">Sin detalle para mostrar.</td></tr>`;
  $("#comunidadFelizNeighborsPreview").hidden = false;
}

function openAiPromptTool() {
  $("#toolsCatalog").hidden = true;
  $("#edifitoNeighborsTool").hidden = true;
  $("#comunidadFelizNeighborsTool").hidden = true;
  $("#aiPromptTool").hidden = false;
  $("#viewTitle").textContent = "Consola IA";
  resetAiPromptTool(false);
  if (!$("#aiPromptInput").value.trim()) loadAiPromptSample();
}

async function uploadAudio(event) {
  event.preventDefault();
  const file = $("#audioFile").files[0];
  if (!file) return;

  const form = new FormData();
  form.append("file", file);
  form.append("language", $("#audioLanguage").value || "es");
  form.append("generate_draft", $("#generateDraft").checked ? "true" : "false");

  $("#audioResult").textContent = "Procesando audio...";

  try {
    const data = await apiFetch("/api/v1/audio/transcriptions", {
      method: "POST",
      body: form,
    });
    $("#audioResult").textContent = data.transcription_text || data.error_message || "Sin transcripcion.";
  } catch (error) {
    $("#audioResult").textContent = isUnauthorizedError(error)
      ? "Tu sesion ha caducado. Vuelve a entrar y procesa el audio de nuevo."
      : "No se pudo procesar el audio.";
  }
}

function isUnauthorizedError(error) {
  return String(error?.message || error || "").includes("401");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

$("#loginForm").addEventListener("submit", login);
$("#logoutButton").addEventListener("click", async () => {
  if (state.refreshToken) {
    try {
      await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
    } catch (error) {
      // Local logout still wins if the server cannot be reached.
    }
  }
  clearSession();
  showLogin();
});
$("#refreshButton").addEventListener("click", loadTable);
$("#pageSizeSelect").addEventListener("change", async () => {
  state.tablePageSize = Number($("#pageSizeSelect").value) || 10;
  state.tablePage = 1;
  await loadTable();
});
$("#firstPageButton").addEventListener("click", () => goToTablePage(1));
$("#prevPageButton").addEventListener("click", () => goToTablePage(state.tablePage - 1));
$("#nextPageButton").addEventListener("click", () => goToTablePage(state.tablePage + 1));
$("#lastPageButton").addEventListener("click", () => goToTablePage(state.tableMeta.pages || 1));
$("#newCompanyButton").addEventListener("click", () => openCompanyForm());
$("#newCondominiumButton").addEventListener("click", () => openCondominiumForm());
$("#newUserButton").addEventListener("click", () => openUserForm());
$("#newGenericButton").addEventListener("click", () => openGenericForm());
$("#cancelGenericButton").addEventListener("click", returnToGenericList);
$("#genericForm").addEventListener("submit", saveGenericEntity);
$("#deleteGenericButton").addEventListener("click", () => deleteGenericEntity());
$("#quickCompanyButton").addEventListener("click", () => openCompanyForm(null, "condominiumForm"));
$("#cancelCompanyButton").addEventListener("click", returnFromCompanyForm);
$("#companyForm").addEventListener("submit", saveCompany);
$("#deleteCompanyButton").addEventListener("click", deleteCurrentCompany);
$("#addCompanyOperationalStaffButton").addEventListener("click", () => addOperationalStaffRow({}, "company"));
$("#cancelCondominiumButton").addEventListener("click", returnToCondominiumList);
$("#condominiumForm").addEventListener("submit", saveCondominium);
$("#deleteCondominiumButton").addEventListener("click", deleteCurrentCondominium);
$("#addOperationalStaffButton").addEventListener("click", () => addOperationalStaffRow());
$("#condominiumOperationalStaffMode").addEventListener("change", () => renderOperationalStaffRows({ id: $("#condominiumId").value }));
$("#condominiumCompany").addEventListener("change", () => renderOperationalStaffRows({ id: $("#condominiumId").value }));
$("#cancelUserButton").addEventListener("click", returnToUserList);
$("#userForm").addEventListener("submit", saveUser);
$("#addMembershipButton").addEventListener("click", () => addMembershipRow());
$("#deleteUserButton").addEventListener("click", deleteCurrentUser);
$("#confirmCancelButton").addEventListener("click", () => closeConfirmModal(false));
$("#confirmAcceptButton").addEventListener("click", () => closeConfirmModal(true));
$("#confirmModal").addEventListener("click", (event) => {
  if (event.target === $("#confirmModal")) closeConfirmModal(false);
});
$("#duplicateTemplateCancelButton").addEventListener("click", closeDuplicateTemplateModal);
$("#duplicateTemplateForm").addEventListener("submit", duplicateTemplateToCondominium);
$("#duplicateTemplateModal").addEventListener("click", (event) => {
  if (event.target === $("#duplicateTemplateModal")) closeDuplicateTemplateModal();
});
$("#duplicateTemplateCompany").addEventListener("change", () => {
  populateDuplicateTemplateCondominiums();
  const template = currentDuplicateTemplateCandidate();
  if (template) suggestDuplicateTemplateName(template);
});
$("#duplicateTemplateCondominium").addEventListener("change", () => {
  const template = currentDuplicateTemplateCandidate();
  if (template) suggestDuplicateTemplateName(template);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("#duplicateTemplateModal").hidden) closeDuplicateTemplateModal();
  if (event.key === "Escape" && !$("#confirmModal").hidden) closeConfirmModal(false);
});
$("#searchInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    clearTimeout(searchDebounceTimer);
    state.tablePage = 1;
    loadTable();
  }
});
$("#searchInput").addEventListener("input", () => {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    state.tablePage = 1;
    loadTable();
  }, 350);
});
$("#companyFilter").addEventListener("change", () => {
  const resource = resources[state.currentView];
  if (resource) {
    if (["condominiums", "committeeMembers", "users", "inspectionTemplates", "inspectionTemplateSections", "inspectionTemplateItems", "aiPromptTemplates"].includes(state.currentView)) {
      state.tablePage = 1;
      loadTable();
      return;
    }
    renderTable(resource.columns, filteredTableItems());
    renderPagination();
  }
});
$("#ticketCompanyFilter").addEventListener("change", async () => {
  populateTicketCondominiumFilter();
  $("#ticketCondominiumFilter").value = "";
  state.tablePage = 1;
  await loadTable();
});
$("#ticketCondominiumFilter").addEventListener("change", async () => {
  state.tablePage = 1;
  await loadTable();
});
$("#ticketStatusFilter").addEventListener("change", async () => {
  state.tablePage = 1;
  await loadTable();
});
$("#audioForm").addEventListener("submit", uploadAudio);
$("#openEdifitoNeighborsTool").addEventListener("click", openEdifitoNeighborsTool);
$("#openComunidadFelizNeighborsTool").addEventListener("click", openComunidadFelizNeighborsTool);
$("#openAiPromptTool").addEventListener("click", openAiPromptTool);
$("#backToToolsCatalog").addEventListener("click", () => {
  $("#viewTitle").textContent = "Herramientas";
  showToolsCatalog();
});
$("#backToToolsCatalogFromComunidadFeliz").addEventListener("click", () => {
  $("#viewTitle").textContent = "Herramientas";
  showToolsCatalog();
});
$("#backToToolsCatalogFromAi").addEventListener("click", () => {
  $("#viewTitle").textContent = "Herramientas";
  showToolsCatalog();
});
$("#aiPromptMode").addEventListener("change", loadAiPromptSample);
$("#aiPromptSampleButton").addEventListener("click", loadAiPromptSample);
$("#aiPromptForm").addEventListener("submit", submitAiPromptTool);
$("#toolCompanySelect").addEventListener("change", () => {
  populateToolCondominiumSelect();
  resetEdifitoNeighborsTool(false);
});
$("#toolCondominiumSelect").addEventListener("change", () => resetEdifitoNeighborsTool(false));
$("#toolAssignmentsFile").addEventListener("change", () => resetEdifitoNeighborsTool(false));
$("#toolResetButton").addEventListener("click", () => resetEdifitoNeighborsTool(true));
$("#edifitoNeighborsForm").addEventListener("submit", previewEdifitoNeighborsTool);
$("#applyEdifitoNeighborsImport").addEventListener("click", applyEdifitoNeighborsTool);
$("#cfToolCompanySelect").addEventListener("change", () => {
  populateCfToolCondominiumSelect();
  resetComunidadFelizNeighborsTool(false);
});
$("#cfToolCondominiumSelect").addEventListener("change", () => resetComunidadFelizNeighborsTool(false));
$("#cfToolChargesFile").addEventListener("change", () => resetComunidadFelizNeighborsTool(false));
$("#cfToolResetButton").addEventListener("click", () => resetComunidadFelizNeighborsTool(true));
$("#comunidadFelizNeighborsForm").addEventListener("submit", previewComunidadFelizNeighborsTool);
$("#applyComunidadFelizNeighborsImport").addEventListener("click", applyComunidadFelizNeighborsTool);
$("#sidebarToggle").addEventListener("click", toggleSidebar);
document.addEventListener("click", (event) => {
  const groupToggle = event.target.closest("[data-nav-group]");
  if (!groupToggle) return;
  event.preventDefault();
  toggleNavGroup(groupToggle.dataset.navGroup);
});
$$(".nav-item").forEach((button) => button.addEventListener("click", () => openView(button.dataset.view)));
$$("[data-view-target]").forEach((button) => button.addEventListener("click", () => openView(button.dataset.viewTarget)));

async function bootstrap() {
  if (!state.token && state.refreshToken) {
    await refreshSession();
  }

  if (state.token) {
    if (window.location.pathname === "/login") {
      window.location.replace(BACKOFFICE_PATH);
    } else {
      showOffice();
    }
  } else {
    showLogin();
  }
}

function bindGenericFieldDependencies() {
  const companySelect = $('[data-generic-field="company_id"]');
  const condominiumSelect = $('[data-generic-field="condominium_id"]');
  const unitSelect = $('[data-generic-field="unit_id"]');
  const contactSelect = $('[data-generic-field="unit_contact_id"]');
  const templateSelect = $('[data-generic-field="template_id"]');
  const sectionSelect = $('[data-generic-field="section_id"]');
  const fullNameInput = $('[data-generic-field="full_name"]');
  const emailInput = $('[data-generic-field="email"]');
  const phoneInput = $('[data-generic-field="phone"]');
  const syncInspectionSectionOptions = () => {
    if (!sectionSelect) return;
    const selectedTemplateId = templateSelect?.value || "";
    const selectedCompanyId = companySelect?.value || "";
    Array.from(sectionSelect.options).forEach((option) => {
      const optionTemplateId = option.dataset.templateId;
      const optionCompanyId = option.dataset.companyId;
      const hiddenByTemplate = Boolean(optionTemplateId && selectedTemplateId && !sameId(optionTemplateId, selectedTemplateId));
      const hiddenByCompany = Boolean(optionCompanyId && selectedCompanyId && !sameId(optionCompanyId, selectedCompanyId));
      setOptionDependencyHidden(option, hiddenByTemplate || hiddenByCompany);
    });
    if (sectionSelect.selectedOptions[0]?.hidden) sectionSelect.value = "";
  };
  const syncInspectionTemplateOptions = () => {
    if (!templateSelect) return;
    const selectedCompanyId = companySelect?.value || "";
    Array.from(templateSelect.options).forEach((option) => {
      const optionCompanyId = option.dataset.companyId;
      setOptionDependencyHidden(option, Boolean(optionCompanyId && selectedCompanyId && !sameId(optionCompanyId, selectedCompanyId)));
    });
    if (templateSelect.selectedOptions[0]?.hidden) templateSelect.value = "";
    syncInspectionSectionOptions();
  };
  companySelect?.addEventListener("change", syncInspectionTemplateOptions);
  templateSelect?.addEventListener("change", syncInspectionSectionOptions);
  syncInspectionTemplateOptions();

  if (!companySelect || !condominiumSelect) return;

  const syncCondominiumOptions = () => {
    const selectedCompanyId = companySelect.value;
    Array.from(condominiumSelect.options).forEach((option) => {
      const optionCompanyId = option.dataset.companyId;
      setOptionDependencyHidden(option, Boolean(optionCompanyId && selectedCompanyId && !sameId(optionCompanyId, selectedCompanyId)));
    });
    const selectedOption = condominiumSelect.selectedOptions[0];
    if (selectedOption?.hidden) condominiumSelect.value = "";
    syncUnitOptions();
  };

  const syncUnitOptions = () => {
    const selectedCondominiumId = condominiumSelect.value;
    if (unitSelect) {
      Array.from(unitSelect.options).forEach((option) => {
        const optionCondominiumId = option.dataset.condominiumId;
        setOptionDependencyHidden(option, Boolean(optionCondominiumId && selectedCondominiumId && !sameId(optionCondominiumId, selectedCondominiumId)));
      });
      if (unitSelect.selectedOptions[0]?.hidden) unitSelect.value = "";
    }
    syncContactOptions();
  };

  const syncContactOptions = () => {
    if (!contactSelect) return;
    const selectedCondominiumId = condominiumSelect.value;
    const selectedUnitId = unitSelect?.value || "";
    Array.from(contactSelect.options).forEach((option) => {
      const optionCondominiumId = option.dataset.condominiumId;
      const optionUnitId = option.dataset.unitId;
      const hiddenByCondominium = Boolean(optionCondominiumId && selectedCondominiumId && !sameId(optionCondominiumId, selectedCondominiumId));
      const hiddenByUnit = Boolean(optionUnitId && selectedUnitId && !sameId(optionUnitId, selectedUnitId));
      setOptionDependencyHidden(option, hiddenByCondominium || hiddenByUnit);
    });
    if (contactSelect.selectedOptions[0]?.hidden) contactSelect.value = "";
  };

  const syncContactData = () => {
    if (!contactSelect) return;
    const option = contactSelect.selectedOptions[0];
    if (!option || !option.value) return;
    if (unitSelect && !unitSelect.value && option.dataset.unitId) unitSelect.value = option.dataset.unitId;
    if (fullNameInput && !fullNameInput.value && option.dataset.fullName) fullNameInput.value = option.dataset.fullName;
    if (emailInput && !emailInput.value && option.dataset.email) emailInput.value = option.dataset.email;
    if (phoneInput && !phoneInput.value && option.dataset.phone) phoneInput.value = option.dataset.phone;
    syncUnitOptions();
  };

  companySelect.addEventListener("change", syncCondominiumOptions);
  condominiumSelect.addEventListener("change", syncUnitOptions);
  unitSelect?.addEventListener("change", syncContactOptions);
  contactSelect?.addEventListener("change", syncContactData);
  syncCondominiumOptions();
}

bootstrap();

