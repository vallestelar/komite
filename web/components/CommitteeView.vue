<script setup lang="ts">
type PageMeta = {
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

type CommitteeMember = {
  id: string;
  condominium_id: string;
  user_id?: string | null;
  unit_contact_id?: string | null;
  unit_id?: string | null;
  position: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  status: string;
  receives_notifications: boolean;
  display_order: number;
  notes?: string | null;
};

const { request } = useApi();
const { activeCondominium } = useAuth();

const members = ref<CommitteeMember[]>([]);
const meta = reactive<PageMeta>({ total: 0, page: 1, page_size: 100, pages: 1 });
const errorMessage = ref("");

const sortedMembers = computed(() => {
  return [...members.value].sort((left, right) => {
    if (left.status !== right.status) return left.status === "active" ? -1 : 1;
    if (left.display_order !== right.display_order) return left.display_order - right.display_order;
    return left.full_name.localeCompare(right.full_name);
  });
});

const activeCount = computed(() => members.value.filter((member) => member.status === "active").length);

const loadCommittee = async () => {
  errorMessage.value = "";
  try {
    const data = await request<{ items?: CommitteeMember[]; meta?: PageMeta }>("/api/v1/committee-members/?page=1&page_size=100&order_by=display_order&order_by=full_name");
    members.value = data.items || [];
    Object.assign(meta, data.meta || { total: members.value.length, page: 1, page_size: 100, pages: 1 });
  } catch (error) {
    members.value = [];
    errorMessage.value = readableError(error);
  }
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

const notificationLabel = (value: boolean) => value ? "Recibe notificaciones" : "No recibe notificaciones";

const periodLabel = (member: CommitteeMember) => {
  if (member.start_date && member.end_date) return `${formatDate(member.start_date)} - ${formatDate(member.end_date)}`;
  if (member.start_date) return `Desde ${formatDate(member.start_date)}`;
  if (member.end_date) return `Hasta ${formatDate(member.end_date)}`;
  return "Sin periodo definido";
};

const formatDate = (value: string) => {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-CL", { day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo cargar el comite.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
};

watch(() => activeCondominium.value?.id, loadCommittee, { immediate: true });
</script>

<template>
  <section class="panel committee-panel">
    <div class="dashboard-hero committee-hero">
      <div>
        <p class="eyebrow">Comite</p>
        <h2>Miembros del comite</h2>
        <p class="hero-copy">{{ activeCondominium?.name || "Condominio activo" }}</p>
      </div>
      <div class="committee-summary">
        <article>
          <span>Activos</span>
          <strong>{{ activeCount }}</strong>
        </article>
        <article>
          <span>Total</span>
          <strong>{{ meta.total }}</strong>
        </article>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error result-message">{{ errorMessage }}</p>

    <div v-if="sortedMembers.length" class="committee-grid">
      <article v-for="member in sortedMembers" :key="member.id" class="committee-card">
        <div class="committee-card-header">
          <span class="committee-avatar" aria-hidden="true">
            <svg class="icon"><use href="#icon-shield" /></svg>
          </span>
          <div>
            <p class="committee-position">{{ member.position }}</p>
            <h3>{{ member.full_name }}</h3>
          </div>
          <span class="status-badge" :class="statusBadgeClass(member.status)">
            <span aria-hidden="true"></span>
            {{ statusLabel(member.status) }}
          </span>
        </div>

        <div class="committee-details">
          <p>
            <svg class="icon" aria-hidden="true"><use href="#icon-calendar" /></svg>
            <span>{{ periodLabel(member) }}</span>
          </p>
          <p v-if="member.email">
            <svg class="icon" aria-hidden="true"><use href="#icon-message" /></svg>
            <span>{{ member.email }}</span>
          </p>
          <p v-if="member.phone">
            <svg class="icon" aria-hidden="true"><use href="#icon-phone" /></svg>
            <span>{{ member.phone }}</span>
          </p>
          <p>
            <svg class="icon" aria-hidden="true"><use href="#icon-bell" /></svg>
            <span>{{ notificationLabel(member.receives_notifications) }}</span>
          </p>
        </div>

        <p v-if="member.notes" class="committee-notes">{{ member.notes }}</p>
      </article>
    </div>

    <div v-else-if="!errorMessage" class="committee-empty">
      <span class="committee-avatar large" aria-hidden="true">
        <svg class="icon"><use href="#icon-users" /></svg>
      </span>
      <h2>Sin miembros registrados</h2>
      <p class="placeholder-copy">Aun no hay miembros de comite cargados para este condominio.</p>
    </div>
  </section>
</template>
