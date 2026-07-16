type KomiteUser = {
  id?: string;
  email?: string;
  full_name?: string;
  company_profile?: string;
};

export type KomiteCompany = {
  id: string;
  name: string;
};

export type KomiteCondominium = {
  id: string;
  name: string;
  role: string;
  role_name: string;
  unit_id?: string | null;
  unit_identifier?: string | null;
};

type LoginResponse = {
  access_token: string;
  refresh_token?: string | null;
  user: KomiteUser;
  company?: KomiteCompany | null;
  condominiums?: KomiteCondominium[];
};

const TOKEN_KEY = "komite_token";
const REFRESH_TOKEN_KEY = "komite_refresh_token";
const USER_KEY = "komite_user";
const COMPANY_KEY = "komite_company";
const CONDOMINIUMS_KEY = "komite_condominiums";
const ACTIVE_CONDOMINIUM_KEY = "komite_active_condominium";
const SESSION_KEYS = [TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY, COMPANY_KEY, CONDOMINIUMS_KEY, ACTIVE_CONDOMINIUM_KEY];

export const useAuth = () => {
  const token = useState<string | null>("komite_token", () => null);
  const refreshToken = useState<string | null>("komite_refresh_token", () => null);
  const user = useState<KomiteUser | null>("komite_user", () => null);
  const company = useState<KomiteCompany | null>("komite_company", () => null);
  const condominiums = useState<KomiteCondominium[]>("komite_condominiums", () => []);
  const activeCondominium = useState<KomiteCondominium | null>("komite_active_condominium", () => null);

  const hydrate = () => {
    if (!import.meta.client) return;
    clearPersistentAuthStorage();
    const storedToken = sessionStorage.getItem(TOKEN_KEY);
    refreshToken.value = sessionStorage.getItem(REFRESH_TOKEN_KEY);
    if (storedToken && isJwtExpired(storedToken) && !refreshToken.value) {
      clearSession();
      return;
    }

    token.value = storedToken;
    const rawUser = sessionStorage.getItem(USER_KEY);
    const rawCompany = sessionStorage.getItem(COMPANY_KEY);
    const rawCondominiums = sessionStorage.getItem(CONDOMINIUMS_KEY);
    const rawActiveCondominium = sessionStorage.getItem(ACTIVE_CONDOMINIUM_KEY);
    user.value = rawUser ? safeJsonParse<KomiteUser>(rawUser) : null;
    company.value = rawCompany ? safeJsonParse<KomiteCompany>(rawCompany) : null;
    condominiums.value = uniqueCondominiumsById(rawCondominiums ? safeJsonParse<KomiteCondominium[]>(rawCondominiums) || [] : []);
    activeCondominium.value = rawActiveCondominium ? safeJsonParse<KomiteCondominium>(rawActiveCondominium) : null;
    if (activeCondominium.value && !condominiums.value.some((condominium) => condominium.id === activeCondominium.value?.id)) {
      activeCondominium.value = condominiums.value[0] || null;
    }
  };

  const setSession = (session: LoginResponse, selectedCondominium: KomiteCondominium) => {
    token.value = session.access_token;
    refreshToken.value = session.refresh_token || refreshToken.value;
    user.value = session.user;
    company.value = session.company || null;
    const uniqueCondominiums = uniqueCondominiumsById(session.condominiums || []);
    condominiums.value = uniqueCondominiums;
    activeCondominium.value = uniqueCondominiums.find((condominium) => condominium.id === selectedCondominium.id) || selectedCondominium;

    if (!import.meta.client) return;
    const userPayload = JSON.stringify(session.user || null);
    const companyPayload = JSON.stringify(session.company || null);
    const condominiumsPayload = JSON.stringify(uniqueCondominiums);
    const activeCondominiumPayload = JSON.stringify(activeCondominium.value);
    clearPersistentAuthStorage();
    sessionStorage.setItem(TOKEN_KEY, session.access_token);
    if (refreshToken.value) sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken.value);
    sessionStorage.setItem(USER_KEY, userPayload);
    sessionStorage.setItem(COMPANY_KEY, companyPayload);
    sessionStorage.setItem(CONDOMINIUMS_KEY, condominiumsPayload);
    sessionStorage.setItem(ACTIVE_CONDOMINIUM_KEY, activeCondominiumPayload);
    document.cookie = `${TOKEN_KEY}=${encodeURIComponent(session.access_token)}; path=/; SameSite=Lax`;
    if (refreshToken.value) {
      document.cookie = `${REFRESH_TOKEN_KEY}=${encodeURIComponent(refreshToken.value)}; path=/; SameSite=Lax`;
    }
    document.cookie = `${USER_KEY}=${encodeURIComponent(userPayload)}; path=/; SameSite=Lax`;
    document.cookie = `${ACTIVE_CONDOMINIUM_KEY}=${encodeURIComponent(activeCondominiumPayload)}; path=/; SameSite=Lax`;
  };

  const setActiveCondominium = (selectedCondominium: KomiteCondominium) => {
    activeCondominium.value = selectedCondominium;

    if (!import.meta.client) return;
    const activeCondominiumPayload = JSON.stringify(selectedCondominium);
    clearPersistentAuthStorage();
    sessionStorage.setItem(ACTIVE_CONDOMINIUM_KEY, activeCondominiumPayload);
    document.cookie = `${ACTIVE_CONDOMINIUM_KEY}=${encodeURIComponent(activeCondominiumPayload)}; path=/; SameSite=Lax`;
  };

  const clearSession = () => {
    token.value = null;
    refreshToken.value = null;
    user.value = null;
    company.value = null;
    condominiums.value = [];
    activeCondominium.value = null;

    if (!import.meta.client) return;
    clearPersistentAuthStorage();
    for (const key of SESSION_KEYS) {
      sessionStorage.removeItem(key);
    }
    document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
    document.cookie = `${REFRESH_TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
    document.cookie = `${USER_KEY}=; path=/; max-age=0; SameSite=Lax`;
    document.cookie = `${ACTIVE_CONDOMINIUM_KEY}=; path=/; max-age=0; SameSite=Lax`;
  };

  return {
    token,
    refreshToken,
    user,
    company,
    condominiums,
    activeCondominium,
    isAuthenticated: computed(() => Boolean((token.value || refreshToken.value) && activeCondominium.value)),
    hydrate,
    setSession,
    setActiveCondominium,
    clearSession,
  };
};

function safeJsonParse<T>(value: string): T | null {
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

function isJwtExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(base64UrlToBase64(token.split(".")[1] || ""))) as { exp?: number };
    return typeof payload.exp === "number" && payload.exp <= Math.floor(Date.now() / 1000);
  } catch {
    return true;
  }
}

function base64UrlToBase64(value: string): string {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  return base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
}

function clearPersistentAuthStorage() {
  for (const key of SESSION_KEYS) {
    localStorage.removeItem(key);
  }
}

function uniqueCondominiumsById(items: KomiteCondominium[]): KomiteCondominium[] {
  const byId = new Map<string, KomiteCondominium>();
  for (const item of items) {
    if (!item?.id || byId.has(item.id)) continue;
    byId.set(item.id, item);
  }
  return [...byId.values()];
}
