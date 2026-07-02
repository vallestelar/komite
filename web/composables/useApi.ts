export const useApi = () => {
  const config = useRuntimeConfig();
  const { token } = useAuth();

  const apiBase = computed(() => {
    if (import.meta.client) {
      return localStorage.getItem("komite_api_base") || config.public.apiBase;
    }

    return config.public.apiBase;
  });

  const request = async <T>(path: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    if (token.value) headers.set("Authorization", `Bearer ${token.value}`);

    const response = await fetch(`${apiBase.value}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }

    return response.json() as Promise<T>;
  };

  return { request };
};
