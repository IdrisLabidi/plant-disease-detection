import * as AuthSession from 'expo-auth-session';
import * as Crypto from 'expo-crypto';
import * as WebBrowser from 'expo-web-browser';

import type { SocialCredentials, SocialProvider } from './types';
import { SocialLoginCancelledError } from './types';

export class GoogleProvider implements SocialProvider {
  async signIn(): Promise<SocialCredentials> {
    const clientId = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID;
    if (!clientId) throw new Error('Google sign-in is not configured');
    const nonce = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      `${Date.now()}-${Math.random()}`,
    );
    const redirectUri =
      typeof window === 'undefined'
        ? AuthSession.makeRedirectUri({ path: 'oauth/callback' })
        : new URL('/oauth/callback', window.location.origin).toString();
    const params = new URLSearchParams({
      client_id: String(clientId),
      redirect_uri: redirectUri,
      response_type: 'id_token',
      response_mode: 'fragment',
      scope: 'openid email profile',
      nonce,
      state: nonce,
    });
    const result = await WebBrowser.openAuthSessionAsync(
      `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`,
      redirectUri,
    );
    if (result.type !== 'success') throw new SocialLoginCancelledError();
    const callback = new URL(result.url);
    const values = new URLSearchParams(
      callback.hash.startsWith('#') ? callback.hash.slice(1) : callback.search.slice(1),
    );
    if (values.get('state') !== nonce) {
      throw new Error('Google OAuth state did not match');
    }
    const idToken = values.get('id_token');
    if (!idToken) throw new Error('Google did not return an ID token');
    return { provider: 'google', idToken, nonce };
  }
}
