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
  roles: [],
  usersLookup: [],
  companyReturnContext: null,
  confirmResolver: null,
};

let ticketsStatusChart = null;
let ticketsCompanyChart = null;
let searchDebounceTimer = null;

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
    columns: ["id", "name", "rut", "email", "status"],
  },
  banks: {
    title: "Bancos",
    endpoint: "/api/v1/banks/",
    columns: ["name", "code", "country", "website", "status"],
    createLabel: "Nuevo banco",
    singular: "banco",
    fields: [
      { name: "name", label: "Nombre", required: true, maxLength: 120 },
      { name: "code", label: "Codigo", maxLength: 40 },
      { name: "country", label: "Pais", defaultValue: "Chile", maxLength: 80 },
      { name: "website", label: "Web", maxLength: 255 },
      { name: "status", label: "Estado", type: "select", options: [["active", "Activo"], ["inactive", "Inactivo"], ["draft", "Borrador"]], defaultValue: "active" },
      { name: "metadata", label: "Metadata", type: "json", defaultValue: {} },
    ],
  },
  condominiums: {
    title: "Condominios",
    endpoint: "/api/v1/condominiums/",
    columns: ["id", "company_id", "name", "address", "status", "units_count"],
  },
  incidents: {
    title: "Incidencias",
    endpoint: "/api/v1/incidents/",
    columns: ["id", "category", "priority", "status", "created_at"],
  },
  supportTickets: {
    title: "Tickets",
    endpoint: "/api/v1/support-tickets/",
    columns: ["id", "company_id", "condominium_id", "subject", "priority", "status", "due_date"],
    createLabel: "Nuevo ticket",
    singular: "ticket",
    fields: [
      { name: "company_id", label: "Empresa", type: "company", required: true },
      { name: "condominium_id", label: "Condominio", type: "condominium" },
      { name: "subject", label: "Asunto", required: true, maxLength: 180 },
      { name: "description", label: "Descripcion", type: "textarea" },
      { name: "requester_name", label: "Solicitante", maxLength: 150 },
      { name: "requester_email", label: "Email solicitante", type: "email", maxLength: 255 },
      { name: "category", label: "Categoria", defaultValue: "general", maxLength: 80 },
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
    columns: ["id", "title", "priority", "status", "due_date"],
  },
  reports: {
    title: "Informes",
    endpoint: "/api/v1/reports/",
    columns: ["id", "title", "report_type", "status", "published_at"],
  },
  communications: {
    title: "Comunicaciones",
    endpoint: "/api/v1/communications/",
    columns: ["id", "title", "communication_type", "audience", "status"],
  },
  inspections: {
    title: "Inspecciones",
    endpoint: "/api/v1/inspections/",
    columns: ["id", "inspection_type", "status", "started_at", "finished_at"],
  },
  users: {
    title: "Usuarios",
    endpoint: "/api/v1/users/",
    columns: ["id", "email", "full_name", "company_profile", "role_code", "status"],
  },
  roles: {
    title: "Roles",
    endpoint: "/api/v1/roles/",
    columns: ["id", "code", "name", "is_system"],
  },
  attachments: {
    title: "Archivos",
    endpoint: "/api/v1/attachments/",
    columns: ["id", "file_name", "file_type", "mime_type", "created_at"],
  },
  audit: {
    title: "Auditoria",
    endpoint: "/api/v1/audit-logs/",
    columns: ["id", "action", "entity_type", "entity_id", "created_at"],
  },
  ai: {
    title: "IA",
    endpoint: "/api/v1/ai-requests/",
    columns: ["id", "provider", "model", "purpose", "status"],
  },
};

const columnLabels = {
  id: "ID",
  name: "Nombre",
  rut: "RUT",
  email: "Email",
  status: "Estado",
  address: "Direccion",
  company_id: "Empresa",
  condominium_id: "Condominio",
  code: "Codigo",
  country: "Pais",
  website: "Web",
  units_count: "Unidades",
  category: "Categoria",
  priority: "Prioridad",
  created_at: "Creado",
  title: "Titulo",
  due_date: "Vencimiento",
  report_type: "Tipo de informe",
  published_at: "Publicado",
  communication_type: "Tipo de comunicacion",
  audience: "Audiencia",
  inspection_type: "Tipo de inspeccion",
  started_at: "Inicio",
  finished_at: "Fin",
  full_name: "Nombre completo",
  company_profile: "Perfil Portal Administrador",
  role_code: "Rol",
  scope: "Ambito",
  is_system: "Sistema",
  file_name: "Archivo",
  file_type: "Tipo",
  mime_type: "MIME",
  action: "Accion",
  entity_type: "Entidad",
  entity_id: "ID entidad",
  provider: "Proveedor",
  model: "Modelo",
  purpose: "Uso",
  subject: "Asunto",
  description: "Descripcion",
  requester_name: "Solicitante",
  requester_email: "Email solicitante",
  assigned_to_id: "Asignado a",
  resolved_at: "Resuelto el",
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
  open: { background: "#dbeafe", color: "#1d4f91", accent: "#60a5fa" },
  pending: { background: "#fef3c7", color: "#8a5a10", accent: "#fbbf24" },
  in_progress: { background: "#ede9fe", color: "#5b3aa4", accent: "#a78bfa" },
  resolved: { background: "#dcfce7", color: "#1f7a3a", accent: "#86efac" },
  closed: { background: "#f1f5f9", color: "#475569", accent: "#94a3b8" },
};

const companyChartPalette = [
  { background: "#bfdbfe", border: "#60a5fa" },
  { background: "#bbf7d0", border: "#4ade80" },
  { background: "#ddd6fe", border: "#a78bfa" },
  { background: "#fecaca", border: "#f87171" },
  { background: "#fde68a", border: "#fbbf24" },
  { background: "#99f6e4", border: "#2dd4bf" },
  { background: "#fed7aa", border: "#fb923c" },
  { background: "#fbcfe8", border: "#f472b6" },
];

const roleLabels = {
  project_manager: "Project manager",
  ejecutivo: "Ejecutivo/a",
  supervisor: "Supervisor",
  conserje: "Conserje",
  vecino: "Vecino",
  comite: "Comite",
};

const placeholders = {
  committee: {
    title: "Comite",
    text: "Aqui quedara la gestion de miembros del comite, cargos, vigencias y relaciones con condominios.",
  },
  neighbors: {
    title: "Vecinos",
    text: "Aqui se preparara la administracion de vecinos, unidades, datos de contacto y preferencias de comunicacion.",
  },
  settings: {
    title: "Configuracion",
    text: "Aqui se centralizaran parametros del sistema, integraciones, proveedores de IA y reglas operativas.",
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

async function apiFetch(path, options = {}) {
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
  const statusColors = statuses.map((status) => ticketStatusPalette[status].background);
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
        borderWidth: 2,
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
          enabled: true,
          color: "#93c5fd",
          width: 1.5,
        },
        stackPercentageLabels: {
          enabled: true,
          color: "#172536",
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
    $("#placeholderText").textContent = "Esta opcion aun no tiene una ruta asociada en el backoffice.";
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
  $("#companyFilter").hidden = view !== "condominiums";
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
  if (view === "condominiums") {
    await ensureCompaniesLoaded();
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

  return params.toString();
}

function filteredTableItems() {
  let items = state.currentItems || [];
  if (state.currentView === "condominiums") {
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
  $("#pageIndicator").textContent = `Pagina ${meta.page} de ${meta.pages}`;
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
  if (column === "is_system") return renderBooleanBadge(value);
  if (column === "company_id") return escapeHtml(companyName(value));
  if (column === "condominium_id") return escapeHtml(condominiumName(value));
  if (["company_profile", "role_code"].includes(column)) return escapeHtml(roleLabels[value] || formatCell(value));
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
  return `
    <div class="table-actions">
      <button class="edit-row icon-button" type="button" data-edit-generic="${safeId}">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
        <span>Editar</span>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-generic="${safeId}">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
        <span>Borrar</span>
      </button>
    </div>
  `;
}

function bindGenericRowActions() {
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
      <button class="edit-row icon-button" type="button" data-edit-condominium="${safeId}">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
        <span>Editar</span>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-condominium="${safeId}">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
        <span>Borrar</span>
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
      <button class="edit-row icon-button" type="button" data-edit-company="${safeId}">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
        <span>Editar</span>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-company="${safeId}">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
        <span>Borrar</span>
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
      <button class="edit-row icon-button" type="button" data-edit-user="${safeId}">
        <svg aria-hidden="true"><use href="#icon-pencil"></use></svg>
        <span>Editar</span>
      </button>
      <button class="delete-row icon-button" type="button" data-delete-user="${safeId}">
        <svg aria-hidden="true"><use href="#icon-trash"></use></svg>
        <span>Borrar</span>
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
  const [companies, condominiums, roles, units, users] = await Promise.all([
    apiFetch("/api/v1/companies/?page=1&page_size=200"),
    apiFetch("/api/v1/condominiums/?page=1&page_size=200"),
    apiFetch("/api/v1/roles/?page=1&page_size=200"),
    apiFetch("/api/v1/units/?page=1&page_size=200"),
    apiFetch("/api/v1/users/?page=1&page_size=200"),
  ]);
  state.companies = companies.items || [];
  state.condominiums = condominiums.items || [];
  state.roles = (roles.items || []).filter((role) => ["vecino", "comite", "supervisor", "conserje"].includes(role.code));
  state.units = units.items || [];
  state.usersLookup = users.items || [];
}

async function openGenericForm(id = null) {
  const resource = resources[state.currentView];
  if (!resource?.fields) return;

  $("#genericFormError").hidden = true;
  if (resource.fields.some((field) => ["company", "condominium", "user"].includes(field.type))) {
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
    return `<label>${label}<select data-generic-field="${name}"${required}><option value="">Selecciona empresa</option>${state.companies
      .map((company) => `<option value="${escapeHtml(company.id)}"${value === company.id ? " selected" : ""}>${escapeHtml(company.name)}</option>`)
      .join("")}</select></label>`;
  }

  if (field.type === "condominium") {
    return `<label>${label}<select data-generic-field="${name}"><option value="">Ticket general empresa</option>${state.condominiums
      .map((condominium) => `<option value="${escapeHtml(condominium.id)}" data-company-id="${escapeHtml(condominium.company_id || "")}"${value === condominium.id ? " selected" : ""}>${escapeHtml(condominium.name)}</option>`)
      .join("")}</select></label>`;
  }

  if (field.type === "user") {
    return `<label>${label}<select data-generic-field="${name}"><option value="">Sin asignar</option>${state.usersLookup
      .map((user) => `<option value="${escapeHtml(user.id)}"${value === user.id ? " selected" : ""}>${escapeHtml(user.full_name || user.email)}</option>`)
      .join("")}</select></label>`;
  }

  if (field.type === "textarea" || field.type === "json") {
    const textareaValue = field.type === "json" ? JSON.stringify(value || {}, null, 2) : value || "";
    return `<label class="span-2">${label}<textarea data-generic-field="${name}" data-field-type="${field.type}" rows="4"${required}>${escapeHtml(textareaValue)}</textarea></label>`;
  }

  const inputType = field.type === "datetime" ? "datetime-local" : field.type || "text";
  const inputValue = field.type === "datetime" && value ? String(value).slice(0, 16) : value;
  return `<label>${label}<input data-generic-field="${name}" type="${inputType}" value="${escapeHtml(inputValue || "")}"${required}${maxlength} /></label>`;
}

function buildGenericPayload(resource) {
  const payload = {};
  resource.fields.forEach((field) => {
    const element = $(`[data-generic-field="${field.name}"]`);
    if (!element) return;
    if (field.type === "json") {
      payload[field.name] = parseJsonText(element.value, {});
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
    await apiFetch(id ? `${resource.endpoint}${id}` : resource.endpoint, {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildGenericPayload(resource)),
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
    message: `Esta accion eliminara el ${resource.singular} seleccionado.`,
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
    await ensureCompaniesLoaded();
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
    message: "Esta accion eliminara la empresa seleccionada. Si tiene datos relacionados, la API puede impedir el borrado.",
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
    message: "Esta accion eliminara el usuario seleccionado. No se puede deshacer desde el backoffice.",
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
  $("#condominiumMetadata").value = JSON.stringify(item?.metadata || {}, null, 2);
}

async function saveCondominium(event) {
  event.preventDefault();
  $("#condominiumFormError").hidden = true;

  try {
    const id = $("#condominiumId").value;
    const payload = buildCondominiumPayload();
    await apiFetch(id ? `/api/v1/condominiums/${id}` : "/api/v1/condominiums/", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
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
    metadata: parseJsonField("#condominiumMetadata", {}),
  };
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
    message: "Esta accion eliminara el condominio seleccionado. No se puede deshacer desde el backoffice.",
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
$("#cancelCondominiumButton").addEventListener("click", returnToCondominiumList);
$("#condominiumForm").addEventListener("submit", saveCondominium);
$("#deleteCondominiumButton").addEventListener("click", deleteCurrentCondominium);
$("#cancelUserButton").addEventListener("click", returnToUserList);
$("#userForm").addEventListener("submit", saveUser);
$("#addMembershipButton").addEventListener("click", () => addMembershipRow());
$("#deleteUserButton").addEventListener("click", deleteCurrentUser);
$("#confirmCancelButton").addEventListener("click", () => closeConfirmModal(false));
$("#confirmAcceptButton").addEventListener("click", () => closeConfirmModal(true));
$("#confirmModal").addEventListener("click", (event) => {
  if (event.target === $("#confirmModal")) closeConfirmModal(false);
});
document.addEventListener("keydown", (event) => {
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
  if (!companySelect || !condominiumSelect) return;

  const syncCondominiumOptions = () => {
    const selectedCompanyId = companySelect.value;
    Array.from(condominiumSelect.options).forEach((option) => {
      const optionCompanyId = option.dataset.companyId;
      option.hidden = Boolean(optionCompanyId && selectedCompanyId && !sameId(optionCompanyId, selectedCompanyId));
    });
    const selectedOption = condominiumSelect.selectedOptions[0];
    if (selectedOption?.hidden) condominiumSelect.value = "";
  };

  companySelect.addEventListener("change", syncCondominiumOptions);
  syncCondominiumOptions();
}

bootstrap();
