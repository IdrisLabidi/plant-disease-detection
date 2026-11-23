import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

export default function OAuthCallbackScreen() {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      WebBrowser.maybeCompleteAuthSession();
    }
  }, []);

  return (
    <View style={styles.page}>
      <ActivityIndicator accessibilityLabel="Completing sign-in" />
      <Text>Completing sign-in...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
});
