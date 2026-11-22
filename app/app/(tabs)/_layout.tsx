import { Redirect, Tabs } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';

export default function TabsLayout() {
  const { user, restoring } = useAuth();
  if (restoring) return null;
  if (!user) return <Redirect href="/(auth)/login" />;
  return (
    <Tabs>
      <Tabs.Screen name="index" options={{ title: 'Scan' }} />
      <Tabs.Screen name="history" options={{ title: 'History' }} />
      <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
    </Tabs>
  );
}
