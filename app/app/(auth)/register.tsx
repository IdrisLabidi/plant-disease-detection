import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { ApiError } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';

export default function RegisterScreen() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      await register(email.trim(), password, displayName || undefined);
      router.replace('/(tabs)');
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Unable to create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.page}>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.title}>
          Create account
        </Text>
        <TextInput
          accessibilityLabel="Display name"
          onChangeText={setDisplayName}
          placeholder="Display name"
          style={styles.input}
          value={displayName}
        />
        <TextInput
          accessibilityLabel="Email"
          autoCapitalize="none"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="Email"
          style={styles.input}
          value={email}
        />
        <TextInput
          accessibilityLabel="Password"
          onChangeText={setPassword}
          placeholder="Password (10+ characters)"
          secureTextEntry
          style={styles.input}
          value={password}
        />
        {error ? (
          <Text accessibilityLiveRegion="polite" style={styles.error}>
            {error}
          </Text>
        ) : null}
        <Pressable
          accessibilityRole="button"
          disabled={loading}
          onPress={submit}
          style={styles.button}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Create account</Text>
          )}
        </Pressable>
        <Link href="/(auth)/login" style={styles.link}>
          Already have an account?
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
  error: { color: '#b91c1c' },
});
