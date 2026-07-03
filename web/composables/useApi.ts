export const useApi = () => {
  const config = useRuntimeConfig();
  const { activeCondominium, clearSession, refreshToken, setSession, token } = useAuth();

  const apiBase = computed(() => {
    if (import.meta.client) {
      return localStorage.getItem("komite_api_base") || config.public.apiBase;
    }

    return config.public.apiBase;
  });

  const refreshSession = async () => {
    if (!refreshToken.value || !activeCondominium.value) return false;

    const response = await fetch(`${apiBase.value}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken.value }),
    });

    if (!response.ok) {
      clearSession();
      return false;
    }

    const session = await response.json();
    const selectedCondominium = session.condominiums?.find((item: { id: string }) => item.id === activeCondominium.value?.id) || activeCondominium.value;
    setSession(session, selectedCondominium);
    return true;
  };

  const request = async <T>(path: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    if (token.value) headers.set("Authorization", `Bearer ${token.value}`);
    if (activeCondominium.value?.id) headers.set("X-Condominium", activeCondominium.value.id);

    let response = await fetch(`${apiBase.value}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && refreshToken.value && shouldAttemptRefresh(path)) {
      const refreshed = await refreshSession();
      if (refreshed) {
        headers.set("Authorization", `Bearer ${token.value}`);
        response = await fetch(`${apiBase.value}${path}`, {
          ...options,
          headers,
        });
      }
    }

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }

    return response.json() as Promise<T>;
  };

  return { request };
};

function shouldAttemptRefresh(path: string): boolean {
  return ![
    "/api/v1/auth/login",
    "/api/v1/auth/backoffice-login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
  ].includes(path);
}
