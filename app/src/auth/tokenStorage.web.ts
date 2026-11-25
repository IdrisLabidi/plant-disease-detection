const REFRESH_KEY = 'refresh_token';

export async function getRefreshToken(): Promise<string | null> {
  return globalThis.localStorage?.getItem(REFRESH_KEY) ?? null;
}

export async function setRefreshToken(token: string): Promise<void> {
  globalThis.localStorage?.setItem(REFRESH_KEY, token);
}

export async function clearRefreshToken(): Promise<void> {
  globalThis.localStorage?.removeItem(REFRESH_KEY);
}
