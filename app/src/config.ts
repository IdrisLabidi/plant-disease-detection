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
  const parsed = schema.safeParse({
    apiUrl: process.env.EXPO_PUBLIC_API_URL,
    googleWebClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
    googleAndroidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
    googleIosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
    facebookAppId: process.env.EXPO_PUBLIC_FACEBOOK_APP_ID,
    appScheme: process.env.EXPO_PUBLIC_APP_SCHEME ?? 'plant-disease',
    mock: process.env.EXPO_PUBLIC_MOCK === '1',
  });
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
