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
const { activeCondominium, company, condominiums, user, clearSession, refreshToken, setActiveCondominium } = useAuth();
const currentView = ref("dashboard");
const viewRefreshKey = ref(0);
const sidebarCollapsed = ref(false);
const collapsedGroups = ref<string[]>([]);
const workspaceRef = ref<HTMLElement | null>(null);

const menuGroups: MenuGroup[] = [
  {
    id: "inicio",
    label: "Inicio",
    items: [{ id: "dashboard", label: "Dashboard", icon: "dashboard", view: "dashboard" }],
  },
  {
    id: "comunidades",
    label: "Comunidades",
    items: [
      { id: "neighbors", label: "Vecinos y unidades", icon: "home", view: "neighbors" },
      { id: "committee", label: "Comite", icon: "users", view: "committee" },
    ],
  },
  {
    id: "operacion",
    label: "Operacion diaria",
    items: [
      { id: "incidents", label: "Incidencias", icon: "alert", view: "incidents" },
      { id: "tasks", label: "Tareas", icon: "checks", view: "tasks" },
      { id: "inspections", label: "Inspecciones", icon: "clipboard", view: "inspections" },
      { id: "files", label: "Archivos", icon: "file-text", view: "files" },
    ],
  },
  {
    id: "comunicacion",
    label: "Informes y comunicacion",
    items: [
      { id: "reports", label: "Informes", icon: "file-text", view: "reports" },
      { id: "communications", label: "Comunicados", icon: "message", view: "communications" },
    ],
  },
  {
    id: "herramientas",
    label: "Herramientas",
    items: [
      { id: "tools", label: "Centro de herramientas", icon: "tool", view: "tools" },
      { id: "audio", label: "Audio IA", icon: "mic", view: "audio" },
      { id: "support", label: "Soporte Komite", icon: "help-circle", view: "support" },
    ],
  },
];

const toolViewTitles: Record<string, string> = {
  edifito: "Edifito",
  "edifito-neighbors-import": "Carga vecinos Edifito",
  "comunidad-feliz": "Comunidad Feliz",
  audio: "Procesar audio",
  "spreadsheet-tools": "Importar planillas",
  "monthly-summary": "Resumen mensual",
};

const currentTitle = computed(() => {
  const item = menuGroups.flatMap((group) => group.items).find((entry) => entry.view === currentView.value);
  return item?.label || toolViewTitles[currentView.value] || "Modulo";
});

const userName = computed(() => user.value?.full_name || user.value?.email || "Usuario");
const contextLabel = computed(() => activeCondominium.value?.name || "Sin condominio");
const tenantLabel = computed(() => company.value?.name || "Empresa administradora");
const activeCondominiumId = computed({
  get: () => activeCondominium.value?.id || "",
  set: (id: string) => {
    const selected = condominiums.value.find((condominium) => condominium.id === id);
    if (!selected) return;
    setActiveCondominium(selected);
    viewRefreshKey.value += 1;
    nextTick(() => {
      workspaceRef.value?.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    });
  },
});

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
          <label class="context-chip" :title="tenantLabel">
            <svg class="icon" aria-hidden="true"><use href="#icon-building" /></svg>
            <select v-model="activeCondominiumId" :aria-label="`Condominio activo: ${contextLabel}`">
              <option v-for="condominium in condominiums" :key="condominium.id" :value="condominium.id">
                {{ condominium.name }}
              </option>
            </select>
          </label>
          <span>{{ userName }}</span>
          <button class="button orange" type="button" @click="logout">
            <svg class="icon" aria-hidden="true"><use href="#icon-log-out" /></svg>
            <span>Salir</span>
          </button>
        </div>
      </header>

      <DashboardView v-if="currentView === 'dashboard'" :key="`dashboard-${activeCondominiumId}-${viewRefreshKey}`" @open-view="selectView" />
      <NeighborsUnitsView v-else-if="currentView === 'neighbors'" :key="`neighbors-${activeCondominiumId}-${viewRefreshKey}`" />
      <CommitteeView v-else-if="currentView === 'committee'" :key="`committee-${activeCondominiumId}-${viewRefreshKey}`" />
      <ComunidadFelizTool v-else-if="currentView === 'comunidad-feliz'" :key="`comunidad-feliz-${activeCondominiumId}-${viewRefreshKey}`" />
      <ToolsView v-else-if="['tools', 'edifito', 'edifito-neighbors-import'].includes(currentView)" :key="`tools-${currentView}-${activeCondominiumId}-${viewRefreshKey}`" :view="currentView" @open-view="selectView" />
      <PlaceholderView v-else :key="`${currentView}-${activeCondominiumId}-${viewRefreshKey}`" :title="currentTitle" :view="currentView" />
    </section>

    <SvgSprite />
  </main>
</template>
