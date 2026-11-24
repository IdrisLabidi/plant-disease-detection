import * as AuthSession from 'expo-auth-session';
import * as Crypto from 'expo-crypto';
import * as WebBrowser from 'expo-web-browser';
import { Platform } from 'react-native';

import type { SocialCredentials, SocialProvider } from './types';
import { SocialLoginCancelledError } from './types';

export class FacebookProvider implements SocialProvider {
  async signIn(): Promise<SocialCredentials> {
    const appId = process.env.EXPO_PUBLIC_FACEBOOK_APP_ID;
    if (!appId) throw new Error('Facebook sign-in is not configured');
    const redirectUri =
      Platform.OS === 'web' && typeof window !== 'undefined'
        ? new URL('/oauth/callback', window.location.origin).toString()
        : AuthSession.makeRedirectUri({ path: 'oauth/callback' });
    const state = Crypto.randomUUID();
    const params = new URLSearchParams({
      client_id: String(appId),
      redirect_uri: redirectUri,
      response_type: 'token',
      scope: 'public_profile,email',
      state,
    });
    const result = await WebBrowser.openAuthSessionAsync(
      `https://www.facebook.com/v22.0/dialog/oauth?${params.toString()}`,
      redirectUri,
    );
    if (result.type !== 'success') throw new SocialLoginCancelledError();
    const callback = new URL(result.url);
    const values = new URLSearchParams(
      callback.hash.startsWith('#') ? callback.hash.slice(1) : callback.search.slice(1),
    );
    if (values.get('state') !== state) {
      throw new Error('Facebook OAuth state did not match');
    }
    const accessToken = values.get('access_token');
    if (!accessToken) throw new Error('Facebook did not return an access token');
    return { provider: 'facebook', accessToken };
  }
}

