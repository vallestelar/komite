export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
    },
  },
  app: {
    head: {
      htmlAttrs: { lang: "es" },
      title: "Komite",
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content: "Front operativo de Komite para ejecutivas y administracion.",
        },
      ],
    },
  },
});
