import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';

export default function ResetPasswordScreen() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const { api } = useAuth();
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await api.request(
        '/auth/password/reset',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token, new_password: password }),
        },
        false,
      );
      setMessage('Password reset. You can now sign in.');
      router.replace('/(auth)/login');
    } catch {
      setMessage('The reset link is invalid or expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.page}>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.title}>
          Choose a new password
        </Text>
        <TextInput
          accessibilityLabel="New password"
          onChangeText={setPassword}
          placeholder="New password"
          secureTextEntry
          style={styles.input}
          value={password}
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
            <Text style={styles.buttonText}>Reset password</Text>
          )}
        </Pressable>
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
});
