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
  evidence_count?: number;
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
const evidenceFiles = ref<File[]>([]);
const optimizingEvidence = ref(false);

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
    const body = new FormData();
    body.append("submitted_by_name", form.submitted_by_name);
    body.append("submitted_by_email", form.submitted_by_email || "");
    body.append("execution_date", form.execution_date || "");
    body.append("result", form.result);
    body.append("work_performed", form.work_performed);
    body.append("findings", form.findings || "");
    body.append("materials_used", form.materials_used || "");
    body.append("recommendations", form.recommendations || "");
    body.append("next_visit_required", String(form.next_visit_required));
    body.append("additional_comments", form.additional_comments || "");
    evidenceFiles.value.forEach((file) => body.append("evidence_files", file));

    const response = await fetch(`${apiBase.value}/api/v1/public/external-service-orders/${token.value}/submit`, {
      method: "POST",
      body,
    });
    if (!response.ok) throw new Error(await response.text() || `HTTP ${response.status}`);
    const result = await response.json() as SubmissionResponse;
    const photoText = result.evidence_count ? ` Fotos adjuntas: ${result.evidence_count}.` : "";
    successMessage.value = `Informe enviado correctamente. Komite notificara al administrador para revision.${photoText}`;
    generatedText.value = result.ai_generated_text || "";
    if (order.value) order.value.status = result.status;
  } catch (error) {
    errorMessage.value = readableError(error);
  } finally {
    submitting.value = false;
  }
};

const optimizeEvidenceFile = (file: File): Promise<File> => {
  const maxBytes = 1.2 * 1024 * 1024;
  const maxSide = 1600;
  if (!file.type.startsWith("image/") || file.size <= maxBytes) return Promise.resolve(file);

  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onerror = () => resolve(file);
    reader.onload = () => {
      const image = new Image();
      image.onerror = () => resolve(file);
      image.onload = () => {
        const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
        const width = Math.max(1, Math.round(image.width * scale));
        const height = Math.max(1, Math.round(image.height * scale));
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        if (!context) {
          resolve(file);
          return;
        }
        context.drawImage(image, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(file);
              return;
            }
            const cleanName = file.name.replace(/\.[^.]+$/, "") || "evidencia";
            resolve(new File([blob], `${cleanName}.jpg`, { type: "image/jpeg", lastModified: Date.now() }));
          },
          "image/jpeg",
          0.82,
        );
      };
      image.src = String(reader.result || "");
    };
    reader.readAsDataURL(file);
  });
};

const selectEvidenceFiles = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  optimizingEvidence.value = true;
  try {
    const selected = Array.from(input.files || []).slice(0, 8);
    evidenceFiles.value = await Promise.all(selected.map((file) => optimizeEvidenceFile(file)));
  } finally {
    optimizingEvidence.value = false;
  }
};

const removeEvidenceFile = (index: number) => {
  evidenceFiles.value = evidenceFiles.value.filter((_, fileIndex) => fileIndex !== index);
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
        <img src="/assets/komite-logo-new.png" alt="Komite" />
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
          <section class="public-evidence-field wide-field">
            <div>
              <span>Fotos de evidencia</span>
              <small>Opcional. Puedes adjuntar hasta 8 imagenes desde el movil.</small>
            </div>
            <input type="file" accept="image/*" multiple capture="environment" @change="selectEvidenceFiles" />
            <small v-if="optimizingEvidence">Optimizando fotos antes de enviarlas...</small>
            <ul v-if="evidenceFiles.length" class="public-evidence-list">
              <li v-for="(file, index) in evidenceFiles" :key="`${file.name}-${index}`">
                <span>{{ file.name }}</span>
                <button type="button" @click="removeEvidenceFile(index)">Quitar</button>
              </li>
            </ul>
          </section>
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
