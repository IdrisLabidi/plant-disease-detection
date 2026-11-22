import * as Crypto from 'expo-crypto';
import {
  GoogleOneTapSignIn,
  isCancelledResponse,
  isSuccessResponse,
} from 'react-native-nitro-google-signin';
import { Platform } from 'react-native';

import type { SocialCredentials, SocialProvider } from './types';
import { SocialLoginCancelledError } from './types';

export class GoogleProvider implements SocialProvider {
  async signIn(): Promise<SocialCredentials> {
    const extra = {
      googleIosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
      googleAndroidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
    };
    const webClientId =
      Platform.OS === 'ios' ? extra?.googleIosClientId : extra?.googleAndroidClientId;
    if (!webClientId) throw new Error('Google sign-in is not configured');

    const nonce = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      `${Date.now()}-${Math.random()}`,
    );
    GoogleOneTapSignIn.configure({
      webClientId,
      iosClientId: extra?.googleIosClientId ?? null,
      nonce,
    });
    const result = await GoogleOneTapSignIn.presentExplicitSignIn();
    if (isCancelledResponse(result) || !isSuccessResponse(result) || !result.data) {
      throw new SocialLoginCancelledError();
    }
    return { provider: 'google', idToken: result.data.idToken, nonce };
  }
}
