import type { z } from 'zod';
import { tokenResponseSchema } from './schemas';

export type TokenResponse = z.infer<typeof tokenResponseSchema>;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

type ApiClientOptions = {
  baseUrl: string;
  getAccessToken: () => string | null;
  setAccessToken: (token: string | null) => void;
  getRefreshToken: () => Promise<string | null>;
  setRefreshToken: (token: string) => Promise<void>;
  clearSession: () => Promise<void>;
};

export class ApiClient {
  private refreshPromise: Promise<TokenResponse> | null = null;

  constructor(private options: ApiClientOptions) {}

  async refresh(): Promise<TokenResponse> {
    if (!this.refreshPromise) {
      this.refreshPromise = this.runRefresh();
    }
    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async runRefresh(): Promise<TokenResponse> {
    const refreshToken = await this.options.getRefreshToken();
    if (!refreshToken) throw new ApiError(401, 'Session expired');
    const response = await fetch(`${this.options.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) {
      await this.options.clearSession();
      throw new ApiError(response.status, 'Session expired');
    }
    const json = await response.json();
    const parsed = tokenResponseSchema.parse(json);
    await this.options.setRefreshToken(parsed.refresh_token);
    this.options.setAccessToken(parsed.access_token);
    return parsed;
  }

  async request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
    const execute = async (retryUnauthorized: boolean): Promise<Response> => {
      const headers = new Headers(init.headers);
      if (!headers.has('Accept')) headers.set('Accept', 'application/json');
      const accessToken = this.options.getAccessToken();
      if (authenticated && accessToken) {
        headers.set('Authorization', `Bearer ${accessToken}`);
      }
      const response = await fetch(`${this.options.baseUrl}${path}`, {
        ...init,
        headers,
      });
      if (response.status === 401 && authenticated && retryUnauthorized) {
        await this.refresh();
        return execute(false);
      }
      return response;
    };

    const response = await execute(true);
    if (!response.ok) {
      let message = 'Request failed';
      try {
        const body = await response.json();
        if (typeof body?.detail === 'string') message = body.detail;
      } catch {}
      throw new ApiError(response.status, message);
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }
}
