import Constants from 'expo-constants';
import type { PropsWithChildren } from 'react';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { z } from 'zod';

import { ApiClient } from '@/api/client';
import { tokenResponseSchema, userSchema } from '@/api/schemas';
import { clearRefreshToken, getRefreshToken, setRefreshToken } from './tokenStorage';

type User = z.infer<typeof userSchema>;

type AuthContextValue = {
  user: User | null;
  restoring: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  api: ApiClient;
};

const AuthContext = createContext<AuthContextValue | null>(null);
class AccessSession {
  value: string | null = null;

  set(token: string | null) {
    this.value = token;
  }
}
const accessSession = new AccessSession();

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [restoring, setRestoring] = useState(true);

  const clearSession = useCallback(async () => {
    accessSession.set(null);
    setUser(null);
    await clearRefreshToken();
  }, []);

  const api = useMemo(
    () =>
      new ApiClient({
        baseUrl: String(Constants.expoConfig?.extra?.apiUrl ?? ''),
        getAccessToken: () => accessSession.value,
        setAccessToken: (token) => accessSession.set(token),
        getRefreshToken,
        setRefreshToken,
        clearSession,
      }),
    [clearSession],
  );

  useEffect(() => {
    void (async () => {
      try {
        await api.refresh();
        const me = await api.request<unknown>('/me');
        setUser(userSchema.parse(me));
      } catch {
        await clearSession();
      } finally {
        setRestoring(false);
      }
    })();
  }, [api, clearSession]);

  const storeTokens = useCallback(async (payload: unknown) => {
    const parsed = tokenResponseSchema.parse(payload);
    accessSession.set(parsed.access_token);
    await setRefreshToken(parsed.refresh_token);
    setUser(parsed.user);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const payload = await api.request<unknown>(
        '/auth/login',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        },
        false,
      );
      await storeTokens(payload);
    },
    [api, storeTokens],
  );

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const payload = await api.request<unknown>(
        '/auth/register',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, display_name: displayName }),
        },
        false,
      );
      await storeTokens(payload);
    },
    [api, storeTokens],
  );

  const logout = useCallback(async () => {
    try {
      const refreshToken = await getRefreshToken();
      if (refreshToken) {
        await api.request(
          '/auth/logout',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          },
          false,
        );
      }
    } finally {
      await clearSession();
    }
  }, [api, clearSession]);

  const logoutAll = useCallback(async () => {
    try {
      await api.request('/auth/logout-all', { method: 'POST' });
    } finally {
      await clearSession();
    }
  }, [api, clearSession]);

  const value = useMemo(
    () => ({ user, restoring, login, register, logout, logoutAll, api }),
    [user, restoring, login, register, logout, logoutAll, api],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider');
  return value;
}
