import {
  createContext, useContext, useState, useEffect, useCallback, type ReactNode,
} from "react";
import type { UserMe } from "../api/types";
import { apiGetMe, setToken, clearToken, hasToken } from "../api/client";

interface AuthState {
  user: UserMe | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    if (!hasToken()) { setUser(null); setLoading(false); return; }
    try {
      setUser(await apiGetMe());
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUser(); }, [fetchUser]);

  const login = useCallback(async (token: string) => {
    setToken(token);
    setLoading(true);
    await fetchUser();
  }, [fetchUser]);

  const logout = useCallback(() => { clearToken(); setUser(null); }, []);

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated: !!user, login, logout, refresh: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
