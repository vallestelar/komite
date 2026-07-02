<script setup lang="ts">
const { hydrate, isAuthenticated } = useAuth();

onMounted(() => {
  hydrate();
});
</script>

<template>
  <AppShell v-if="isAuthenticated" />
  <LoginView v-else />
</template>
