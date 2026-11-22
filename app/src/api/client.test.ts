import { ApiClient } from './client';

describe('ApiClient refresh single-flight', () => {
  it('reports an HTML API response as a configuration error', async () => {
    global.fetch = jest.fn(
      async () =>
        new Response('<!doctype html><title>Expo</title>', {
          status: 200,
          headers: { 'Content-Type': 'text/html' },
        }),
    ) as typeof fetch;

    const client = new ApiClient({
      baseUrl: 'https://api.example.com',
      getAccessToken: () => null,
      setAccessToken: jest.fn(),
      getRefreshToken: async () => null,
      setRefreshToken: jest.fn(),
      clearSession: jest.fn(),
    });

    await expect(client.request('/auth/login', { method: 'POST' }, false)).rejects.toThrow(
      'EXPO_PUBLIC_API_URL',
    );
  });

  it('runs only one refresh for concurrent calls', async () => {
    let refreshToken = 'old-refresh-token-123456789';
    let accessToken: string | null = 'old-access';
    let fetchCalls = 0;
    const clearSession = jest.fn(async () => {
      refreshToken = '';
      accessToken = null;
    });

    global.fetch = jest.fn(async (input) => {
      const url = String(input);
      fetchCalls += 1;
      if (url.endsWith('/auth/refresh')) {
        return new Response(
          JSON.stringify({
            access_token: 'new-access',
            refresh_token: 'new-refresh-token-123456789',
            expires_in: 900,
            user: {
              id: '00000000-0000-0000-0000-000000000001',
              email: 'user@example.com',
              email_verified: true,
              display_name: 'User',
              created_at: '2026-01-01T00:00:00Z',
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
      }
      return new Response('{}', { status: 200 });
    }) as typeof fetch;

    const client = new ApiClient({
      baseUrl: 'https://api.example.com',
      getAccessToken: () => accessToken,
      setAccessToken: (token) => {
        accessToken = token;
      },
      getRefreshToken: async () => refreshToken,
      setRefreshToken: async (token) => {
        refreshToken = token;
      },
      clearSession,
    });

    const [first, second] = await Promise.all([client.refresh(), client.refresh()]);

    expect(first.access_token).toBe('new-access');
    expect(second.access_token).toBe('new-access');
    expect(fetchCalls).toBe(1);
  });

  it('clears the session when refresh fails', async () => {
    const clearSession = jest.fn(async () => {});
    global.fetch = jest.fn(
      async () =>
        new Response(JSON.stringify({ detail: 'Invalid refresh token' }), { status: 401 }),
    ) as typeof fetch;

    const client = new ApiClient({
      baseUrl: 'https://api.example.com',
      getAccessToken: () => 'access',
      setAccessToken: jest.fn(),
      getRefreshToken: async () => 'old-refresh-token-123456789',
      setRefreshToken: jest.fn(),
      clearSession,
    });

    await expect(client.refresh()).rejects.toMatchObject({ status: 401 });
    expect(clearSession).toHaveBeenCalledTimes(1);
  });
});
