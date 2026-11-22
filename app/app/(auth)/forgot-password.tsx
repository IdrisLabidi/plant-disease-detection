import { Link } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';

export default function ForgotPasswordScreen() {
  const { api } = useAuth();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await api.request<{ message: string }>(
        '/auth/password/forgot',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email }),
        },
        false,
      );
      setMessage('If an account exists, reset instructions were sent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.page}>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.title}>
          Reset password
        </Text>
        <TextInput
          accessibilityLabel="Email"
          autoCapitalize="none"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="Email"
          style={styles.input}
          value={email}
        />
        {message ? <Text accessibilityLiveRegion="polite">{message}</Text> : null}
        <Pressable
          accessibilityRole="button"
          disabled={loading}
          onPress={submit}
          style={styles.button}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Send reset link</Text>
          )}
        </Pressable>
        <Link href="/(auth)/login" style={styles.link}>
          Back to sign in
        </Link>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 20 },
  card: { width: '100%', maxWidth: 420, gap: 12 },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: '#64748b',
    borderRadius: 8,
    minHeight: 48,
    paddingHorizontal: 12,
  },
  button: {
    backgroundColor: '#166534',
    minHeight: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { color: '#fff', fontWeight: '700' },
  link: { minHeight: 44, textAlign: 'center', paddingVertical: 12, color: '#1d4ed8' },
});
