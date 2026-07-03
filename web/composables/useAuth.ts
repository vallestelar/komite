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
const ACCESS_TOKEN_MAX_AGE_SECONDS = 1800;
const REFRESH_TOKEN_MAX_AGE_SECONDS = 604800;

export const useAuth = () => {
  const token = useState<string | null>("komite_token", () => null);
  const refreshToken = useState<string | null>("komite_refresh_token", () => null);
  const user = useState<KomiteUser | null>("komite_user", () => null);
  const company = useState<KomiteCompany | null>("komite_company", () => null);
  const condominiums = useState<KomiteCondominium[]>("komite_condominiums", () => []);
  const activeCondominium = useState<KomiteCondominium | null>("komite_active_condominium", () => null);

  const hydrate = () => {
    if (!import.meta.client) return;
    const storedToken = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
    refreshToken.value = localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY);
    if (storedToken && isJwtExpired(storedToken) && !refreshToken.value) {
      clearSession();
      return;
    }

    token.value = storedToken;
    const rawUser = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    const rawCompany = localStorage.getItem(COMPANY_KEY) || sessionStorage.getItem(COMPANY_KEY);
    const rawCondominiums = localStorage.getItem(CONDOMINIUMS_KEY) || sessionStorage.getItem(CONDOMINIUMS_KEY);
    const rawActiveCondominium = localStorage.getItem(ACTIVE_CONDOMINIUM_KEY) || sessionStorage.getItem(ACTIVE_CONDOMINIUM_KEY);
    user.value = rawUser ? safeJsonParse<KomiteUser>(rawUser) : null;
    company.value = rawCompany ? safeJsonParse<KomiteCompany>(rawCompany) : null;
    condominiums.value = rawCondominiums ? safeJsonParse<KomiteCondominium[]>(rawCondominiums) || [] : [];
    activeCondominium.value = rawActiveCondominium ? safeJsonParse<KomiteCondominium>(rawActiveCondominium) : null;
  };

  const setSession = (session: LoginResponse, selectedCondominium: KomiteCondominium) => {
    token.value = session.access_token;
    refreshToken.value = session.refresh_token || refreshToken.value;
    user.value = session.user;
    company.value = session.company || null;
    condominiums.value = session.condominiums || [];
    activeCondominium.value = selectedCondominium;

    if (!import.meta.client) return;
    const userPayload = JSON.stringify(session.user || null);
    const companyPayload = JSON.stringify(session.company || null);
    const condominiumsPayload = JSON.stringify(session.condominiums || []);
    const activeCondominiumPayload = JSON.stringify(selectedCondominium);
    localStorage.setItem(TOKEN_KEY, session.access_token);
    if (refreshToken.value) localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken.value);
    localStorage.setItem(USER_KEY, userPayload);
    localStorage.setItem(COMPANY_KEY, companyPayload);
    localStorage.setItem(CONDOMINIUMS_KEY, condominiumsPayload);
    localStorage.setItem(ACTIVE_CONDOMINIUM_KEY, activeCondominiumPayload);
    sessionStorage.setItem(TOKEN_KEY, session.access_token);
    if (refreshToken.value) sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken.value);
    sessionStorage.setItem(USER_KEY, userPayload);
    sessionStorage.setItem(COMPANY_KEY, companyPayload);
    sessionStorage.setItem(CONDOMINIUMS_KEY, condominiumsPayload);
    sessionStorage.setItem(ACTIVE_CONDOMINIUM_KEY, activeCondominiumPayload);
    document.cookie = `${TOKEN_KEY}=${encodeURIComponent(session.access_token)}; path=/; max-age=${ACCESS_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
    if (refreshToken.value) {
      document.cookie = `${REFRESH_TOKEN_KEY}=${encodeURIComponent(refreshToken.value)}; path=/; max-age=${REFRESH_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
    }
    document.cookie = `${USER_KEY}=${encodeURIComponent(userPayload)}; path=/; max-age=${REFRESH_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
    document.cookie = `${ACTIVE_CONDOMINIUM_KEY}=${encodeURIComponent(activeCondominiumPayload)}; path=/; max-age=${REFRESH_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
  };

  const clearSession = () => {
    token.value = null;
    refreshToken.value = null;
    user.value = null;
    company.value = null;
    condominiums.value = [];
    activeCondominium.value = null;

    if (!import.meta.client) return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(COMPANY_KEY);
    localStorage.removeItem(CONDOMINIUMS_KEY);
    localStorage.removeItem(ACTIVE_CONDOMINIUM_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(COMPANY_KEY);
    sessionStorage.removeItem(CONDOMINIUMS_KEY);
    sessionStorage.removeItem(ACTIVE_CONDOMINIUM_KEY);
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
