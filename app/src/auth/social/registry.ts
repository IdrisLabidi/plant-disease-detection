import { FacebookProvider } from './facebook';
import { GoogleProvider } from './google';
import type { SocialCredentials, SocialProvider, SocialProviderName } from './types';

export function createSocialProvider(name: SocialProviderName): SocialProvider {
  return name === 'google' ? new GoogleProvider() : new FacebookProvider();
}

export async function signInWithProvider(
  name: SocialProviderName,
  providers?: Partial<Record<SocialProviderName, SocialProvider>>,
): Promise<SocialCredentials> {
  const provider = providers?.[name] ?? createSocialProvider(name);
  return provider.signIn();
}
