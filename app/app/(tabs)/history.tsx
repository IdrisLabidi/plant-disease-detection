import { Text, View } from 'react-native';

export default function HistoryScreen() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <Text accessibilityRole="header" style={{ fontSize: 24, fontWeight: '700' }}>
        History
      </Text>
      <Text>History implementation continues in Phase 3.</Text>
    </View>
  );
}
