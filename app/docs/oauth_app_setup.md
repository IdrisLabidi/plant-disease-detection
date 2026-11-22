# OAuth app setup

## Expo values

- `EXPO_PUBLIC_APP_SCHEME`: custom app scheme, default `plant-disease`.
- `EXPO_PUBLIC_IOS_BUNDLE_ID`: iOS bundle identifier.
- `EXPO_PUBLIC_ANDROID_PACKAGE`: Android application/package name.
- `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`: Google OAuth web client ID.
- `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`: Google OAuth Android client ID.
- `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`: Google OAuth iOS client ID.
- `EXPO_PUBLIC_GOOGLE_IOS_REVERSED_CLIENT_ID`: iOS reversed client ID used by the native
  Google plugin.
- `EXPO_PUBLIC_FACEBOOK_APP_ID`: public Facebook application ID.

Never put a Facebook app secret or backend secret in `EXPO_PUBLIC_*` variables.

## Google

Configure one web OAuth client and, for native builds, Android and iOS clients.

- Add the Expo web redirect origin/redirect URI to the Google web client.
- Android: add the app package and signing certificate SHA-1/SHA-256 fingerprints.
- iOS: add the bundle identifier and put the reversed iOS client ID in
  `EXPO_PUBLIC_GOOGLE_IOS_REVERSED_CLIENT_ID`.
- Set all public client IDs in the app and include all accepted IDs in backend
  `GOOGLE_CLIENT_IDS`.

Native sign-in uses `react-native-nitro-google-signin` and requires a development build.
Web sign-in uses `expo-auth-session`.

## Facebook

- Set `EXPO_PUBLIC_FACEBOOK_APP_ID` to the public app ID used by backend `FACEBOOK_APP_ID`.
- Android: configure the package name and key hashes in Meta's Android settings.
- iOS: configure the bundle identifier and `fb<APP_ID>` URL scheme.
- Web: configure the Expo web redirect origin in Meta's valid OAuth redirect URIs.

Native sign-in uses `react-native-fbsdk-next` and requires a development build.
Web sign-in uses `expo-auth-session`.

## Deep links

The app uses Expo Router routes:

- `/(auth)/reset-password/[token]`
- `/(auth)/verify-email/[token]`

The custom scheme is `plant-disease://` by default. Public universal/app link domains
could not be verified and must be supplied before associating domains.
