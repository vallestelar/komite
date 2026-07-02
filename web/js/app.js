const API_BASE = localStorage.getItem("komite_api_base") || "http://localhost:8000";

const state = {
  token: localStorage.getItem("komite_token"),
  user: JSON.parse(localStorage.getItem("komite_user") || "null"),
  currentView: "dashboard",
};

const resources = {
  condominiums: {
    title: "Condominios",
    endpoint: "/api/v1/condominiums/",
    columns: ["id", "name", "address", "status", "units_count"],
  },
  incidents: {
    title: "Incidencias",
    endpoint: "/api/v1/incidents/",
    columns: ["id", "category", "priority", "status", "created_at"],
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
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  return response.json();
}

function setSession(data) {
  state.token = data.access_token;
  state.user = data.user;
  localStorage.setItem("komite_token", state.token);
  localStorage.setItem("komite_user", JSON.stringify(state.user));
}

function clearSession() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("komite_token");
  localStorage.removeItem("komite_user");
}

function showLogin() {
  $("#loginView").hidden = false;
  $("#officeView").hidden = true;
}

function showOffice() {
  $("#loginView").hidden = true;
  $("#officeView").hidden = false;
  $("#userName").textContent = state.user?.full_name || state.user?.email || "Usuario";
  openView("dashboard");
}

async function login(event) {
  event.preventDefault();
  $("#loginError").hidden = true;

  try {
    const data = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: $("#email").value,
        password: $("#password").value,
      }),
    });
    setSession(data);
    showOffice();
  } catch (error) {
    $("#loginError").textContent = "No se pudo iniciar sesion.";
    $("#loginError").hidden = false;
  }
}

async function loadDashboard() {
  const [condominiums, incidents, tasks, reports] = await Promise.all([
    apiFetch("/api/v1/condominiums/?page=1&page_size=5"),
    apiFetch("/api/v1/incidents/?page=1&page_size=5"),
    apiFetch("/api/v1/tasks/?page=1&page_size=5"),
    apiFetch("/api/v1/reports/?page=1&page_size=5"),
  ]);

  $("#metricCondominiums").textContent = condominiums.meta.total;
  $("#metricIncidents").textContent = incidents.meta.total;
  $("#metricTasks").textContent = tasks.meta.total;
  $("#metricReports").textContent = reports.meta.total;
  renderList("#recentIncidents", incidents.items, "category", "status");
  renderList("#recentTasks", tasks.items, "title", "status");
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
  $("#audioPanel").hidden = panel !== "audio";
}

async function openView(view) {
  state.currentView = view;
  $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));

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

  $("#viewTitle").textContent = resources[view].title;
  showPanel("table");
  await loadTable();
}

async function loadTable() {
  const resource = resources[state.currentView];
  const q = encodeURIComponent($("#searchInput").value.trim());
  const data = await apiFetch(`${resource.endpoint}?page=1&page_size=50${q ? `&q=${q}` : ""}`);
  renderTable(resource.columns, data.items);
}

function renderTable(columns, items) {
  $("#tableHead").innerHTML = `<tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>`;
  $("#tableBody").innerHTML = items
    .map((item) => `<tr>${columns.map((column) => `<td>${escapeHtml(formatCell(item[column]))}</td>`).join("")}</tr>`)
    .join("");
}

function formatCell(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
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
    $("#audioResult").textContent = "No se pudo procesar el audio.";
  }
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
$("#logoutButton").addEventListener("click", () => {
  clearSession();
  showLogin();
});
$("#refreshButton").addEventListener("click", loadTable);
$("#searchInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadTable();
});
$("#audioForm").addEventListener("submit", uploadAudio);
$$(".nav-item").forEach((button) => button.addEventListener("click", () => openView(button.dataset.view)));

if (state.token) {
  showOffice();
} else {
  showLogin();
}

