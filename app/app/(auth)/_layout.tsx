import { Redirect, Stack } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';

export default function AuthLayout() {
  const { user, restoring } = useAuth();
  if (restoring) return null;
  if (user) return <Redirect href="/(tabs)" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
