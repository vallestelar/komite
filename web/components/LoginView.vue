<script setup lang="ts">
const email = ref("admin@komite.cl");
const password = ref("");
const error = ref("");
const loading = ref(false);

const { request } = useApi();
const { setSession } = useAuth();

const submit = async () => {
  error.value = "";
  loading.value = true;

  try {
    const session = await request<{ access_token: string; user: Record<string, unknown> }>("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
    });
    setSession(session);
  } catch {
    error.value = "No se pudo iniciar sesion.";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <main class="login-shell">
    <section class="login-panel">
      <img class="login-logo" src="/assets/komite-logo.png" alt="Komite" />
      <p class="login-context">Portal administrador</p>
      <form class="login-form" @submit.prevent="submit">
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
    </section>
  </main>
</template>
