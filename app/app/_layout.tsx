import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import * as WebBrowser from 'expo-web-browser';

import { AuthProvider } from '@/auth/AuthProvider';

if (typeof window !== 'undefined') {
  WebBrowser.maybeCompleteAuthSession();
}

export default function RootLayout() {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="auto" />
        <Stack screenOptions={{ headerShown: false }} />
      </QueryClientProvider>
    </AuthProvider>
  );
}
