type KomiteUser = {
  id?: string;
  email?: string;
  full_name?: string;
  global_role?: string;
};

type LoginResponse = {
  access_token: string;
  user: KomiteUser;
};

const TOKEN_KEY = "komite_token";
const USER_KEY = "komite_user";

export const useAuth = () => {
  const token = useState<string | null>("komite_token", () => null);
  const user = useState<KomiteUser | null>("komite_user", () => null);

  const hydrate = () => {
    if (!import.meta.client) return;
    token.value = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
    const rawUser = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    user.value = rawUser ? safeJsonParse<KomiteUser>(rawUser) : null;
  };

  const setSession = (session: LoginResponse) => {
    token.value = session.access_token;
    user.value = session.user;

    if (!import.meta.client) return;
    const userPayload = JSON.stringify(session.user || null);
    localStorage.setItem(TOKEN_KEY, session.access_token);
    localStorage.setItem(USER_KEY, userPayload);
    sessionStorage.setItem(TOKEN_KEY, session.access_token);
    sessionStorage.setItem(USER_KEY, userPayload);
    document.cookie = `${TOKEN_KEY}=${encodeURIComponent(session.access_token)}; path=/; max-age=28800; SameSite=Lax`;
    document.cookie = `${USER_KEY}=${encodeURIComponent(userPayload)}; path=/; max-age=28800; SameSite=Lax`;
  };

  const clearSession = () => {
    token.value = null;
    user.value = null;

    if (!import.meta.client) return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
    document.cookie = `${USER_KEY}=; path=/; max-age=0; SameSite=Lax`;
  };

  return {
    token,
    user,
    isAuthenticated: computed(() => Boolean(token.value)),
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
