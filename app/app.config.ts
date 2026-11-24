import type { ConfigContext, ExpoConfig } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => {
  const plugins: ExpoConfig['plugins'] = [
    'expo-router',
    'expo-web-browser',
    'expo-secure-store',
    'expo-sqlite',
  ];

  return {
    ...config,
    name: 'Plant Disease',
    slug: 'plant-disease',
    scheme: process.env.EXPO_PUBLIC_APP_SCHEME ?? 'plant-disease',
    extra: {
      apiUrl: process.env.EXPO_PUBLIC_API_URL,
      googleWebClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
      googleAndroidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
      googleIosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
      facebookAppId: process.env.EXPO_PUBLIC_FACEBOOK_APP_ID,
      appScheme: process.env.EXPO_PUBLIC_APP_SCHEME ?? 'plant-disease',
      mock: process.env.EXPO_PUBLIC_MOCK === '1',
    },
    ios: {
      ...config.ios,
      supportsTablet: true,
      bundleIdentifier: process.env.EXPO_PUBLIC_IOS_BUNDLE_ID,
    },
    android: {
      ...config.android,
      package: process.env.EXPO_PUBLIC_ANDROID_PACKAGE,
    },
    plugins,
  };
};
