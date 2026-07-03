<script setup lang="ts">
import type { KomiteCondominium } from "~/composables/useAuth";

const email = ref("admin@komite.cl");
const password = ref("");
const error = ref("");
const loading = ref(false);
const step = ref<"credentials" | "condominium">("credentials");
const selectedCondominiumId = ref("");
const pendingSession = ref<{
  access_token: string;
  user: Record<string, unknown>;
  company?: { id: string; name: string } | null;
  condominiums?: KomiteCondominium[];
} | null>(null);

const { request } = useApi();
const { setSession } = useAuth();

const availableCondominiums = computed(() => {
  const byId = new Map<string, KomiteCondominium>();
  for (const condominium of pendingSession.value?.condominiums || []) {
    if (!byId.has(condominium.id)) {
      byId.set(condominium.id, condominium);
    }
  }
  return Array.from(byId.values());
});

const submit = async () => {
  error.value = "";
  loading.value = true;

  try {
    const session = await request<{
      access_token: string;
      user: Record<string, unknown>;
      company?: { id: string; name: string } | null;
      condominiums?: KomiteCondominium[];
    }>("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
    });

    if (!session.condominiums?.length) {
      error.value = "Tu usuario no tiene condominios habilitados para este portal.";
      return;
    }

    pendingSession.value = session;
    selectedCondominiumId.value = availableCondominiums.value[0]?.id || "";
    step.value = "condominium";
  } catch {
    error.value = "No se pudo iniciar sesion.";
  } finally {
    loading.value = false;
  }
};

const finishLogin = () => {
  error.value = "";
  const session = pendingSession.value;
  const condominium = availableCondominiums.value.find((item) => item.id === selectedCondominiumId.value);

  if (!session || !condominium) {
    error.value = "Selecciona un condominio para continuar.";
    return;
  }

  setSession(session, condominium);
};

const backToCredentials = () => {
  step.value = "credentials";
  pendingSession.value = null;
  selectedCondominiumId.value = "";
  password.value = "";
  error.value = "";
};
</script>

<template>
  <main class="login-shell">
    <section class="login-panel">
      <img class="login-logo" src="/assets/komite-logo.png" alt="Komite" />
      <p class="login-context">Portal administrador</p>
      <form v-if="step === 'credentials'" class="login-form" @submit.prevent="submit">
        <label>
          Email
          <input v-model="email" name="email" type="email" autocomplete="email" required />
        </label>
        <label>
          Password
          <input v-model="password" name="password" type="password" autocomplete="current-password" required />
        </label>
        <button class="button" type="submit" :disabled="loading">
          {{ loading ? "Entrando..." : "Entrar" }}
        </button>
        <p v-if="error" class="form-error">{{ error }}</p>
      </form>

      <form v-else class="login-form" @submit.prevent="finishLogin">
        <div class="login-selection-summary">
          <span>{{ pendingSession?.company?.name || "Empresa administradora" }}</span>
          <strong>{{ pendingSession?.user?.full_name || pendingSession?.user?.email }}</strong>
        </div>
        <label>
          Condominio
          <select v-model="selectedCondominiumId" name="condominium" required>
            <option v-for="condominium in availableCondominiums" :key="condominium.id" :value="condominium.id">
              {{ condominium.name }}
            </option>
          </select>
        </label>
        <button class="button" type="submit">Entrar al portal</button>
        <button class="button ghost" type="button" @click="backToCredentials">Cambiar usuario</button>
        <p v-if="error" class="form-error">{{ error }}</p>
      </form>
    </section>
  </main>
</template>
