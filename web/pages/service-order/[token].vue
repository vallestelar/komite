<script setup lang="ts">
type PublicOrder = {
  token_status: string;
  id: string;
  title: string;
  instructions?: string | null;
  provider_name: string;
  condominium_name: string;
  condominium_address?: string | null;
  event_title: string;
  event_description?: string | null;
  planned_date: string;
  asset_name?: string | null;
  status: string;
  expires_at?: string | null;
};

type SubmissionResponse = {
  id: string;
  status: string;
  execution_id?: string | null;
  ai_generated_text?: string | null;
  ai_error?: string | null;
};

const route = useRoute();
const config = useRuntimeConfig();
const token = computed(() => String(route.params.token || ""));
const apiBase = computed(() => {
  if (import.meta.client) {
    return localStorage.getItem("komite_api_base") || config.public.apiBase;
  }
  return config.public.apiBase;
});

const loading = ref(true);
const submitting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const order = ref<PublicOrder | null>(null);
const generatedText = ref("");

const form = reactive({
  submitted_by_name: "",
  submitted_by_email: "",
  execution_date: new Date().toISOString().slice(0, 10),
  result: "completed",
  work_performed: "",
  findings: "",
  materials_used: "",
  recommendations: "",
  next_visit_required: false,
  additional_comments: "",
});

const loadOrder = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    const response = await fetch(`${apiBase.value}/api/v1/public/external-service-orders/${token.value}`);
    if (!response.ok) throw new Error(await response.text() || `HTTP ${response.status}`);
    order.value = await response.json();
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    loading.value = false;
  }
};

const submitOrder = async () => {
  submitting.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  generatedText.value = "";
  try {
    const response = await fetch(`${apiBase.value}/api/v1/public/external-service-orders/${token.value}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        submitted_by_email: form.submitted_by_email || null,
        findings: form.findings || null,
        materials_used: form.materials_used || null,
        recommendations: form.recommendations || null,
        additional_comments: form.additional_comments || null,
      }),
    });
    if (!response.ok) throw new Error(await response.text() || `HTTP ${response.status}`);
    const result = await response.json() as SubmissionResponse;
    successMessage.value = "Informe enviado correctamente. Komite notificara al administrador para revision.";
    generatedText.value = result.ai_generated_text || "";
    if (order.value) order.value.status = result.status;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    submitting.value = false;
  }
};

const readableError = (error: unknown) => {
  const message = error instanceof Error ? error.message : "No se pudo completar la operacion.";
  try {
    const parsed = JSON.parse(message);
    if (typeof parsed.detail === "string") return parsed.detail;
    return JSON.stringify(parsed.detail || parsed);
  } catch {
    return message;
  }
};

onMounted(loadOrder);
</script>

<template>
  <main class="public-order-shell">
    <section class="public-order-panel">
      <div class="public-order-brand">
        <img src="/assets/komite-logo.png" alt="Komite" />
        <span>Orden de servicio</span>
      </div>

      <p v-if="loading" class="public-order-state">Cargando orden...</p>
      <p v-else-if="errorMessage" class="form-error">{{ errorMessage }}</p>

      <template v-else-if="order">
        <header class="public-order-header">
          <p class="eyebrow">Proveedor externo</p>
          <h1>{{ order.title }}</h1>
          <p>{{ order.condominium_name }}<span v-if="order.condominium_address"> · {{ order.condominium_address }}</span></p>
        </header>

        <dl class="public-order-summary">
          <div>
            <dt>Trabajo</dt>
            <dd>{{ order.event_title }}</dd>
          </div>
          <div v-if="order.asset_name">
            <dt>Activo</dt>
            <dd>{{ order.asset_name }}</dd>
          </div>
          <div>
            <dt>Fecha planificada</dt>
            <dd>{{ order.planned_date }}</dd>
          </div>
          <div>
            <dt>Proveedor</dt>
            <dd>{{ order.provider_name }}</dd>
          </div>
        </dl>

        <section v-if="order.instructions || order.event_description" class="public-order-instructions">
          <h2>Instrucciones</h2>
          <p>{{ order.instructions || order.event_description }}</p>
        </section>

        <p v-if="successMessage" class="form-success">{{ successMessage }}</p>

        <form v-if="order.status !== 'submitted' && order.status !== 'completed' && !successMessage" class="public-order-form" @submit.prevent="submitOrder">
          <label>
            Nombre de quien informa
            <input v-model="form.submitted_by_name" type="text" maxlength="160" required />
          </label>
          <label>
            Email
            <input v-model="form.submitted_by_email" type="email" maxlength="255" />
          </label>
          <label>
            Fecha de ejecucion
            <input v-model="form.execution_date" type="date" />
          </label>
          <label>
            Resultado
            <select v-model="form.result">
              <option value="completed">Completado</option>
              <option value="observed">Con observaciones</option>
              <option value="requires_action">Requiere accion</option>
              <option value="not_executed">No ejecutado</option>
            </select>
          </label>
          <label class="wide-field">
            Trabajo realizado
            <textarea v-model="form.work_performed" rows="4" required></textarea>
          </label>
          <label class="wide-field">
            Hallazgos
            <textarea v-model="form.findings" rows="3"></textarea>
          </label>
          <label class="wide-field">
            Materiales o repuestos utilizados
            <textarea v-model="form.materials_used" rows="2"></textarea>
          </label>
          <label class="wide-field">
            Recomendaciones
            <textarea v-model="form.recommendations" rows="3"></textarea>
          </label>
          <label class="public-switch">
            <input v-model="form.next_visit_required" type="checkbox" />
            <span>Requiere una proxima visita</span>
          </label>
          <label class="wide-field">
            Comentarios adicionales
            <textarea v-model="form.additional_comments" rows="3"></textarea>
          </label>
          <button class="button navy" type="submit" :disabled="submitting">
            {{ submitting ? "Enviando..." : "Enviar informe" }}
          </button>
        </form>

        <section v-if="generatedText" class="public-order-generated">
          <h2>Borrador generado</h2>
          <pre>{{ generatedText }}</pre>
        </section>
      </template>
    </section>
  </main>
</template>
