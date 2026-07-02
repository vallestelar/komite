type KomiteUser = {
  id?: string;
  email?: string;
  full_name?: string;
  global_role?: string;
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
  user: KomiteUser;
  company?: KomiteCompany | null;
  condominiums?: KomiteCondominium[];
};

const TOKEN_KEY = "komite_token";
const USER_KEY = "komite_user";
const COMPANY_KEY = "komite_company";
const CONDOMINIUMS_KEY = "komite_condominiums";
const ACTIVE_CONDOMINIUM_KEY = "komite_active_condominium";

export const useAuth = () => {
  const token = useState<string | null>("komite_token", () => null);
  const user = useState<KomiteUser | null>("komite_user", () => null);
  const company = useState<KomiteCompany | null>("komite_company", () => null);
  const condominiums = useState<KomiteCondominium[]>("komite_condominiums", () => []);
  const activeCondominium = useState<KomiteCondominium | null>("komite_active_condominium", () => null);

  const hydrate = () => {
    if (!import.meta.client) return;
    token.value = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
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
    localStorage.setItem(USER_KEY, userPayload);
    localStorage.setItem(COMPANY_KEY, companyPayload);
    localStorage.setItem(CONDOMINIUMS_KEY, condominiumsPayload);
    localStorage.setItem(ACTIVE_CONDOMINIUM_KEY, activeCondominiumPayload);
    sessionStorage.setItem(TOKEN_KEY, session.access_token);
    sessionStorage.setItem(USER_KEY, userPayload);
    sessionStorage.setItem(COMPANY_KEY, companyPayload);
    sessionStorage.setItem(CONDOMINIUMS_KEY, condominiumsPayload);
    sessionStorage.setItem(ACTIVE_CONDOMINIUM_KEY, activeCondominiumPayload);
    document.cookie = `${TOKEN_KEY}=${encodeURIComponent(session.access_token)}; path=/; max-age=28800; SameSite=Lax`;
    document.cookie = `${USER_KEY}=${encodeURIComponent(userPayload)}; path=/; max-age=28800; SameSite=Lax`;
    document.cookie = `${ACTIVE_CONDOMINIUM_KEY}=${encodeURIComponent(activeCondominiumPayload)}; path=/; max-age=28800; SameSite=Lax`;
  };

  const clearSession = () => {
    token.value = null;
    user.value = null;
    company.value = null;
    condominiums.value = [];
    activeCondominium.value = null;

    if (!import.meta.client) return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(COMPANY_KEY);
    localStorage.removeItem(CONDOMINIUMS_KEY);
    localStorage.removeItem(ACTIVE_CONDOMINIUM_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(COMPANY_KEY);
    sessionStorage.removeItem(CONDOMINIUMS_KEY);
    sessionStorage.removeItem(ACTIVE_CONDOMINIUM_KEY);
    document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
    document.cookie = `${USER_KEY}=; path=/; max-age=0; SameSite=Lax`;
    document.cookie = `${ACTIVE_CONDOMINIUM_KEY}=; path=/; max-age=0; SameSite=Lax`;
  };

  return {
    token,
    user,
    company,
    condominiums,
    activeCondominium,
    isAuthenticated: computed(() => Boolean(token.value && activeCondominium.value)),
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
