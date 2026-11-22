import Constants from 'expo-constants';
import * as AuthSession from 'expo-auth-session';
import * as Crypto from 'expo-crypto';
import * as WebBrowser from 'expo-web-browser';

import type { SocialCredentials, SocialProvider } from './types';
import { SocialLoginCancelledError } from './types';

export class GoogleProvider implements SocialProvider {
  async signIn(): Promise<SocialCredentials> {
    const clientId = Constants.expoConfig?.extra?.googleWebClientId;
    if (!clientId) throw new Error('Google sign-in is not configured');
    const nonce = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      `${Date.now()}-${Math.random()}`,
    );
    const redirectUri = AuthSession.makeRedirectUri({ preferLocalhost: true });
    const params = new URLSearchParams({
      client_id: String(clientId),
      redirect_uri: redirectUri,
      response_type: 'id_token',
      scope: 'openid email profile',
      nonce,
      state: nonce,
    });
    WebBrowser.maybeCompleteAuthSession();
    const result = await WebBrowser.openAuthSessionAsync(
      `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`,
      redirectUri,
    );
    if (result.type !== 'success') throw new SocialLoginCancelledError();
    const fragment = new URL(result.url).hash.slice(1);
    const values = new URLSearchParams(fragment);
    const idToken = values.get('id_token');
    if (!idToken) throw new Error('Google did not return an ID token');
    return { provider: 'google', idToken, nonce };
  }
}
