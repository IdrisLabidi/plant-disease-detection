import { Redirect } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';

export default function Index() {
  const { user, restoring } = useAuth();
  if (restoring) return null;
  return <Redirect href={user ? '/(tabs)' : '/(auth)/login'} />;
}
