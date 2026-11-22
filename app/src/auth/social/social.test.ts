import { ApiClient } from '@/api/client';
import { signInWithProvider } from './registry';
import { SocialLoginCancelledError } from './types';

jest.mock('react-native-fbsdk-next', () => ({
  AccessToken: { getCurrentAccessToken: jest.fn() },
  LoginManager: { logInWithPermissions: jest.fn() },
}));

jest.mock('react-native-nitro-google-signin', () => ({
  GoogleOneTapSignIn: {
    configure: jest.fn(),
    presentExplicitSignIn: jest.fn(),
  },
  isCancelledResponse: jest.fn(() => false),
  isSuccessResponse: jest.fn(() => true),
}));

describe('fake social providers', () => {
  it('handles Google success', async () => {
    const result = await signInWithProvider('google', {
      google: {
        signIn: async () => ({
          provider: 'google',
          idToken: 'fake-google-id-token',
          nonce: 'fake-nonce',
        }),
      },
    });
    expect(result).toEqual({
      provider: 'google',
      idToken: 'fake-google-id-token',
      nonce: 'fake-nonce',
    });
  });

  it('handles Facebook success', async () => {
    const result = await signInWithProvider('facebook', {
      facebook: {
        signIn: async () => ({
          provider: 'facebook',
          accessToken: 'fake-facebook-access-token',
        }),
      },
    });
    expect(result).toEqual({
      provider: 'facebook',
      accessToken: 'fake-facebook-access-token',
    });
  });

  it('handles cancellation', async () => {
    await expect(
      signInWithProvider('google', {
        google: {
          signIn: async () => {
            throw new SocialLoginCancelledError();
          },
        },
      }),
    ).rejects.toBeInstanceOf(SocialLoginCancelledError);
  });

  it('handles provider errors', async () => {
    await expect(
      signInWithProvider('facebook', {
        facebook: {
          signIn: async () => {
            throw new Error('Provider unavailable');
          },
        },
      }),
    ).rejects.toThrow('Provider unavailable');
  });

  it('preserves the last-method unlink error', async () => {
    global.fetch = jest.fn(
      async () =>
        new Response(JSON.stringify({ detail: 'Cannot remove the last login method' }), {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        }),
    ) as typeof fetch;
    const client = new ApiClient({
      baseUrl: 'https://api.example.com',
      getAccessToken: () => 'access',
      setAccessToken: jest.fn(),
      getRefreshToken: async () => 'refresh',
      setRefreshToken: jest.fn(),
      clearSession: jest.fn(),
    });
    await expect(client.request('/auth/link/google', { method: 'DELETE' })).rejects.toMatchObject({
      status: 409,
      message: 'Cannot remove the last login method',
    });
  });
});
