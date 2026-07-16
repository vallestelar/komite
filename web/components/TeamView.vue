<script setup lang="ts">
type TeamMember = {
  id: string;
  user_id: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  portal_profile: string;
  company_profile?: string | null;
  organization_position?: string | null;
  responsibility?: string | null;
  is_primary: boolean;
  status: string;
};

const { request } = useApi();
const { company } = useAuth();

const members = ref<TeamMember[]>([]);
const errorMessage = ref("");

const activeMembers = computed(() => members.value.filter((member) => member.status === "active"));
const principalMembers = computed(() => activeMembers.value.filter((member) => member.is_primary));

const loadTeam = async () => {
  errorMessage.value = "";
  try {
    const data = await request<{ items?: TeamMember[] }>("/api/v1/portal/team/");
    members.value = data.items || [];
  } catch (error) {
    members.value = [];
    errorMessage.value = readableError(error);
  }
};

const profileLabel = (profile: string | null | undefined) => {
  const normalized = (profile || "").trim().toLowerCase();
  if (normalized === "project_manager" || normalized.includes("project")) return "Project manager";
  if (normalized === "supervisor") return "Supervisor";
  if (normalized === "executive" || normalized.includes("ejecutiv")) return "Ejecutivo";
  if (normalized === "none" || normalized.includes("sin acceso")) return "Sin acceso al portal";
  return profile || "Sin perfil";
};

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

const profileBadgeClass = (profile: string | null | undefined) => {
  const normalized = (profile || "").trim().toLowerCase();
  if (normalized === "project_manager" || normalized.includes("project")) return "is-project-manager";
  if (normalized === "supervisor") return "is-supervisor";
  if (normalized === "executive" || normalized.includes("ejecutiv")) return "is-executive";
  return "is-neutral-profile";
};

const initials = (name: string) => name
  .split(" ")
  .filter(Boolean)
  .slice(0, 2)
  .map((part) => part[0])
  .join("")
  .toUpperCase();

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo cargar el equipo.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

onMounted(loadTeam);
</script>

<template>
  <section class="panel team-panel">
    <div class="dashboard-hero team-hero">
      <div>
        <p class="eyebrow">Administración</p>
        <h2>Quién es quién en la empresa</h2>
        <p class="hero-copy">{{ company?.name || "Empresa administradora" }}</p>
      </div>
      <div class="committee-summary">
        <article>
          <span>Activos</span>
          <strong>{{ activeMembers.length }}</strong>
        </article>
        <article>
          <span>Principales</span>
          <strong>{{ principalMembers.length }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div v-if="members.length" class="team-grid">
      <article v-for="member in members" :key="member.id" class="team-card">
        <div class="team-card-header">
          <span class="team-avatar" :class="profileBadgeClass(member.portal_profile || member.company_profile)" aria-hidden="true">{{ initials(member.full_name) }}</span>
          <div>
            <p class="team-profile">
              <span>Perfil en el Portal:</span>
              <strong>{{ profileLabel(member.portal_profile || member.company_profile) }}</strong>
            </p>
            <h3>{{ member.full_name }}</h3>
          </div>
          <span class="status-badge" :class="statusBadgeClass(member.status)">
            <span aria-hidden="true"></span>
            {{ statusLabel(member.status) }}
          </span>
        </div>

        <div class="team-role">
          <svg class="icon" aria-hidden="true"><use href="#icon-briefcase" /></svg>
          <div>
            <span>Puesto</span>
            <strong>{{ member.responsibility || member.organization_position || "Sin puesto definido" }}</strong>
          </div>
        </div>

        <div class="committee-details">
          <p v-if="member.email">
            <svg class="icon" aria-hidden="true"><use href="#icon-message" /></svg>
            <span>{{ member.email }}</span>
          </p>
          <p v-if="member.phone">
            <svg class="icon" aria-hidden="true"><use href="#icon-phone" /></svg>
            <span>{{ member.phone }}</span>
          </p>
          <p v-if="member.is_primary">
            <svg class="icon" aria-hidden="true"><use href="#icon-shield" /></svg>
            <span>Contacto principal</span>
          </p>
        </div>
      </article>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-users" /></svg>
      </span>
      <h2>Sin equipo operativo cargado</h2>
      <p class="placeholder-copy">Aún no hay personas definidas en el equipo base de la empresa.</p>
    </div>
  </section>
</template>
