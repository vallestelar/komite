<script setup lang="ts">
const { isLoading } = useLoading();
</script>

<template>
  <NuxtPage />
  <Transition name="loading-fade">
    <div v-if="isLoading" class="loading-overlay" role="status" aria-live="polite" aria-label="Cargando">
      <div class="loading-card">
        <span class="loading-spinner" aria-hidden="true"></span>
        <span>Cargando...</span>
      </div>
    </div>
  </Transition>
</template>
