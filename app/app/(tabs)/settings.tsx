import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { FacebookProvider } from '@/auth/social/facebook';
import { GoogleProvider } from '@/auth/social/google';

type Identity = { provider: string; email_at_link: string };

export default function SettingsScreen() {
  const { api, logout, logoutAll, linkIdentity, unlinkIdentity, changePassword, deleteAccount } =
    useAuth();
  const [identities, setIdentities] = useState<Identity[]>([]);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const loadIdentities = useCallback(async () => {
    const result = await api.request<Identity[]>('/me/identities');
    setIdentities(result);
  }, [api]);

  useEffect(() => {
    void Promise.resolve().then(loadIdentities);
  }, [loadIdentities]);

  const link = async (provider: 'google' | 'facebook') => {
    setMessage(null);
    try {
      await linkIdentity(provider);
      await loadIdentities();
      setMessage(`${provider} linked`);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : 'Unable to link account');
    }
  };

  const unlink = async (provider: 'google' | 'facebook') => {
    setMessage(null);
    try {
      await unlinkIdentity(provider);
      await loadIdentities();
      setMessage(`${provider} unlinked`);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : 'Unable to unlink account');
    }
  };

  const setPassword = async () => {
    setMessage(null);
    try {
      await changePassword(currentPassword || null, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setMessage('Password changed');
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : 'Unable to change password');
    }
  };

  const removeAccount = async (provider?: 'google' | 'facebook') => {
    setMessage(null);
    try {
      if (provider) {
        const credentials =
          provider === 'google'
            ? await new GoogleProvider().signIn()
            : await new FacebookProvider().signIn();
        const token =
          credentials.provider === 'google' ? credentials.idToken : credentials.accessToken;
        await deleteAccount({ provider, providerToken: token });
      } else {
        await deleteAccount({ currentPassword });
      }
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : 'Unable to delete account');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text accessibilityRole="header" style={styles.title}>
        Settings
      </Text>
      <Text accessibilityRole="header" style={styles.heading}>
        Linked accounts
      </Text>
      {identities.map((identity) => (
        <Pressable
          accessibilityRole="button"
          key={identity.provider}
          onPress={() => void unlink(identity.provider as 'google' | 'facebook')}
          style={styles.button}
        >
          <Text style={styles.buttonText}>Unlink {identity.provider}</Text>
        </Pressable>
      ))}
      {['google', 'facebook'].map((provider) =>
        identities.some((identity) => identity.provider === provider) ? null : (
          <Pressable
            accessibilityRole="button"
            key={provider}
            onPress={() => void link(provider as 'google' | 'facebook')}
            style={styles.button}
          >
            <Text style={styles.buttonText}>Link {provider}</Text>
          </Pressable>
        ),
      )}
      <Text accessibilityRole="header" style={styles.heading}>
        Password
      </Text>
      <TextInput
        accessibilityLabel="Current password"
        onChangeText={setCurrentPassword}
        placeholder="Current password"
        secureTextEntry
        style={styles.input}
        value={currentPassword}
      />
      <TextInput
        accessibilityLabel="New password"
        onChangeText={setNewPassword}
        placeholder="New password"
        secureTextEntry
        style={styles.input}
        value={newPassword}
      />
      <Pressable
        accessibilityRole="button"
        onPress={() => void setPassword()}
        style={styles.button}
      >
        <Text style={styles.buttonText}>Change password</Text>
      </Pressable>
      {message ? <Text accessibilityLiveRegion="polite">{message}</Text> : null}
      <Text accessibilityRole="header" style={styles.heading}>
        Delete account
      </Text>
      <Pressable
        accessibilityRole="button"
        onPress={() => void removeAccount()}
        style={styles.danger}
      >
        <Text style={styles.buttonText}>Delete with password</Text>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        onPress={() => void removeAccount('google')}
        style={styles.danger}
      >
        <Text style={styles.buttonText}>Delete after Google re-authentication</Text>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        onPress={() => void removeAccount('facebook')}
        style={styles.danger}
      >
        <Text style={styles.buttonText}>Delete after Facebook re-authentication</Text>
      </Pressable>
      <Pressable accessibilityRole="button" onPress={logout} style={styles.button}>
        <Text style={styles.buttonText}>Log out</Text>
      </Pressable>
      <Pressable accessibilityRole="button" onPress={logoutAll} style={styles.button}>
        <Text style={styles.buttonText}>Log out everywhere</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { alignItems: 'center', gap: 12, padding: 20, maxWidth: 520, alignSelf: 'center' },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 8 },
  heading: { fontSize: 18, fontWeight: '700', marginTop: 12 },
  input: {
    width: '100%',
    borderWidth: 1,
    borderColor: '#64748b',
    borderRadius: 8,
    minHeight: 48,
    paddingHorizontal: 12,
  },
  button: {
    minWidth: 220,
    minHeight: 48,
    borderRadius: 8,
    backgroundColor: '#166534',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { color: '#fff', fontWeight: '700' },
  danger: {
    minWidth: 220,
    minHeight: 48,
    borderRadius: 8,
    backgroundColor: '#b91c1c',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
