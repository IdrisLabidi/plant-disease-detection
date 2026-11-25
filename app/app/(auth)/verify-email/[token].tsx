import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';

export default function VerifyEmailScreen() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const { api } = useAuth();
  const router = useRouter();
  const [message, setMessage] = useState('Verifying...');

  useEffect(() => {
    void api
      .request(
        '/auth/email/verify',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        },
        false,
      )
      .then(() => setMessage('Email verified.'))
      .catch(() => setMessage('The verification link is invalid or expired.'));
  }, [api, token]);

  return (
    <View style={styles.page}>
      {message === 'Verifying...' ? <ActivityIndicator /> : null}
      <Text accessibilityLiveRegion="polite" style={styles.message}>
        {message}
      </Text>
      <Pressable
        accessibilityRole="button"
        onPress={() => router.replace('/(auth)/login')}
        style={styles.button}
      >
        <Text style={styles.buttonText}>Continue</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, padding: 20 },
  message: { fontSize: 18, textAlign: 'center' },
  button: {
    backgroundColor: '#166534',
    minHeight: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  buttonText: { color: '#fff', fontWeight: '700' },
});
