import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import type { UserMe } from '../types/api';
import { ApiError } from '../utils/http';

type AuthContextValue = {
  user: UserMe | null;
  bootstrapping: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [bootstrapping, setBootstrapping] = useState(true);

  const refreshMe = async () => {
    try {
      const me = await api.me();
      setUser(me);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setUser(null);
        return;
      }
      throw e;
    }
  };

  useEffect(() => {
    refreshMe().finally(() => setBootstrapping(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      bootstrapping,
      login: async (email, password) => {
        await api.login(email, password);
        await refreshMe();
      },
      register: async (email, password) => {
        await api.register(email, password);
      },
      logout: async () => {
        await api.logout();
        setUser(null);
      },
      refreshMe,
    }),
    [user, bootstrapping],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
