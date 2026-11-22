import { AccessToken, LoginManager } from 'react-native-fbsdk-next';

import type { SocialCredentials, SocialProvider } from './types';
import { SocialLoginCancelledError } from './types';

export class FacebookProvider implements SocialProvider {
  async signIn(): Promise<SocialCredentials> {
    const result = await LoginManager.logInWithPermissions(['public_profile', 'email']);
    if (result.isCancelled) throw new SocialLoginCancelledError();
    const token = await AccessToken.getCurrentAccessToken();
    if (!token?.accessToken) throw new Error('Facebook did not return an access token');
    return { provider: 'facebook', accessToken: token.accessToken };
  }
}
