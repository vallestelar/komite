<script setup lang="ts">
type MenuItem = {
  id: string;
  label: string;
  icon: string;
  view: string;
};

type MenuGroup = {
  id: string;
  label: string;
  items: MenuItem[];
};

const SIDEBAR_KEY = "komite_sidebar_collapsed";
const NAV_GROUPS_KEY = "komite_nav_groups_collapsed";

const config = useRuntimeConfig();
const { activeCondominium, company, user, clearSession, refreshToken } = useAuth();
const currentView = ref("dashboard");
const sidebarCollapsed = ref(false);
const collapsedGroups = ref<string[]>([]);
const workspaceRef = ref<HTMLElement | null>(null);

const menuGroups: MenuGroup[] = [
  {
    id: "inicio",
    label: "Inicio",
    items: [{ id: "dashboard", label: "Panel operativo", icon: "dashboard", view: "dashboard" }],
  },
  {
    id: "cartera",
    label: "Cartera",
    items: [
      { id: "condominiums", label: "Condominios", icon: "building", view: "condominiums" },
      { id: "maintenance", label: "Mantenciones", icon: "checks", view: "maintenance" },
      { id: "history", label: "Historial", icon: "file-text", view: "history" },
    ],
  },
  {
    id: "operacion",
    label: "Operacion diaria",
    items: [
      { id: "incidents", label: "Incidencias", icon: "alert", view: "incidents" },
      { id: "tasks", label: "Tareas", icon: "checks", view: "tasks" },
      { id: "inspections", label: "Inspecciones", icon: "clipboard", view: "inspections" },
      { id: "evidence", label: "Evidencias", icon: "file-text", view: "evidence" },
    ],
  },
  {
    id: "comunicacion",
    label: "Informes y comunicacion",
    items: [
      { id: "reports", label: "Informes", icon: "file-text", view: "reports" },
      { id: "communications", label: "Comunicados", icon: "message", view: "communications" },
      { id: "recipients", label: "Destinatarios", icon: "users", view: "recipients" },
      { id: "publication-rules", label: "Reglas de publicacion", icon: "shield", view: "publication-rules" },
    ],
  },
  {
    id: "herramientas",
    label: "Herramientas",
    items: [
      { id: "tools", label: "Centro de herramientas", icon: "tool", view: "tools" },
      { id: "edifito", label: "Edifito", icon: "table", view: "edifito" },
      { id: "comunidad-feliz", label: "Comunidad Feliz", icon: "home", view: "comunidad-feliz" },
      { id: "audio", label: "Procesar audio", icon: "mic", view: "audio" },
      { id: "spreadsheet-tools", label: "Importar planillas", icon: "table", view: "spreadsheet-tools" },
      { id: "monthly-summary", label: "Resumen mensual", icon: "spark", view: "monthly-summary" },
    ],
  },
  {
    id: "gestion",
    label: "Gestion interna",
    items: [
      { id: "team", label: "Equipo", icon: "user", view: "team" },
      { id: "accesses", label: "Accesos operativos", icon: "shield", view: "accesses" },
      { id: "settings", label: "Preferencias", icon: "settings", view: "settings" },
    ],
  },
];

const currentTitle = computed(() => {
  const item = menuGroups.flatMap((group) => group.items).find((entry) => entry.view === currentView.value);
  return item?.label || "Modulo";
});

const userName = computed(() => user.value?.full_name || user.value?.email || "Usuario");
const contextLabel = computed(() => activeCondominium.value?.name || "Sin condominio");
const tenantLabel = computed(() => company.value?.name || "Empresa administradora");

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
  localStorage.setItem(SIDEBAR_KEY, String(sidebarCollapsed.value));
};

const toggleGroup = (groupId: string) => {
  collapsedGroups.value = collapsedGroups.value.includes(groupId)
    ? collapsedGroups.value.filter((item) => item !== groupId)
    : [...collapsedGroups.value, groupId];
  localStorage.setItem(NAV_GROUPS_KEY, JSON.stringify(collapsedGroups.value));
};

const isGroupCollapsed = (groupId: string) => collapsedGroups.value.includes(groupId);

const selectView = (view: string) => {
  currentView.value = view;
  nextTick(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    workspaceRef.value?.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  });
};

const logout = async () => {
  const tokenToRevoke = refreshToken.value;
  if (tokenToRevoke && import.meta.client) {
    const apiBase = localStorage.getItem("komite_api_base") || config.public.apiBase;
    try {
      await fetch(`${apiBase}/api/v1/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: tokenToRevoke }),
      });
    } catch {
      // Local logout still wins if the API is unreachable.
    }
  }
  clearSession();
};

onMounted(() => {
  sidebarCollapsed.value = localStorage.getItem(SIDEBAR_KEY) === "true";
  try {
    collapsedGroups.value = JSON.parse(localStorage.getItem(NAV_GROUPS_KEY) || "[]");
  } catch {
    collapsedGroups.value = [];
  }
});
</script>

<template>
  <main class="office-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <aside class="sidebar">
      <span class="sidebar-logo-crop">
        <img class="sidebar-logo" src="/assets/komite-logo.png" alt="Komite" />
      </span>
      <span class="sidebar-context">Portal administrador</span>

      <nav class="side-nav" aria-label="Menu principal">
        <section
          v-for="group in menuGroups"
          :key="group.id"
          class="nav-group"
          :class="{ collapsed: isGroupCollapsed(group.id) }"
        >
          <button class="nav-section" type="button" :aria-expanded="!isGroupCollapsed(group.id)" @click="toggleGroup(group.id)">
            <span>{{ group.label }}</span>
            <svg class="icon" aria-hidden="true"><use href="#icon-chevron-down" /></svg>
          </button>
          <div class="nav-group-items">
            <button
              v-for="item in group.items"
              :key="item.id"
              class="nav-item"
              :class="{ active: currentView === item.view }"
              type="button"
              :title="item.label"
              @click="selectView(item.view)"
            >
              <svg class="icon" aria-hidden="true"><use :href="`#icon-${item.icon}`" /></svg>
              <span class="nav-label">{{ item.label }}</span>
            </button>
          </div>
        </section>
      </nav>
    </aside>

    <section ref="workspaceRef" class="workspace">
      <header class="topbar">
        <div class="title-row">
          <button class="button ghost icon-only" type="button" :title="sidebarCollapsed ? 'Expandir menu' : 'Contraer menu'" @click="toggleSidebar">
            <svg class="icon" aria-hidden="true"><use href="#icon-panel-left" /></svg>
          </button>
          <h1>{{ currentTitle }}</h1>
        </div>
        <div class="user-chip">
          <span class="context-chip" :title="tenantLabel">
            <svg class="icon" aria-hidden="true"><use href="#icon-building" /></svg>
            <span>{{ contextLabel }}</span>
          </span>
          <span>{{ userName }}</span>
          <button class="button orange" type="button" @click="logout">
            <svg class="icon" aria-hidden="true"><use href="#icon-log-out" /></svg>
            <span>Salir</span>
          </button>
        </div>
      </header>

      <DashboardView v-if="currentView === 'dashboard'" @open-view="selectView" />
      <ComunidadFelizTool v-else-if="currentView === 'comunidad-feliz'" />
      <ToolsView v-else-if="['tools', 'edifito', 'audio', 'spreadsheet-tools', 'monthly-summary'].includes(currentView)" :view="currentView" />
      <PlaceholderView v-else :title="currentTitle" :view="currentView" />
    </section>

    <SvgSprite />
  </main>
</template>
