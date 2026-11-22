import { useLocalSearchParams, useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { getAdvice } from '@/content/advice';
import type { ScanResult } from '@/inference/types';

export default function ScanResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string; imageUri?: string; result?: string }>();
  const [showMask, setShowMask] = useState(true);
  const result = useMemo<ScanResult | null>(() => {
    if (!params.result) return null;
    try {
      return JSON.parse(params.result) as ScanResult;
    } catch {
      return null;
    }
  }, [params.result]);

  if (!result) {
    return (
      <View style={styles.page}>
        <Text accessibilityRole="header" style={styles.title}>
          Result unavailable
        </Text>
        <Pressable accessibilityRole="button" onPress={() => router.back()} style={styles.button}>
          <Text>Go back</Text>
        </Pressable>
      </View>
    );
  }

  const advice = getAdvice(result.top3[0]?.className ?? '');
  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.title}>
          Scan result
        </Text>
        {params.imageUri ? (
          <View style={styles.imageWrap}>
            <Image
              accessibilityLabel="Analyzed plant image"
              source={{ uri: params.imageUri }}
              style={styles.image}
            />
            {result.maskUri && showMask ? (
              <Image
                accessibilityLabel="Lesion mask overlay"
                source={{ uri: result.maskUri }}
                style={styles.maskOverlay}
              />
            ) : null}
          </View>
        ) : null}
        {result.unsure ? (
          <View style={styles.unsure}>
            <Text style={styles.unsureTitle}>Not sure, please retake the photo</Text>
            <Text>Use better light and frame one clear leaf.</Text>
          </View>
        ) : null}
        {result.top3.map((item, index) => (
          <View key={item.className} style={styles.prediction}>
            <View style={styles.predictionLabel}>
              <Text style={styles.predictionName}>
                {index + 1}. {item.className}
              </Text>
              <Text>{Math.round(item.probability * 100)}%</Text>
            </View>
            <View style={styles.bar}>
              <View style={[styles.barFill, { width: `${Math.round(item.probability * 100)}%` }]} />
            </View>
          </View>
        ))}
        {result.lesionAreaFrac !== null ? (
          <Text>Estimated lesion area: {Math.round(result.lesionAreaFrac * 100)}%</Text>
        ) : null}
        {result.maskUri ? (
          <Pressable
            accessibilityRole="button"
            onPress={() => setShowMask((value) => !value)}
            style={styles.button}
          >
            <Text>{showMask ? 'Hide mask overlay' : 'Show mask overlay'}</Text>
          </Pressable>
        ) : null}
        <View style={styles.advice}>
          <Text accessibilityRole="header" style={styles.adviceTitle}>
            Advice
          </Text>
          {advice.status === 'placeholder' ? (
            <Text>Neutral fallback: {advice.summary}</Text>
          ) : (
            <Text>{advice.summary}</Text>
          )}
          {advice.prevention.map((item) => (
            <Text key={item}>• {item}</Text>
          ))}
        </View>
        <Text style={styles.meta}>
          Engine: {result.source} • Model: {result.modelName} • Version: {result.modelVersion}
        </Text>
        <Text style={styles.disclaimer}>
          This app does not replace an agronomist or professional diagnosis.
        </Text>
        <Pressable
          accessibilityRole="button"
          onPress={() => router.push('/(tabs)/history')}
          style={styles.button}
        >
          <Text>View history</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() => router.replace('/(tabs)/index')}
          style={styles.primary}
        >
          <Text style={styles.primaryText}>Scan another leaf</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { alignItems: 'center', padding: 20 },
  card: { width: '100%', maxWidth: 520, gap: 12 },
  title: { fontSize: 28, fontWeight: '700' },
  imageWrap: {
    width: '100%',
    height: 280,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#e2e8f0',
    position: 'relative',
  },
  image: { width: '100%', height: '100%', resizeMode: 'cover' },
  maskOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
    opacity: 0.45,
    tintColor: '#ef4444',
  },
  unsure: { backgroundColor: '#fef3c7', borderRadius: 8, padding: 12, gap: 4 },
  unsureTitle: { fontWeight: '700', color: '#92400e' },
  prediction: { gap: 6 },
  predictionLabel: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  predictionName: { flex: 1, fontWeight: '700' },
  bar: { height: 10, borderRadius: 5, backgroundColor: '#e2e8f0', overflow: 'hidden' },
  barFill: { height: '100%', backgroundColor: '#166534' },
  advice: { backgroundColor: '#f8fafc', borderRadius: 8, padding: 12, gap: 6 },
  adviceTitle: { fontSize: 18, fontWeight: '700' },
  meta: { color: '#475569' },
  disclaimer: { fontWeight: '700', color: '#7f1d1d' },
  button: {
    minHeight: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#64748b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    minHeight: 48,
    borderRadius: 8,
    backgroundColor: '#166534',
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryText: { color: '#fff', fontWeight: '700' },
});
