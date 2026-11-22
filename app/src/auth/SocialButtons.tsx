import { useState } from 'react';
import { useRouter } from 'expo-router';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from './AuthProvider';

export function SocialButtons() {
  const { socialLogin } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const signIn = async (provider: 'google' | 'facebook') => {
    setLoading(provider);
    setError(null);
    try {
      await socialLogin(provider);
      router.replace('/(tabs)');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Social login failed');
    } finally {
      setLoading(null);
    }
  };

  return (
    <View style={styles.buttons}>
      {error ? (
        <Text accessibilityLiveRegion="polite" style={styles.error}>
          {error}
        </Text>
      ) : null}
      <Pressable
        accessibilityRole="button"
        disabled={loading !== null}
        onPress={() => void signIn('google')}
        style={styles.button}
      >
        {loading === 'google' ? (
          <ActivityIndicator />
        ) : (
          <Text style={styles.label}>Continue with Google</Text>
        )}
      </Pressable>
      <Pressable
        accessibilityRole="button"
        disabled={loading !== null}
        onPress={() => void signIn('facebook')}
        style={styles.button}
      >
        {loading === 'facebook' ? (
          <ActivityIndicator />
        ) : (
          <Text style={styles.label}>Continue with Facebook</Text>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  buttons: { gap: 10 },
  button: {
    minHeight: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#64748b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: { fontWeight: '700' },
  error: { color: '#b91c1c', textAlign: 'center' },
});
