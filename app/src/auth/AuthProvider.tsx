import type { PropsWithChildren } from 'react';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { z } from 'zod';

import { ApiClient } from '@/api/client';
import { tokenResponseSchema, userSchema } from '@/api/schemas';
import { loadConfig } from '@/config';
import { clearRefreshToken, getRefreshToken, setRefreshToken } from './tokenStorage';
import type { SocialProviderName } from './social/types';
import { signInWithProvider } from './social/registry';

type User = z.infer<typeof userSchema>;

type AuthContextValue = {
  user: User | null;
  restoring: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  socialLogin: (provider: SocialProviderName) => Promise<void>;
  linkIdentity: (provider: SocialProviderName) => Promise<void>;
  unlinkIdentity: (provider: SocialProviderName) => Promise<void>;
  changePassword: (currentPassword: string | null, newPassword: string) => Promise<void>;
  deleteAccount: (payload: {
    currentPassword?: string;
    provider?: 'google' | 'facebook';
    providerToken?: string;
  }) => Promise<void>;
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
  const config = loadConfig();

  const clearSession = useCallback(async () => {
    accessSession.set(null);
    setUser(null);
    await clearRefreshToken();
  }, []);

  const api = useMemo(
    () =>
      new ApiClient({
        baseUrl: config.apiUrl,
        getAccessToken: () => accessSession.value,
        setAccessToken: (token) => accessSession.set(token),
        getRefreshToken,
        setRefreshToken,
        clearSession,
      }),
    [clearSession, config.apiUrl],
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

  const socialLogin = useCallback(
    async (providerName: SocialProviderName) => {
      const credentials = await signInWithProvider(providerName);
      const payload =
        credentials.provider === 'google'
          ? await api.request<unknown>(
              '/auth/oauth/google',
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  id_token: credentials.idToken,
                  nonce: credentials.nonce,
                }),
              },
              false,
            )
          : await api.request<unknown>(
              '/auth/oauth/facebook',
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ access_token: credentials.accessToken }),
              },
              false,
            );
      await storeTokens(payload);
    },
    [api, storeTokens],
  );

  const linkIdentity = useCallback(
    async (providerName: SocialProviderName) => {
      const credentials = await signInWithProvider(providerName);
      const body: Record<string, string> =
        credentials.provider === 'google'
          ? {
              id_token: credentials.idToken,
              nonce: credentials.nonce ?? '',
            }
          : { access_token: credentials.accessToken };
      await api.request(`/auth/link/${providerName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
    },
    [api],
  );

  const unlinkIdentity = useCallback(
    async (providerName: SocialProviderName) => {
      await api.request(`/auth/link/${providerName}`, { method: 'DELETE' });
    },
    [api],
  );

  const changePassword = useCallback(
    async (currentPassword: string | null, newPassword: string) => {
      await api.request('/auth/password/change', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
    },
    [api],
  );

  const deleteAccount = useCallback(
    async (payload: {
      currentPassword?: string;
      provider?: 'google' | 'facebook';
      providerToken?: string;
    }) => {
      await api.request('/me', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: payload.currentPassword,
          provider: payload.provider,
          provider_token: payload.providerToken,
        }),
      });
      await clearSession();
    },
    [api, clearSession],
  );

  const value = useMemo(
    () => ({
      user,
      restoring,
      login,
      register,
      logout,
      logoutAll,
      socialLogin,
      linkIdentity,
      unlinkIdentity,
      changePassword,
      deleteAccount,
      api,
    }),
    [
      user,
      restoring,
      login,
      register,
      logout,
      logoutAll,
      socialLogin,
      linkIdentity,
      unlinkIdentity,
      changePassword,
      deleteAccount,
      api,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider');
  return value;
}
