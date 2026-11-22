import Constants from 'expo-constants';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';

import type { SocialCredentials, SocialProvider } from './types';
import { SocialLoginCancelledError } from './types';

export class FacebookProvider implements SocialProvider {
  async signIn(): Promise<SocialCredentials> {
    const appId = Constants.expoConfig?.extra?.facebookAppId;
    if (!appId) throw new Error('Facebook sign-in is not configured');
    const redirectUri = AuthSession.makeRedirectUri({ preferLocalhost: true });
    const state = crypto.randomUUID();
    const params = new URLSearchParams({
      client_id: String(appId),
      redirect_uri: redirectUri,
      response_type: 'token',
      scope: 'public_profile,email',
      state,
    });
    WebBrowser.maybeCompleteAuthSession();
    const result = await WebBrowser.openAuthSessionAsync(
      `https://www.facebook.com/v22.0/dialog/oauth?${params.toString()}`,
      redirectUri,
    );
    if (result.type !== 'success') throw new SocialLoginCancelledError();
    const fragment = new URL(result.url).hash.slice(1);
    const values = new URLSearchParams(fragment);
    const accessToken = values.get('access_token');
    if (!accessToken) throw new Error('Facebook did not return an access token');
    return { provider: 'facebook', accessToken };
  }
}
