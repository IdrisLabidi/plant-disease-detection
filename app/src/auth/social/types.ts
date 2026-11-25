export type SocialProviderName = 'google' | 'facebook';

export type SocialCredentials =
  | { provider: 'google'; idToken: string; nonce?: string }
  | { provider: 'facebook'; accessToken: string };

export class SocialLoginCancelledError extends Error {
  constructor() {
    super('Social login cancelled');
  }
}

export interface SocialProvider {
  signIn(): Promise<SocialCredentials>;
}
