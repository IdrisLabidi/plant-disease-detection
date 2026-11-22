import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';

export default function SettingsScreen() {
  const { logout, logoutAll } = useAuth();
  return (
    <View style={styles.page}>
      <Text accessibilityRole="header" style={styles.title}>
        Settings
      </Text>
      <Pressable accessibilityRole="button" onPress={logout} style={styles.button}>
        <Text style={styles.buttonText}>Log out</Text>
      </Pressable>
      <Pressable accessibilityRole="button" onPress={logoutAll} style={styles.button}>
        <Text style={styles.buttonText}>Log out everywhere</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, padding: 20 },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 8 },
  button: {
    minWidth: 220,
    minHeight: 48,
    borderRadius: 8,
    backgroundColor: '#166534',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { color: '#fff', fontWeight: '700' },
});
