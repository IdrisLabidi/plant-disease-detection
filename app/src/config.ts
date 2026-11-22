import Constants from 'expo-constants';
import { z } from 'zod';

const schema = z.object({
  apiUrl: z.string().url(),
  googleWebClientId: z.string().optional(),
  googleAndroidClientId: z.string().optional(),
  googleIosClientId: z.string().optional(),
  facebookAppId: z.string().optional(),
  appScheme: z.string().min(1),
  mock: z.boolean(),
});

export type AppConfig = z.infer<typeof schema>;

export function loadConfig(): AppConfig {
  const extra = Constants.expoConfig?.extra ?? {};
  const parsed = schema.safeParse(extra);
  if (!parsed.success) {
    throw new Error(`Invalid app configuration: ${parsed.error.message}`);
  }
  if (
    !parsed.data.mock &&
    process.env.NODE_ENV === 'production' &&
    !parsed.data.apiUrl.startsWith('https://')
  ) {
    throw new Error('Production builds require an HTTPS EXPO_PUBLIC_API_URL.');
  }
  return parsed.data;
}
